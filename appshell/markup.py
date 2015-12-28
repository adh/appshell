from markupsafe import Markup
from appshell.urls import url_or_url_for

def xmlattrs(attrs):
    res = Markup(" ").join(
        Markup('{0}="{1}"').format(k, v) 
        for k, v in attrs.items()
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

def button(text, classes="", context_class="default", size=None, attrs={}):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    a = {"class": cls + " " + classes, 
         "type": "button"}
    a.update(attrs)
    return element("button", 
                   a,
                   text)

def link_button(url, text, context_class="default", size=None, hint=None, link_target=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("a", 
                   {"class": cls, "role": "button", "href": url, "title": hint, "target": link_target},
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
                         for k, v in self.widths.items()])
        
    def render(self, content):
        return element("div", {"class": self.get_class()}, content)

class ToolbarButton(object):
    __slots__ = ["text", "endpoint", "context_class", "hint", "args",
                 "pass_args"]
    def __init__(self, text, endpoint, context_class="default", hint='',
                 args={}, pass_args=[]):
        self.text = text
        self.endpoint = endpoint
        self.context_class = context_class
        self.hint = hint
        self.args = args
        self.pass_args = pass_args 

    def render(self, toolbar, size, args={}):
        a = dict(self.args)
        for i in self.pass_args:
            a[i] = args[i]
            
        return link_button(url_or_url_for(self.endpoint,
                                          **a),
                           self.text,
                           self.context_class,
                           size,
                           self.hint)

class ToolbarSplitter(object):
    def render(self, toolbar, size, args={}):
        return Markup('</div><div class="btn-group" role="group">')
    
class Toolbar(object):
    def __init__(self, grouped=True, size=None):
        self.buttons = []
        self.grouped = grouped
        self.size = size

    def add_button(self, text, endpoint,
                   context_class="default", hint='', args={}):
        self.buttons.append(ToolbarButton(text, endpoint, context_class,
                                          hint=hint, args=args))

    def add_splitter(self):
        self.buttons.append(ToolbarSplitter())
        self.grouped = True

    def render(self, size, in_group=False, **kwargs):
        res = Markup("").join((i.render(self, size, **kwargs)
                               for i in self.buttons))

        if not in_group:
            if self.grouped:
                res = element("div", {"class": "btn-group"}, res)
                res = element("div", {"class": "btn-toolbar"}, res)
            else:
                res = element("div", {}, res)
            
        return res
        
    def __html__(self):
        return self.render(self.size)
        
    def prepend(self, content):
        return Markup("{}{}").format(self, content)
