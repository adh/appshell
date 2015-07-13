from flask.ext.wtf import Form
from flask import render_template
from wtforms.widgets import TextArea
from wtforms.fields import HiddenField, FileField
from appshell.markup import element
from markupsafe import Markup

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
    __slots__ = ["view", "field", "kwargs"]
    def __init__(self, view, field, **kwargs):
        self.view = view
        self.field = field
        self.kwargs = kwargs

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
    
class FormView(object):
    def __init__(self,
                 form=None,
                 **kwargs):
        self.form = form
        self.field_renderers = {}
        self.label_args = {}
        self.field_div_attrs = None
        self.form_attrs = {}
        
    def get_field_args(self, field):
        return {}
            
    def render_field(self, field, **kwargs):
        if field.type in field_renderers:
            r = field_renderers[field.type]
        else:
            r = FieldRenderer
        return r(self, field, **kwargs)

    def render_fields(self, fields):
        l = []
        for i in fields:
            if isinstance(i, HiddenField):
                continue
            l.append(self.render_field(i))
            
        return Markup("").join(l)

    def hidden_errors(self, form):
        l = (Markup("").join((Markup('<p class="error">{}</p>').format(j)
                              for j in i.errors))
             for i in form if not isinstance(i, HiddenField))
        return Markup("").join(l)
    
    def render(self, form):
        contents=Markup("{}{}{}{}").format(
            form.hidden_tag(),
            self.hidden_errors(form),
            self.render_fields(form),
            self.render_footer()
        )
        
        attrs = dict(self.form_attrs)
        if any((isinstance(i, FileField) for i in form)):
            attrs["enctype"] = "multipart/form-data"
        
        return element("form", attrs, contents)

    def render_footer(self):
        return ""
    
    def __html__(self):
        return self.render(self.form)

def field_renderer(t):
    def wrap(cls):
        field_renderers[t] = cls
        return cls

class VerticalFormView(FormView):
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
    def __init__(self, form, widths=[3, 9], size="md", **kwargs):
        super(HorizontalFormView, self).__init__(form, **kwargs)
        self.label_args= {"class": "col-{}-{}".format(size, widths[0])}
        self.field_div_attrs = {"class": "col-{}-{}".format(size, widths[1])}
        self.form_attrs = {"class": "form-horizontal"}
