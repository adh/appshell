from appshell.skins import Skin

class DefaultSkin(Skin):
    base_template = "appshell/base.html"
    local_nav_template = "appshell/local_nav.html"

    def initialize(self, appshell):
        appshell.add_base_template("plain", "appshell/base_plain.html")
