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

class MapExtension(object):
    pass

class MapElement(object):
    def __init__(self, popup=None, **kwargs):
        if popup is not None:
            self.popup = escape(popup)
        else:
            self.popup = None

    def get_bounds(self):
        return []
    
    def get_js(self):
        return t.element((self.get_element_js(), self.get_popup_js()))

    def get_popup_js(self):
        if self.popup is None:
            return ""
        else:
            return t.popup(self.popup)

class Icon(object):
    __leaflet_class__ = "L.icon"
    def __init__(self, options):
        self.options = options
    def __html__(self):
        return t.icon(klass=self.__leaflet_class__,
                      options=self.options)

class AwesomeMarker(Icon):
    __leaflet_class__ = "L.AwesomeMarkers.icon"
class DivIcon(Icon):
    __leaflet_class__ = "L.divIcon"
class BeautifyMarker(Icon):
    __leaflet_class__ = "L.BeautifyIcon.icon"
    
class LayerGroup(MapElement):
    __leaflet_class__ = "LayerGroup"
    def __init__(self, options={}, **kwargs):
        self.elements = []
        self.fit_to = []
        self.options = options
    def add(self, el, fit=False):
        self.elements.append(el)
        if fit:
            self.fit_to = merge_bounds(self.fit_to, el.get_bounds())
    def get_bounds(self):
        return self.fit_to
    def get_js(self):
        return t.group(c=self,
                       options=self.options,
                       klass=self.__leaflet_class__)

class FeatureGroup(LayerGroup):
    __leaflet_class__ = "FeatureGroup"
        
class Marker(MapElement):
    def __init__(self, pos, options={}, icon=None, divicon=None,
                 name=None, **kwargs):
        super(Marker, self).__init__(pos=pos, **kwargs);
        self.pos = pos
        self.options = options
        self.name = name

        self.icon = icon
        if divicon:
            self.icon = DivIcon(divicon)
    def get_element_js(self):
        return t.marker(self, self.pos, self.options)
    def get_bounds(self):
        return [self.pos]

class MarkerCluster(FeatureGroup):
    __leaflet_class__ = "MarkerClusterGroup"

class PathElement(MapElement):
    def __init__(self, points=[], options={}, **kwargs):
        super(PathElement, self).__init__(**kwargs);
        self.points = points
        self.options = options

    def add(self, point):
        self.points.append(point)

    def get_bounds(self):
        return merge_bounds(self.points)

    def get_element_js(self):
        return t.pathelement(points=self.points, 
                             opts=self.options,
                             klass=self.__leaflet_class__)
    
class Polyline(PathElement):
    __leaflet_class__ = "polyline"

class Polygon(PathElement):
    __leaflet_class__ = "polygon"

class Rectangle(PathElement):
    __leaflet_class__ = "rectangle"

class HeatLayer(PathElement):
    __leaflet_class__ = "heatLayer"
    
class Circle(MapElement):
    def __init__(self, pos, radius, options={}, name=None, **kwargs):
        super(Circle, self).__init__(name=name, **kwargs);
        self.pos = pos
        self.options = options
        self.radius = radius
        self.name = name

    def get_bounds(self):
        return [self.pos]

    def get_element_js(self):
        return t.circle(self.pos, self.radius, self.options, name=self.name)

class MapControl(MapElement):
    pass
    
class LayerControl(MapControl):
    def __init__(self, options=None):
        self.overlays = []
        self.fit_to = []
        self.bases = []
        if options is not None:
            self.options = options
        else:
            self.options = {}
            
        
    def get_js(self):
        return t.layer_control(self)

    def add_overlay(self, l, name, visible=False, fit=False):
        self.overlays.append((l, name, visible))
        if fit:
            self.fit_to = merge_bounds(self.fit_to, l.get_bounds())

    def add_base(self, l, name, visible=False, fit=False):
        self.bases.append((l, name, visible))
        if fit:
            self.fit_to = merge_bounds(self.fit_to, l.get_bounds())
        
        
    def get_bounds(self):
        return self.fit_to
        
    
class Map(object):
    def __init__(self, x=0, y=0, z=0, tilelayer=None, tile_options={}, after=None):
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
        self.extensions = []
        self.fit_to = []
        if after:
            self.after = [after]
        else:
            self.after = []

    def add_after(self, html):
        self.after.append(html)
            
    def add(self, el, fit=False):
        self.elements.append(el)
        if fit:
            self.fit_to = merge_bounds(self.fit_to, el.get_bounds())

    def add_extension(self, ex):
        self.extensions.append(ex)
            
    def render(self, **kwargs):
        return render_template('appshell/leaflet.html', map=self, **kwargs)

class DrawingSelector(MapElement):
    def __init__(self,
                 allow_point=False,
                 allow_rectangle=True,
                 allow_polygon=True,
                 handler_modal='#selector_modal',
                 handler_field='#selector_shape'):
        self.handler_modal = handler_modal
        self.handler_field = handler_field
        self.allow_point = allow_point
        self.allow_polygon = allow_polygon
        self.allow_rectangle = allow_rectangle
    
    def get_js(self):
        return t.drawing_selector(self)
        
