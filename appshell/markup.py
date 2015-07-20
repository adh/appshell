from markupsafe import Markup

def xmlattrs(attrs):
    res = Markup(" ").join(
        Markup('{0}="{1}"').format(k, v) 
        for k, v in attrs.iteritems()
        if v != None
    )
    if res != '':
        return " " + res
    else:
        return ""

def xmltag(name, attrs):
    return Markup("<{0}{1}>").format(name, xmlattrs(attrs))

def element(name, attrs, contents):
    return Markup("{0}{1}</{2}>").format(xmltag(name, attrs),
                                         contents,
                                         name)

def button(text, classes, context_class="default", size=None, attrs={}):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    a = {"class": cls + " " + classes, 
         "type": "button"}
    a.update(attrs)
    return element("button", 
                   a,
                   text)

def link_button(url, text, context_class="default", size=None, hint=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("a", 
                   {"class": cls, "role": "button", "href": url, "title": hint},
                   text)
    

def glyphicon(icon):
    return Markup('<span class="glyphicon glyphicon-{0}"></span>')\
        .format(icon)

def image_enlarge(img, content):
    return ""

class GridColumn(object):
    __slots__ = ["widths"]
    def __init__(self, width=3, **widths):
        if not widths:
            widths = {"md": width}
            
        self.widths = widths

    def get_class(self):
        return " ".join(["col-{}-{}".format(k, v)
                         for k, v in self.widths.iteritems()])
        
    def render(self, content):
        return element("div", {"class": self.get_class()}, content)
