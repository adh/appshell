from flask.ext.wtf import Form
from flask import render_template
from wtforms.widgets import TextArea, TextInput
from wtforms.fields import HiddenField, FileField
from wtforms import fields
from appshell.markup import element, button, link_button, GridColumn
from markupsafe import Markup
from flask.ext.babelex import Babel, Domain
from itertools import chain
from hashlib import sha256
from appshell.widgets import ClientSideTabbar
from appshell import View
from appshell.templates import single_view

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

class DateWidget(TextInput):
    def __call__(self, field, **kwargs):
        i = super(DateWidget, self).__call__(field, **kwargs)
        
        i = Markup("""<div class="input-group date"
                           data-provide="datepicker"
                           data-date-format="yyyy-mm-dd">
                        {}  
                        <span class="input-group-addon"><i class="glyphicon glyphicon-calendar"></i></span>
                      </div>""").format(i)
        return i

class DateField(fields.DateField):
    widget = DateWidget()
    
    

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
        self.error_attrs = {}
        self.description_attrs = {}
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
             for i in form if isinstance(i, HiddenField))
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

    def get_formfield_view(self):
        return self
    
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
    return wrap

@field_renderer('RadioField')
class RadioFieldRenderer(FieldRenderer):
    def render_input(self):
        itms = (Markup('<div class="radio"><label>{} {}</label></div>').
                format(Markup(i), Markup(i.label.text))
                for i in self.field)
        return Markup("").join(itms)


@field_renderer('BooleanField')
class BooleanFieldRenderer(FieldRenderer):
    def render_input(self):
        return Markup(self.field(**self.kwargs))
        
    def __html__(self):
        l = ""
        if self.view.label_args:
            l = element("div", self.view.label_args, "")

        i = Markup('<div class="checkbox"><label>{} {}</label>{}{}</div>')\
            .format(self.render_input(),
                    self.field.label.text,
                    self.render_description(),
                    self.render_errors())
        
        if self.view.field_div_attrs:
            i = element("div", self.view.field_div_attrs, i)

        return l+i

@field_renderer('FormField')
class FormFieldRenderer(FieldRenderer):
    def render_input(self):
        v = self.view.get_formfield_view()
        c = Markup("{}{}").format(self.field.hidden_tag(),
                                     v.render_fields(self.field,
                                                     form_info=self.form_info))
        return element("div", v.form_attrs, c)
        
    def render_errors(self):
        return ""
    
class VerticalFormView(FormView):
    def __init__(self, **kwargs):
        super(VerticalFormView, self).__init__(**kwargs)
        if any((isinstance(i, ButtonGroup) for i in self.buttons)):
            self.button_bar_attrs = {"class": "btn-toolbar"}
        self.error_attrs = {"class": "help-block"}
        self.description_attrs = {"class": "help-block"}
        self.formfield_view = None
    
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

    def get_formfield_view(self):
        return self.formfield_view or HorizontalFormView()

    
class HorizontalFormView(VerticalFormView):
    def __init__(self, widths=[3, 9], size="md", **kwargs):
        super(HorizontalFormView, self).__init__(**kwargs)
        self.label_args= {"class": "col-{}-{}".format(size, widths[0])}
        self.field_div_attrs = {"class": "col-{}-{}".format(size, widths[1])}
        self.form_attrs = {"class": "form-horizontal"}
        
class FormPart(object):
    __slots__ = ["fields", "view", "name", "title"]
    def __init__(self, title, view, fields=None, name=None):
        self.title = title
        self.view = view
        if fields is None:
            self.fields = view.get_owned_fields()
        else:
            self.fields = fields

        if name is None:
            self.name = "form-part-" + sha256(title).hexdigest()
        else:
            self.name = name
            
    def get_owned_fields(self):
        return self.fields

    def filter_own_fields(self, fields):
        own = []
        own_set = set()
        rest = []

        for i in self.get_owned_fields():
            for j in fields:
                if j.name == i:
                    own.append(j)
                    own_set.add(j)

        rest = [i for i in fields if i not in own_set]

        return own, rest
    
class HierarchicalFormView(FormView):
    def __init__(self, rest_view=None, **kwargs):
        super(HierarchicalFormView, self).__init__(**kwargs)
        self.rest_view = rest_view
        self.parts = []
        
    def get_owned_fields(self):
        return chain(*(i.get_owned_fields() for i in self.tabs))

    def add_part(self, part):
        self.parts.append(part)

    
