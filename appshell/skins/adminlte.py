from appshell.skins import Skin
from appshell.assets import assets, appshell_components_css
from flask_assets import Bundle
from appshell import current_appshell
from subprocess import check_output
from markupsafe import Markup

adminlte_js = Bundle('appshell/adminlte/plugins/jquery.slimscroll.min.js',
                     'appshell/adminlte/dist/js/app.min.js',
                     output="appshell/adminlte.js")
assets.register("appshell_adminlte_js", adminlte_js)
adminlte_css = Bundle('appshell/adminlte/build/less/AdminLTE.less',
                      filters='less', output='appshell/adminlte.css')
assets.register("appshell_adminlte_css", adminlte_css)

adminlte_full_css = Bundle(adminlte_css, appshell_components_css,
                           'appshell/adminlte/appshell-fixups.css',
                           output='appshell/adminlte-full.css')
assets.register("appshell_adminlte_full_css", adminlte_full_css)

def get_version():
    return check_output("git describe --always --tags",
                        shell=True).decode("utf-8")

class BaseAdminLTESkin(Skin):
    height_decrement = 290
    footer_right = None
    footer_left = Markup("&nbsp;")
    
    def __init__(self, colorscheme='blue',
                 skin_filename=None,
                 skin_class=None,
                 footer=True,
                 footer_right=None,
                 footer_left=None,
                 favicon=None,
                 get_version=get_version,
                 top_nav_add=[]):

        self.top_nav_add = top_nav_add
        self.favicon = favicon
        
        if skin_filename is not None:
            self.skin_less_file = skin_filename
            self.skin_css_class = skin_class
        else:
            self.colorscheme = colorscheme
            self.skin_less_file = "appshell/adminlte/build/less/skins/skin-{}.less"\
                .format(self.colorscheme)
            self.skin_css_class = "skin-{}".format(self.colorscheme)

        self.want_footer = footer
        if not footer:
            self.height_decrement -= 45
        else:
            if footer_right is None:
                self.footer_right = "v. " + get_version()
            else:
                self.footer_right = footer_right

            if footer_left is not None:
                self.footer_left = footer_left
        
    @property
    def footer_data(self):
        pass

    def get_extra_head(self):
        if self.favicon:
            return (Markup('<link rel="shortcut icon" href="{}" />')
                    .format(self.favicon))
        return ''
    
    def get_base_template(self, module):
        return "appshell/adminlte/base.html"

    def get_small_logo(self):
        return current_appshell.app_name
    def get_large_logo(self):
        return current_appshell.app_name
    
class AdminLTESkin(BaseAdminLTESkin):
    def initialize(self, appshell):
        super(AdminLTESkin, self).initialize(appshell)
        appshell.default_menu_position = 'primary'
        self.menu_positions = ['left', 'right', 'primary']
        self.want_sidebar = True

    def body_classes(self, page_layout=None):
        return "fixed"
        
    def build_sidebar_menus(self):
        res = []

        res.append((current_appshell.menu['primary'].build_real_menu(),
                    ''))
        return res
        
class NavbarAdminLTESkin(BaseAdminLTESkin):
    height_decrement = 300
    def initialize(self, appshell, boxed=True):
        super(NavbarAdminLTESkin, self).initialize(appshell)
        self.want_sidebar = False
        self.boxed = boxed
        
    def body_classes(self, page_layout=None):
        if page_layout == 'fluid':
            return "layout-top-nav"
        
        if self.boxed:
            return "layout-top-nav layout-boxed"
        else:
            return "layout-top-nav"
