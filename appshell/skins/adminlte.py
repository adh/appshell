from appshell.skins import Skin
from appshell.assets import assets, appshell_components_css
from flask.ext.assets import Bundle
from appshell import current_appshell

adminlte_js = Bundle('appshell/adminlte/dist/js/app.min.js',
                     output="appshell/adminlte.js")
assets.register("appshell_adminlte_js", adminlte_js)
adminlte_css = Bundle('appshell/adminlte/build/less/AdminLTE.less',
                      filters='less', output='appshell/adminlte.css')
assets.register("appshell_adminlte_css", adminlte_css)

adminlte_full_css = Bundle(adminlte_css, appshell_components_css,
                           'appshell/adminlte/appshell-fixups.css',
                           output='appshell/adminlte-full.css')
assets.register("appshell_adminlte_full_css", adminlte_full_css)

class BaseAdminLTESkin(Skin):
    height_decrement = 290

    def __init__(self, colorscheme='blue'):
        self.colorscheme = colorscheme
        self.skin_less_file = "appshell/adminlte/build/less/skins/skin-{}.less"\
            .format(self.colorscheme)
        self.skin_css_class = "skin-{}".format(self.colorscheme)
        
    @property
    def footer_data(self):
        pass

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
        self.body_classes = "fixed"

    def build_sidebar_menus(self):
        res = []

        res.append((current_appshell.menu['primary'].build_real_menu(),
                    ''))
        return res
        
class NavbarAdminLTESkin(BaseAdminLTESkin):
    def initialize(self, appshell):
        super(NavbarAdminLTESkin, self).initialize(appshell)
        self.want_sidebar = False
        self.body_classes = "layout-top-nav layout-boxed"
        