class TabbedFormView(HierarchicalFormView):
    def add_tab(self, title, fields=None, view=None, name=None):
        if view is None:
            view = HorizontalFormView()
        self.add_part(FormPart(title, view, fields=fields, name=name))

    def render_fields(self, fields, form_info=None):
        tb = ClientSideTabbar()
        f = fields
        for i in self.parts:
            of, f = i.filter_own_fields(f)

            t = i.title

            if any((i.errors for i in of)):
                t = Markup('<span class="text-danger"><span class="glyphicon glyphicon-warning-sign"> {}</span>').format(t) 
            
            tb.add_tab(t,
                       element("div",
                               i.view.form_attrs,
                               i.view.render_fields(of, form_info=form_info)),
                       name=i.name)
        rest = ""
        if f:
            if not self.rest_view:
                raise ValueError("Not all fields assigned to parts")
            
            rest = element("div",
                           self.rest_view.form_attrs,
                           self.rest_view.render_fields(f,
                                                        form_info=form_info))

        return Markup("{}{}").format(rest, tb)

class FormPanel(FormPart):
    __slots__ = ["footer", "width", "border", "column"]
    def __init__(self, view,
                 title=None, footer=None, name=None,
                 width=None,
                 column=None,
                 border="default",
                 **kwargs):
        
        if name is None:
            name = "form-panel-" + sha256(u"{}{}".format(title,
                                                         footer)).hexdigest()

        super(FormPanel, self).__init__(title, view,
                                       name=name,
                                       **kwargs)

        self.footer = footer
        self.width = width
        self.border = border
        if column is None:
            if width is not None:
                column = GridColumn(width=width)
        self.column = column

    def should_be_wrapped_in_row(self):
        return self.column is not None
        
    def panel_wrapper(self, content):
        if self.border is not None:
            content = element("div",
                              {"class": "panel-body"},
                              content)

            if self.title is not None:
                content = element("div",
                                  {"class": "panel-heading"},
                                  self.title) + content
            
            content = element("div",
                              {"class": "panel panel-{}".format(self.border)},
                              content)


        if self.column:
            content = self.column.render(content)
            
        return content
        
class PanelizedFormView(HierarchicalFormView):
    def __init__(self, breakpoint='md', **kwargs):
        super(PanelizedFormView, self).__init__(**kwargs)
        self.breakpoint = breakpoint
    
    def add_panel(self,
                  title=None,
                  fields=None,
                  width=None,
                  column=None,
                  footer=None,
                  view=None,
                  name=None,
                  border="default"):
        if view is None:
            view = VerticalFormView()
            
        self.add_part(FormPanel(view,
                                title=title,
                                footer=footer,
                                fields=fields,
                                name=name,
                                border=border,
                                width=width,
                                column=column))

    def render_fields(self, fields, form_info=None):
        f = fields
        output = []
        to_wrap = []
        wrapped = False
        for i in self.parts:
            of, f = i.filter_own_fields(f)

            t = i.title

            fm = element("div",
                         i.view.form_attrs,
                         i.view.render_fields(of,
                                              form_info=form_info))

            if i.should_be_wrapped_in_row():
                to_wrap.append(i.panel_wrapper(fm))
                
            else:
                if to_wrap:
                    output.append(element("div",
                                         {"class": "row"},
                                         Markup("").join(to_wrap)))
                to_wrap = []

                output.append(i.panel_wrapper(fm))

        if to_wrap:
            output.append(element("div",
                                  {"class": "row"},
                                  Markup("").join(to_wrap)))
                
        return Markup("").join(output)
            
        
        
class FormEndpoint(View):
    methods = ['GET', 'POST']
    formview = HorizontalFormView()
    def __init__(self):
        self.page_args = {}

    def get_form_info(self):
        return {}
    
    def dispatch_request(self, **kwargs):
        self.form = self.create_form(**kwargs)
        if self.form.validate_on_submit():
            res = self.submitted(**kwargs)
            if res is not None:
                return res
        return self.render_form(**kwargs)

    def render_template(self, form):
        return single_view(form, **self.page_args)
    
    def render_form(self, **kwargs):
        return self.render_template(self.formview(self.form,
                                                  form_info=self.get_form_info()))

        
