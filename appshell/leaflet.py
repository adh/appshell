from flask import render_template
from appshell.templates import TemplateProxy

t = TemplateProxy('appshell/leaflet_elements.html')

class MapElement(object):
    def __init__(self, popup=None, **kwargs):
        self.popup = popup
    def get_bounds(self):
        return []
    def get_js(self):
        return self.get_element_js() + self.get_popup_js()
    def get_popup_js(self):
        if not self.popup:
            return ""
        else:
            return t.popup(self.popup)

class Marker(MapElement):
    def __init__(self, pos, options={}, **kwargs):
        super(Marker, self).__init__(pos=pos, **kwargs);
        self.pos = pos
        self.options = options
    def get_element_js(self):
        return t.marker(self.pos, self.options)
    def get_bounds(self):
        return [self.pos]

class Map(object):
    def __init__(self, x=0, y=0, z=0, tilelayer=None, tile_options={}):
        self.x = x
        self.y = y
        self.z = z
        if tilelayer is None:
            self.tilelayer = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            self.tile_options = {
                "attribution": 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
                "maxZoom": 18
            }
        else:
            self.tilelayer = tilelayer
            self.tileoptions = tile_options

        self.elements = []
        self.fit_to = []

    def add(self, el, fit=False):
        self.elements.append(el)
        if fit:
            self.fit_to += el.get_bounds()
            print self.fit_to
            
    def render(self):
        return render_template('appshell/leaflet.html', map=self)
