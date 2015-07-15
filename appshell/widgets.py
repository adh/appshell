from flask import render_template, jsonify, request
from markupsafe import Markup
from appshell.markup import element, link_button, button, xmltag
from appshell.urls import res_url, url_or_url_for, url_for
from appshell.templates import widgets, dropdowns, modals
from appshell.locals import current_appshell
from hashlib import sha256

class Tab(object):
    __slots__ = ['text', 'target']
    def __init__(self, text, target):
        self.text = text
        self.target = target

    def __html__(self):
        params = request.view_args
        if not current_appshell.endpoint_accessible(self.target, params):
            return ''
        attrs = {"role": "presentation"}

        if request.endpoint == self.target:
            attrs["class"] = "active"

        url = url_for(self.target, **params)
        link = element('a', {'href': url}, self.text)
        return element('li', attrs, link)

class ServerSideTabbar(object):
    def __init__(self, tabs, style='tabs'):
        self.tabs = tabs
        self.style = style
    def __html__(self):
        return element('ul', {"class": "appshell-tabs nav nav-"+self.style},
                       Markup(u"").join(self.tabs))

class ClientTab(object):
    __slots__ = ["title", "name", "content"]
    def __init__(self, title, content, name=None):
        self.title = title
        self.content = content
        if name is None:
            self.name = "tab-" + sha256(title).hexdigest()
        else:
            self.name = name

    def is_active(self):
        return None
            
    def html_tab(self, first=False):
        attrs = {"role": "presentation"}

        if (first and self.is_active() is None) or self.is_active():
            attrs["class"] = "active"

        link = element('a',
                       {'href': "#" + self.name,
                        "aria-controls": self.name,
                        "role": "tab",
                        "data-toggle": "tab"},
                       self.title)
    
        return element('li', attrs, link)

    def html_content(self, first=False):
        cls = "tab-pane"
        if (first and self.is_active() is None) or self.is_active():
            cls += " active"

        return element("div",
                       {"class": cls,
                        "id": self.name,
                        "role": "tabpanel"},
                       self.content)

            
class ClientSideTabbar(object):
    def __init__(self, content_class=None):
        self.tabs = []
        self.content_class = content_class
        
    def add_tab(self, title, content, name=None):
        self.tabs.append(ClientTab(title, content, name=name))

    def __html__(self):
        tcl = []
        tbl = []
        first = True
        for i in self.tabs:
            tbl.append(i.html_tab(first=first))
            tcl.append(i.html_content(first=first))
            first=False

        tcclass = ""
        if self.content_class:
            tcclass = " " + self.content_class
            
        tb = Markup('<ul class="nav nav-tabs" role="tablist">{}</ul>')\
            .format(Markup("").join(tbl))
        tc = Markup('<div class="tab-content{}">{}</div>')\
            .format(tcclass,
                    Markup("").join(tcl))
            
        return Markup('<div>{}{}</div>').format(tb, tc)
