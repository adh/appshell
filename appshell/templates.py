from flask import get_template_attribute, current_app, make_response
import flask
from markupsafe import Markup

class TemplateProxy(object):
    def __init__(self,name):
        self.name = name

    def __getattr__(self, name):
        return get_template_attribute(self.name, name)

widgets = TemplateProxy('appshell/widgets.html')
dropdowns = TemplateProxy('appshell/dropdowns.html')
modals = TemplateProxy('appshell/modals.html')
wtf = TemplateProxy('bootstrap/wtf.html')

def render_template(path, 
                    **kwargs):
    return flask.render_template(path, **kwargs)

def single_view(main_content, title='', template=None, layout=None,
                heading=False, description=''):
    if not template:
        template = current_app.extensions['appshell'].base_template

    if heading and title:
        main_content = Markup(u"<h1>{0}</h1>{1}").format(title, Markup(main_content))
        
    return render_template(template, 
                           main_content=main_content,
                           page_title=title,
                           page_description=description,
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
    
def confirmation(message, severity='primary', title=None):
    s = render_template('appshell/confirmation.html', 
                        message=message,
                        page_title=title,
                        severity=severity)
    return s
    
