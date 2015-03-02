from flask import get_template_attribute, current_app
import flask

class TemplateProxy(object):
    def __init__(self,name):
        self.name = name

    def __getattr__(self, name):
        return get_template_attribute(self.name, name)

widgets = TemplateProxy('appshell/widgets.html')
dropdowns = TemplateProxy('appshell/dropdowns.html')
wtf = TemplateProxy('bootstrap/wtf.html')

def render_template(path, 
                    **kwargs):
    return flask.render_template(path, **kwargs)

def single_view(main_content, title=None, template=None):
    if not template:
        template = current_app.extensions['appshell'].base_template
    return render_template(template, 
                           main_content=main_content,
                           page_title=title)

