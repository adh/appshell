from flask import get_template_attribute, current_app, make_response
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

def single_view(main_content, title=None, template=None, layout=None):
    if not template:
        template = current_app.extensions['appshell'].base_template
    return render_template(template, 
                           main_content=main_content,
                           page_title=title,
                           page_layout=layout)

def message(message, severity='primary', title=None, status=None):
    s = render_template('appshell/message.html', 
                        message=message,
                        page_title=title,
                        severity=severity)
    if status is not None:
        return make_response(s, status)
    else:
        return s
    
