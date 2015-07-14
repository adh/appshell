from flask.ext.wtf import Form
from flask import render_template
from wtforms.widgets import TextArea
from wtforms.fields import HiddenField, FileField
from appshell.markup import element, button, link_button
from markupsafe import Markup
from flask.ext.babelex import Babel, Domain

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext


class OrderedForm(Form):
    def __iter__(self):
        fields = list(super(OrderedForm, self).__iter__())
        field_order = getattr(self, 'field_order', None)
        if field_order:
            temp_fields = []
            for name in field_order:
                if name == '*':
                    temp_fields.extend([f for f in fields
                                        if f.name not in field_order])
                else:
                    temp_fields.append([f for f in fields
                                        if f.name == name][0])
            fields =temp_fields
        return iter(fields)
        
    field_order = ['*','ok']

class BootstrapMarkdown(TextArea):
    def __init__(self, rows=10):
        self.rows = rows

    def __call__(self, field, **kwargs):
        kwargs['rows'] = self.rows
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s %s' % ("bootstrap-markdown", c)
        return super(BootstrapMarkdown, self).__call__(field, **kwargs)


field_renderers = {}

class FieldRenderer(object):
    __slots__ = ["view", "field", "kwargs", "form_info"]
    def __init__(self, view, field, form_info=None, **kwargs):
        self.view = view
        self.field = field
        self.kwargs = kwargs
        self.form_info = form_info

    def render_input(self):
        args = self.view.get_field_args(self.field)
        args.update(self.kwargs)
        return Markup(self.field(**args))

    def render_errors(self):
        if self.field.errors:
            return Markup("").join((element("p", self.view.error_attrs, i)
                                    for i in self.field.errors))
        else:
            return ""

    def render_description(self):
        if self.field.description:
            return element("p", self.view.description_attrs,
                           self.field.description)
        else:
            return ""

    def render_label(self):
        return self.field.label(**self.view.label_args)
    
    def __html__(self):
        l = self.render_label()

        i = Markup("{}{}{}").format(self.render_input(),
                                    self.render_description(),
                                    self.render_errors())
        
        if self.view.field_div_attrs:
            i = element("div", self.view.field_div_attrs, i)

        return l+i

class FormButton(object):
    __slots__ = ["content"]
    
    def __init__(self, content, **kwargs):
        self.content = content

    def __html__(self):
        return self.render(view=None, form_info=None)
        
class SubmitButton(FormButton):
    __slots__ = ["name", "value", "action", "context_class"]
    
    def __init__(self, text,
                 name=None,
                 value=None,
                 action=None,
                 context_class="primary",
                 **kwargs):
        super(SubmitButton, self).__init__(content=text, **kwargs)
        self.name = name
        self.value = value
        self.action = action
        self.context_class = context_class
        
    def render(self, view, form_info=None):
        attrs = {"type": "submit"}
        
        if self.name is not None:
            attrs["name"] = self.name
        if self.value is not None:
            attrs["value"] = self.value
        if self.action is not None:
            attrs["formaction"] = self.action
            
        return button(self.content,
                      self.context_class,
                      attrs=attrs)

class ButtonGroup(FormButton):
    def get_div_attrs(self):
        return {"class": "btn-group"}
    
    def render(self, view, **kwargs):
        if not self.content:
            return ""
        
        c = Markup("").join((i.render(self) if isinstance(i, FormButton) else i
                             for i in self.content))
        return element("div", self.get_div_attrs(), c)
        
        
class FormView(object):
    def __init__(self,
                 buttons=None,
                 method="POST",
                 **kwargs):
        self.field_renderers = {}
        self.label_args = {}
        self.field_div_attrs = None
        self.form_attrs = {}
        self.button_bar_attrs = {}
        self.method = method
        if buttons is None:
            self.buttons = [SubmitButton(lazy_gettext("OK"))]
        else:
            self.buttons = buttons
        
    def get_field_args(self, field):
        return {}
            
    def render_field(self, field, form_info=None, **kwargs):
        if field.type in field_renderers:
            r = field_renderers[field.type]
        else:
            r = FieldRenderer
        return r(self, field, form_info=form_info, **kwargs)

    def render_fields(self, fields, form_info=None, **kwargs):
        l = []
        for i in fields:
            if isinstance(i, HiddenField):
                continue
            l.append(self.render_field(i,
                                       form_info=form_info,
                                       **kwargs))
            
        return Markup("").join(l)

    def hidden_errors(self, form):
        l = (Markup("").join((Markup('<p class="error">{}</p>').format(j)
                              for j in i.errors))
             for i in form if not isinstance(i, HiddenField))
        return Markup("").join(l)
    
    def render(self, form, form_info=None):
        contents=Markup("{}{}{}{}").format(
            form.hidden_tag(),
            self.hidden_errors(form),
            self.render_fields(form, form_info=form_info),
            self.render_footer(form_info=form_info)
        )
        
        attrs = dict(self.form_attrs)
        if any((isinstance(i, FileField) for i in form)):
            attrs["enctype"] = "multipart/form-data"

        attrs["method"] = self.method
            
        return element("form", attrs, contents)

    def render_footer(self, form_info=None):
        if not self.buttons:
            return ""
        
        c = Markup("").join((i.render(self, form_info=form_info)
                             if isinstance(i, FormButton) else i
                             for i in self.buttons))
        return element("div", self.button_bar_attrs, c)

    def __call__(self, form, form_info=None):
        return RenderProxy(self, form, form_info=form_info)

class RenderProxy(object):
    __slots__ = ["obj", "args", "kwargs"]
    
    def __init__(self, obj, *args, **kwargs):
        self.obj = obj
        self.args = args
        self.kwargs = kwargs
        
    def __html__(self):
        return self.obj.render(*self.args, **self.kwargs)

def field_renderer(t):
    def wrap(cls):
        field_renderers[t] = cls
        return cls

class VerticalFormView(FormView):
    def __init__(self, **kwargs):
        super(VerticalFormView, self).__init__(**kwargs)
        if any((isinstance(i, ButtonGroup) for i in self.buttons)):
            self.button_bar_attrs = {"class": "btn-toolbar"}

    
    def render_field(self, field, **kwargs):
        cls = "form-group"
        if field.errors:
            cls += " has-error"
        if field.flags.required:
            cls += " required"
            
        return element("div", {"class": cls},
                       super(VerticalFormView, self).render_field(field,
                                                                  **kwargs)) 
    def get_field_args(self, field):
        return {"class": "form-control"}

    
class HorizontalFormView(VerticalFormView):
    def __init__(self, widths=[3, 9], size="md", **kwargs):
        super(HorizontalFormView, self).__init__(**kwargs)
        self.label_args= {"class": "col-{}-{}".format(size, widths[0])}
        self.field_div_attrs = {"class": "col-{}-{}".format(size, widths[1])}
        self.form_attrs = {"class": "form-horizontal"}
