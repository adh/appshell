from flask import get_template_attribute
import flask

class TemplateProxy(object):
    def __init__(self,name):
        self.name = name

    def __getattr__(self, name):
        return get_template_attribute(self.name, name)

def render_template(path, 
                    **kwargs):
    return flask.render_template(path, **kwargs)
