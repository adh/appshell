
class Skin(object):
    menu_positions = ["left", "right"]
    height_decrement = 150
    
    def get_base_template(self, module):
        t = self.base_template
        if module and module.has_local_nav():
            t = self.local_nav_template

        return t

    def initialize(self, appshell):
        pass
