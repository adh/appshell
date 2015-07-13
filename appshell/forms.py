from flask.ext.wtf import Form
from flask import render_template
from wtforms.widgets import TextArea
from wtforms.fields import HiddenField
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


default_field_renderers = {}

class FieldRenderer(object):
    __slots__ = ["view", "field", "kwargs"]
    def __init__(self, view, field, **kwargs):
        self.view = view
        self.field = field
        self.kwargs = kwargs

    def render_input(self):
        args = self.view.get_field_args(self.field)
        args.update(kwargs)
        return self.field(args)

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
        
    def __html__(self):
        l = self.field.label(self.view.label_args)

        i = Markup("{}{}{}").format(self.render_input(),
                                    self.render_description(),
                                    self.render_errors())
        
        if self.view.input_div_attrs:
            i = element("div", self.view.input_div_attrs, i)

        return l+i
    
class FormView(object):
    def init(self,
             form=None,
             field_type_map=None,
             **kwargs):
        self.form = form
        self.field_renderers = field_renderers
        self.label_args = {}
        if from_attrs is None:
            self.form_attrs = {}
        else:
            self.form_attrs = form_attrs

    def get_field_args(self, field):
        return {}
            
    def render_field(self, field, **kwargs):
        if self.field_renderers \
           and field.type in self.field_renderers:
            r = self.field_renderers[field.type]
        elif field.type in default_field_renderers:
            r = default_field_renderers[field.type]
        else:
            r = FieldRenderer
        return r(self, field, **kwargs)

    def render_fields(self, fields):
        l = []
        for i in fields:
            l.append(self.render_field(i))
            
        return Markup("").join(l)

    def hidden_errors(self):
        l = ((Markup('<p class="error">{}</p>').format(j) for j in i.errors)
             for i in self.form.fields if not isinstance(i, HiddenField))
        return Markup("").join(l)
    
    def render(self, fields):
        contents=Markup("{}{}{}{}").format(
            self.form.hidden_tag(),
            self.hidden_errors(),
            self.render_fields(fields),
            self.render_footer()
        )
        
        attrs = dict(self.form_attrs)
        if any((isinstance(i, FileField) for i in fields)):
            attrs["enctype"] = "multipart/form-data"
        
        return element("form", attrs, contents)

    def render_footer(self):
        return ""
    
    def __html__(self):
        return self.render(self.form)

def field_renderer(t):
    def wrap(f):
        default_field_renderers[t] = f
        return f
    
