from flask import render_template, jsonify, request
from markupsafe import Markup
from appshell.markup import element, link_button, button, xmltag
from appshell.urls import res_url, url_or_url_for, url_for
from appshell.templates import widgets, dropdowns, modals
from appshell.locals import current_appshell

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

