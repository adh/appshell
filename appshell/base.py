from flask import Flask, Blueprint, Markup, request, current_app
import flask
import flask.views
from flask.ext.bootstrap import Bootstrap
from flask.ext.babelex import Babel, Domain
from flask.ext.wtf import CsrfProtect
from appshell.menu import MenuEntry, MainMenu
from appshell.urls import url_for, url_or_url_for, res_url, url_or_res_url
from appshell.templates import render_template, single_view
from appshell.utils import push_block, get_pushed_blocks
from appshell.locals import current_appshell
import importlib
from werkzeug.local import LocalProxy


mydomain = Domain('appshell')

def endpoint_accessible(target, values):
    return current_appshell.endpoint_accessible(target, values)

template_globals = {"url_for": url_for, 
                    "url_or_url_for": url_or_url_for,
                    "url_or_res_url": url_or_res_url,
                    "res_url": res_url,
                    "push_block": push_block,
                    "get_pushed_blocks": get_pushed_blocks,
                    "endpoint_accessible": endpoint_accessible}

def parse_menu_path(path):
    menu, discard, item = path.partition('/')
    if item == '':
        return menu, None, None
    group, discard, item = item.rpartition(':')
    return menu, group, item


class TopLevelMenu(object):
    def __init__(self, *args, **kwargs):
        super(TopLevelMenu, self).__init__(*args, **kwargs)
        self.menu_entry_class = MenuEntry

    def add_menu_entry(self, path, entry, postion='left'):
        raise NotImplementedError

    def add_menu_label(self, path, text, position='left'):
        raise NotImplementedError
  
    def add_menu(self, entries, position='left'):
        for i in entries:
            self.add_menu_entry_from_desc(*i, position=position)
      

class AppShell(TopLevelMenu):
    def __init__(self, app_name, root_view, app=None, components=[]):
        TopLevelMenu.__init__(self)
        self.app_name = app_name

        self.menu = {"left": MainMenu(),
                     "right": MainMenu()}
        self.system_module = None
        self.babel = mydomain
        self.root_view = root_view
        self.component_config = components
        self.search_view = None
        self.base_templates = {"plain": "appshell/base_plain.html"}
        self.access_map = {}

        if app:
            self.init_app(app)
        
    def use_component(self, app, module, cfg):
        mod = importlib.import_module("."+module, 'appshell')
        d = mod.register_in_app(self, app, **cfg)
        setattr(self, module, d)
        return d

    def add_base_template(self, name, filename):
        self.base_templates[name] = filename

    @property
    def base_template(self):
        t = "appshell/base.html"
        if self.current_module and self.current_module.has_local_nav():
            t = "appshell/local_nav.html"

        if "__view" in request.args:
            vn = request.args["__view"]
            if vn in self.base_templates:
                t = self.base_templates[vn]
        return t

    @property
    def current_module(self):
        return current_app.blueprints[request.blueprint]

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['appshell'] = self
        bp = Blueprint('appshell', __name__, 
                       template_folder='templates',
                       static_folder='static',
                       static_url_path=app.static_url_path + '/appshell')
        app.register_blueprint(bp)

        @app.context_processor
        def context_processor():
            return {"appshell": self}

        @app.before_request
        def check_access():
            if not self.endpoint_accessible(request.endpoint, request.args):
                return self.handle_forbidden_endpoint()


        for n, f in template_globals.items():
            app.add_template_global(f, name=n)

        Bootstrap(app)
        app.config['BOOTSTRAP_SERVE_LOCAL'] = True

        Babel(app)

        for k, v in self.component_config.items():
            self.use_component(app, k, v)

    
    def root_view_url(self):
        return url_or_url_for(self.root_view)

    def add_menu_entry_from_desc(self, path, text=None, entry=None, 
                                 position=None, klass=None):
        menu, group, item = parse_menu_path(path)
        
        if not position:
            if item:
                position = 'left'
            else:
                position = 'right'

        if not entry:
            target = item or menu

            if '/' in target:
                if not klass:
                    klass = MenuEntry
                entry = klass(text, url=url)
            else:
                if not klass:
                    klass = self.menu_entry_class

                entry = klass(text, target=target)

        self.add_menu_entry(menu, group, item, entry, position=position)

    def add_menu_entry(self, menu, group, item, entry, position='left'):
        if not item:
            self.menu[position].add_top_entry(menu, entry)
        else:
            self.menu[position].add_entry(menu, item, entry, group=group)

    def add_menu_label(self, path, text, position='left'):
        menu, discard, group = path.partition('/')
        m = self.menu[position]
        if group:
            m.ensure_group(menu, group, text)
        else:
            m.ensure_menu(menu, text)

    def build_menu(self):
        return {k: v.build_real_menu() for k,v in self.menu.items()}
        
    def add_access_rule(self, endpoint, proc):
        if endpoint not in self.access_map:
            self.access_map[endpoint] = []

        self.access_map[endpoint].append(proc)

    def endpoint_accessible(self, endpoint, values):
        if endpoint not in self.access_map:
            return True
        rules = self.access_map[endpoint]
        for i in rules:
            if not i(**values):
                return False
        return True

    def handle_forbidden_endpoint(self):
        if self.system_module:
            return self.system_module.handle_forbidden_endpoint()
        return flask.abort(403)


