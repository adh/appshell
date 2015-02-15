from flask import Flask, Blueprint, url_for, Markup, request
from flask.ext.bootstrap import Bootstrap
from flask.ext.babelex import Babel, Domain
from flask.ext.wtf import CsrfProtect
from menu import MenuEntry, MainMenu
import importlib

mydomain = Domain('appshell')

def url_or_url_for(path):
    if '/' in path:
        return path
    else:
        return url_for(path)

def parse_menu_path(path):
    menu, discard, item = path.partition('/')
    if item == '':
        return menu, None, None
    group, discard, item = item.rpartition(':')
    return menu, group, item

class TopLevelMenu(object):
    def __init__(self):
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
        self.babel = mydomain
        self.root_view = root_view
        self.components = components
        self.search_view = None

        if app:
            self.init_app(app)
        
    def use_component(self, app, module):
        mod = importlib.import_module(module, 'appshell')
        return mod.register_in_app(app)

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

        Bootstrap(app)
        app.config['BOOTSTRAP_SERVE_LOCAL'] = True

        Babel(app)

        for k in self.components:
            self.use_component(app, k)

    
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
        return {k: v.build_real_menu() for k,v in self.menu.iteritems()}
        

class Module(Blueprint, TopLevelMenu):
    def __init__(self, *args, **kwargs):
        Blueprint.__init__(self, *args, **kwargs)
        TopLevelMenu.__init__(self)
        self.default_menu = self.name
        self.default_group = ''
        self.default_position = 'left'
        self.menuentries = []
        self.menulabels = []

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

    def label(self, text):
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

        

    def register(self, app, *args, **kwargs):
        Blueprint.register(self, app, *args, **kwargs)
        
        if not hasattr(app, 'extensions'):
            return
        if not 'appshell' in app.extensions:
            return

        ash = app.extensions['appshell']
        for i in self.menuentries:
            ash.add_menu_entry(*i)
        for i in self.menulabels:
            ash.add_menu_label(*i)