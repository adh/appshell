from flask.ext.login import LoginManager, current_user
from flask.ext.login import login_user, logout_user, login_fresh, \
    login_required, fresh_login_required, current_user, login_url
from flask.ext.babelex import Babel, Domain
from flask import Blueprint, request, flash, redirect
from appshell import SystemModule, current_appshell, url_for
from appshell.menu import MenuItem, DropdownMenu
from appshell.templates import wtf, single_view
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from appshell.utils import view_visible

from functools import wraps

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext

class AuthenticationModule(SystemModule):
    def __init__(self, *args, **kwargs):
        super(AuthenticationModule, self).__init__(*args, **kwargs)
        self.login_manager = LoginManager()
        self.login_manager.login_message_category = "warning"
        self.login_manager.user_loader(self.load_user)
        self.logged_in_menu = DropdownMenu()
        self.login_text = mydomain.lazy_gettext('Login...')
        self.logged_in_user_text = mydomain.lazy_gettext('User: ')

    def load_user(self, user_id):
        raise NotImplementedError

    def login(self, view):
        self.login_manager.login_view = self.name + '.' + view.__name__
        return view

    def register(self, app, *args, **kwargs):
        super(AuthenticationModule, self).register(app, *args, **kwargs)
        self.login_manager.init_app(app)

    def login_url(self):
        return login_url(self.login_manager.login_view,
                         request.url)

    def logged_in_text(self):
        return self.logged_in_user_text + ' ' + self.get_current_user_name()

    def get_current_user_name(self):
        return current_user.get_name()

    def user_menu(self, text, group='', values={}):
        def wrap(view):
            name = self.name + '.' + view.__name__
            entry = self.menu_entry_for_view(view, text, values=values)
            self.logged_in_menu.add_entry(name, entry, group)
            return view
        return wrap
        

    def get_system_menu_item(self):
        if current_user.is_anonymous():
            return MenuItem(text=self.login_text,
                            url=self.login_url())
        else:
            return MenuItem(text=self.logged_in_text(),
                            items=self.logged_in_menu.build_real_menu())

class PasswordLoginForm(Form):
    username = StringField(lazy_gettext('Username:'))
    password = PasswordField(lazy_gettext('Password:'))
    ok = SubmitField(lazy_gettext("OK"))

class PasswordAuthenticationModule(AuthenticationModule):
    def __init__(self, *args, **kwargs):
        super(PasswordAuthenticationModule, self).__init__(*args, **kwargs)
        self.userclass = None
        #self.authenticate_user = None

        @self.route('/login', methods=('GET', 'POST'))
        @self.login
        def login():
            f = PasswordLoginForm()
            if f.validate_on_submit():
                user = self.authenticate_user(f.username.data, f.password.data)
                if not user:
                    flash(_("Invalid username or password"), "danger")
                else:
                    login_user(user)
                    flash(_("Login successful"), "success")
                    return redirect(request.args.get("next") or 
                                    url_for(current_appshell.root_view))

            return single_view(wtf.quick_form(f, 
                                              form_type="horizontal",
                                              horizontal_columns=('lg', 2, 3)),
                               title=_('Login'))

        @self.route('/logout')
        @self.user_menu(lazy_gettext('Logout'))
        def logout():
            logout_user()
            flash(_("You have logged out"), "info")
            return redirect(url_for(current_appshell.root_view))

    def load_user(self, user_id):
        return self.userclass.load_user(user_id)

    def authenticate_user(self, username, password):
        return self.userclass.authenticate(username, password)

all_permissions = {}
    
class Permission(object):
    def __init__(self, name, text=None, fresh=False, *args, **kwargs):
        self.name = name
        if text is None:
            text = name
        self.text = text
        self.login_required = login_required if not fresh \
                              else fresh_login_required

    def permitted(self, user=None):
        if user is None:
            user = current_user
        if user.is_anonymous():
            return False
        return user.has_permission(self)
        
    @property
    def require(self):
        def wrap(view):
            view_visible(view)
            def visibility_proc(**kwargs):
                return self.permitted()

            @wraps(view)
            def wrapper(**kwargs):
                if not self.permitted():
                    return "403"
                return view(*args, **kwargs)
            return self.login_required(wrapper)
        return wrap

class ModulePermissions(object):
    def __init__(self, name_prefix, permissions=[]):
        for i in permissions:
            n = i.name
            i.name = name_prefix+n
            setattr(self, n, i)