class Module(TopLevelMenu, Blueprint):
    def __init__(self, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        self.default_menu = self.name
        self.default_group = ''
        self.default_position = 'left'
        self.menuentries = []
        self.menulabels = []
        self.base_templates = {}
        self.local_nav = {}
        self.title_text = None
        self.access_rules = []

    def has_local_nav(self):
        return len(self.local_nav) > 0

    @property
    def local_nav_menu(self):
        ln = self.local_nav
        return [ [ln[k][j] for j in sorted(ln[k].keys())]
                 for k in sorted(self.local_nav.keys())]
    
    def entrypoint_for_view(self, view):
        return self.name + '.' + view.__name__

    def menu_entry_for_view(self, view, text, values={}):
        return self.menu_entry_class(text,
                                     target=self.entrypoint_for_view(view),
                                     values=values)

    def menu(self,  text, path=None, values={}, position=None):
        if not position:
            position = self.default_position

        def wrap(view):
            name = self.name + '.' + view.__name__

            if not path:
                menu = self.default_menu
                group = self.default_group
            else:
                menu, discard, group = path.partition('/')
                
            if not menu:
                menu = name
                item = None
            else:
                item = name

            entry = self.menu_entry_for_view(view, text, values=values)

            self.add_menu_entry(menu, group, item, entry, position=position)
            return view
        return wrap

    def local_menu(self, text, group=None, sort_key=None):
        def wrap(view):
            name = self.name + '.' + view.__name__
            self.add_local_menu_entry(name, text, group, sort_key)
            return view
        return wrap

    def label(self, text):
        self.title_text = text
        self.add_menu_label(self.default_menu + '/' + self.default_group, 
                            text, position=self.default_position)

    def add_menu_entry(self, menu, group, item, entry, position='left'):
        if not position:
            position = self.default_position
        self.menuentries.append((menu, group, item, entry, position))

    def add_menu_label(self, path, text, position=None):
        if not position:
            position = self.default_position
        self.menulabels.append((path, text, position))

    def add_local_menu_entry(self, endpoint, text, group=None, sort_key=None):
        if sort_key == None:
            sort_key = text
        
        if group not in self.local_nav:
            self.local_nav[group] = {}

        self.local_nav[group][sort_key] = (endpoint, text)
        
    def add_base_template(self, name, filename):
        self.base_templates[name] = filename

    def register(self, app, *args, **kwargs):
        super(Module, self).register(app, *args, **kwargs)
        
        if not hasattr(app, 'extensions'):
            return
        if not 'appshell' in app.extensions:
            return

        ash = app.extensions['appshell']
        for i in self.menuentries:
            ash.add_menu_entry(*i)
        for i in self.menulabels:
            ash.add_menu_label(*i)
        for k, v in self.base_templates.items():
            ash.add_base_template(k, v)
        for endpoint, proc in self.access_rules:
            ash.add_access_rule(self.name + "." + endpoint, proc)

    def add_access_rule(self, endpoint, proc):
        self.access_rules.append((endpoint, proc))

    def access(self, proc):
        def wrap(f):
            self.add_access_rule(f.__name__, proc)
            return f
        return wrap

class SystemModule(Module):
    def register(self, app, *args, **kwargs):
        if not hasattr(app, 'extensions'):
            return
        if not 'appshell' in app.extensions:
            return

        ash = app.extensions['appshell']
        if ash.system_module != None:
            raise ValueError("Multiple system modules in one application")
        ash.system_module = self

        super(Module, self).register(app, *args, **kwargs)
        
    def get_system_menu(self):
        return None

    def handle_forbidden_endpoint(self):
        return flask.abort(403)



class View(flask.views.View):
    def __init__(self):
        self.page_args = {}
    
    @classmethod
    def route(cls, blueprint, route,
              name=None,
              decorators=[],
              **kwargs):
        if name is None:
            name = cls.__name__

        view = cls.as_view(name, **kwargs)

        for i in decorators:
            view = i(view)
        
        blueprint.add_url_rule(route, view_func=view)

    def render_template(self, form):
        return single_view(form, **self.page_args)
