from flask import render_template
from appshell.templates import TemplateProxy
from markupsafe import Markup, escape
from itertools import chain
from appshell import current_appshell

t = TemplateProxy('appshell/leaflet_elements.html')

def merge_bounds(*lists):
    coords = list(chain(*lists))
    if not coords:
        return []
    return [[min((i[0] for i in coords)),
             min((i[1] for i in coords))],
            [max((i[0] for i in coords)),
             max((i[1] for i in coords))]]

class MapElement(object):
    def __init__(self, popup=None, **kwargs):
        if popup is not None:
            self.popup = escape(popup)
        else:
            self.popup = None

    def get_bounds(self):
        return []
    def get_js(self, target='map'):
        return self.get_element_js(target=target) + self.get_popup_js()
    def get_popup_js(self):
        if self.popup is None:
            return ""
        else:
            return t.popup(self.popup)

class Marker(MapElement):
    def __init__(self, pos, options={}, **kwargs):
        super(Marker, self).__init__(pos=pos, **kwargs);
        self.pos = pos
        self.options = options
    def get_element_js(self, target='map'):
        return t.marker(self.pos, self.options, target=target)
    def get_bounds(self):
        return [self.pos]

class MarkerCluster(MapElement):
    def __init__(self, **kwargs):
        self.elements = []
        self.fit_to = []
    def add(self, el, fit=False):
        self.elements.append(el)
        if fit:
            self.fit_to = merge_bounds(self.fit_to, el.get_bounds())
    def get_bounds(self):
        return self.fit_to
    def get_js(self, target='map'):
        return t.marker_cluster(c=self, target=target)

class Polyline(MapElement):
    __leaflet_class__ = "polyline"
    def __init__(self, points=[], options={}, **kwargs):
        super(Polyline, self).__init__(**kwargs);
        self.points = points
        self.options = options

    def add(self, point):
        self.points.append(point)

    def get_bounds(self):
        return merge_bounds(self.points)

    def get_element_js(self, target='map'):
        return t.polyline(points=self.points, 
                          opts=self.options,
                          target=target,
                          klass=self.__leaflet_class__)
class Polygon(Polyline):
    __leaflet_class__ = "polygon"

class Rectangle(Polygon):
    __leaflet_class__ = "rectangle"

class Circle(MapElement):
    def __init__(self, pos, radius, options={}, **kwargs):
        super(Circle, self).__init__(**kwargs);
        self.pos = pos
        self.options = options
        self.radius = radius

    def get_bounds(self):
        return [self.pos]

    def get_element_js(self, target='map'):
        return t.circle(self.pos, self.radius, self.options, target=target)
        

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
            self.fit_to = merge_bounds(self.fit_to, el.get_bounds())
            
    def render(self):
        return render_template('appshell/leaflet.html', map=self)
