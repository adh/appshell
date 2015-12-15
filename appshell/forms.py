from flask.ext.wtf import Form
from flask import render_template
from wtforms.widgets import TextArea, TextInput
from wtforms.fields import HiddenField, FileField
from wtforms import fields, widgets, Form
from appshell.markup import element, button, link_button, GridColumn
from markupsafe import Markup
from flask.ext.babelex import Babel, Domain
from itertools import chain
from hashlib import sha256
from appshell.widgets import ClientSideTabbar
from appshell import View
from appshell.templates import single_view
from wtforms.validators import StopValidation

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
        try:
            if self.field.widget.suppress_form_decoration:
                return self.field.widget(self.field)
        except:
            pass

        if self.view.want_labels:
            l = self.render_label()
            

            if l is None:
                field_div_attrs = self.view.field_div_attrs_no_label
                l = ""
            else:
                field_div_attrs = self.view.field_div_attrs
        else:
            field_div_attrs = self.view.field_div_attrs
            l = ""
        
        i = Markup("{}{}{}").format(self.render_input(),
                                    self.render_description(),
                                    self.render_errors())
        
        if field_div_attrs:
            i = element("div", field_div_attrs, i)

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
                      context_class=self.context_class,
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
    want_labels = True
    
    def __init__(self,
                 buttons=None,
                 method="POST",
                 field_order=None,
                 **kwargs):
        self.field_renderers = {}
        self.label_args = {}
        self.field_div_attrs = None
        self.field_div_attrs_no_label = None
        self.form_attrs = {}
        self.button_bar_attrs = {}
        self.method = method
        self.error_attrs = {}
        self.description_attrs = {}
        self.field_order = field_order
        if buttons is None:
            self.buttons = [SubmitButton(lazy_gettext("OK"))]
        else:
            self.buttons = buttons
        
    def get_field_args(self, field):
        return {}
            
    def render_field(self, field, form_info=None, **kwargs):
        try:
            if field.widget.suppress_form_decoration:
                return field.widget(field)
        except:
            pass

        if field.type in field_renderers:
            r = field_renderers[field.type]
        elif hasattr(field, 'renderer'):
            r = field.renderer
        else:
            r = FieldRenderer
        return r(self, field, form_info=form_info, **kwargs)

    def render_fields(self, fields, form_info=None, **kwargs):
        l = []
        if self.field_order:
            for i in self.field_order:
                l.append(self.render_field(fields[i],
                                           form_info=form_info,
                                           **kwargs))                
        else:
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


@field_renderer('SubmitField')
class SubmitFieldRenderer(FieldRenderer):
    def render_label(self):
        return None

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
    formfield_view = None
    
    def __init__(self, formfield_view=None, **kwargs):
        super(VerticalFormView, self).__init__(**kwargs)
        if any((isinstance(i, ButtonGroup) for i in self.buttons)):
            self.button_bar_attrs = {"class": "btn-toolbar"}
        self.error_attrs = {"class": "help-block"}
        self.description_attrs = {"class": "help-block"}
        if formfield_view is not None:
            self.formfield_view = formfield_view
    
    def render_field(self, field, **kwargs):
        try:
            if field.widget.suppress_form_decoration:
                return field.widget(field)
        except:
            pass

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
        self.label_args= {"class": "control-label col-{}-{}".format(size,
                                                                    widths[0])}
        self.field_div_attrs = {"class": "col-{}-{}".format(size, widths[1])}
        self.field_div_attrs_no_label = {
            "class": "col-{}-{} col-{}-offset-{}".format(size, widths[1],
                                                         size, widths[0])
        }
        self.form_attrs = {"class": "form-horizontal"}

    def render_footer(self, form_info=None):
        f = super(HorizontalFormView, self).render_footer(form_info=form_info)
        if not f:
            return ""
        
        return element("div", {"class": "form-group"},
                       element("div", self.field_div_attrs_no_label, f))
        
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
            self.name = "form-part-" + sha256(title.encode("utf-8")).hexdigest()
        else:
            self.name = name
            
    def get_owned_fields(self):
        return self.fields

    def filter_own_fields(self, fields):
        own = []
        own_set = set()
        rest = []

        for i in self.get_owned_fields():
            if i[-1] == '*':
                for j in fields:
                    if j.name.startswith(i[:-1]):
                        own.append(j)
                        own_set.add(j)
            else:
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
                                                         footer).encode("utf-8")).hexdigest()

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

class FormBox(FormPanel):
    def panel_wrapper(self, content):
        if self.border is not None:
            content = element("div",
                              {"class": "box-body"},
                              content)

            if self.title is not None:
                content = element("div",
                                  {"class": "box-header with-border"},
                                  element("h3",
                                          {"class": "box-title"},
                                          self.title)) + content
            
            content = element("div",
                              {"class": "box box-{}".format(self.border)},
                              content)


        if self.column:
            content = self.column.render(content)
            
        return content
    
    
class PanelizedFormView(HierarchicalFormView):
    PanelClass = FormPanel
    
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
            
        self.add_part(self.PanelClass(view,
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

class BoxedFormView(PanelizedFormView):
    PanelClass = FormBox
        
        
class FormEndpoint(View):
    methods = ['GET', 'POST']
    formview = HorizontalFormView()

    def get_form_info(self):
        return {}
    
    def dispatch_request(self, **kwargs):
        self.form = self.create_form(**kwargs)
        if self.form.validate_on_submit():
            res = self.submitted(**kwargs)
            if res is not None:
                return res
        return self.render_form(**kwargs)
    
    def render_form(self, **kwargs):
        return self.render_template(self.formview(self.form,
                                                  form_info=self.get_form_info()))

class ButtonWidget(widgets.SubmitInput):
    def __init__(self, size=None, context_class='primary', **kwargs):
        self.size = size
        self.context_class = context_class
        return super(ButtonWidget, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        klass = " btn btn-{}".format(self.context_class)
        
        if self.size:
            klass += " btn-" + self.size
            
        kwargs['class'] = klass
        return super(ButtonWidget, self).__call__(field, **kwargs)

class TableRowFormView(FormView):
    formfield_view = None
    want_labels = False
    
    def get_field_args(self, field):
        return {"class": "form-control"}

    def render_field(self, field, **kwargs):
        cls = ""
        if field.errors:
            cls += " has-error"
        if field.flags.required:
            cls += " required"
            
        return element("td", {"class": cls},
                       super(TableRowFormView, self).render_field(field,
                                                                  **kwargs)) 

class ButtonField(fields.SubmitField):
    widget = ButtonWidget()
    renderer = SubmitFieldRenderer

class StaticTextWidget(object):
    def __call__(self, field, **kwargs):
        value = field.data
        if 'value' in kwargs:
            value = kwargs['value']
        
        input = Markup('<input type="hidden" name="{}" value="{}">')\
                .format(field.name, value)

        text = self.get_text(value, field)
        
        return Markup('{}<span>{}</span>').format(input, text)

    def get_text(self, value, field):
        return value

class StaticSelectWidget(StaticTextWidget):
    def get_text(self, value, field):
        for val, label, selected in field.iter_choices():
            if val == value:
                return label
        return ""

    
class CollectionWidget(object):
    entry_view = HorizontalFormView()
    add_view = HorizontalFormView()

    suppress_form_decoration = True
    
    def __init__(self,
                 entry_view=None,
                 add_view=None):
        if self.entry_view:
            self.entry_view = entry_view
        if self.add_view:
            self.add_view = add_view
        
    def render_add(self, add):
        return Markup("{}{}").format(add.hidden_tag(),
                                     self.add_view.render_fields(add))

    def render_items(self, items):
        return Markup("").join((self.render_item(i) for i in items))

    def render_item(self, item):
        return Markup("{}{}").format(item.hidden_tag(),
                                     self.add_view.render_fields(item))

    def __call__(self, field, **kwargs):
        #c = Markup("{}{}").format(self.render,
        #                          v.render_fields(field.add,
        #                                          form_info=self.form_info))

        c = self.render_items(field.items)

        if hasattr(field, 'add'):
            c += self.render_add(field.add)
        
        return c

class TabularCollectionWidget(CollectionWidget):
    def __init__(self, headers=None, field_order=None, **kwargs):
        self.headers = headers
        self.entry_view = TableRowFormView(field_order=field_order)
        self.add_view = TableRowFormView(field_order=field_order)
        
    def __call__(self, field, **kwargs):
        return Markup('<table class="table table-striped table-hover">{}{}</table>')\
            .format(self.render_header(field),
                    super(TabularCollectionWidget, self).__call__(field,
                                                                  **kwargs))
    def render_add(self, add):
        return Markup('<tr>{}</tr>').format(super(TabularCollectionWidget,
                                                  self).render_add(add))
    def render_item(self, item):
        return Markup('<tr>{}</tr>').format(super(TabularCollectionWidget,
                                                  self).render_item(item))

    def render_header(self, field):
        if not self.headers:
            return ""
        
        h = Markup("").join((Markup("<th>{}</th>").format(i)
                             for i in self.headers))
        return Markup('<thead><tr>{}</tr></thead>').format(h)


def model_constructor(cls):
    def constructor(data):
        o = cls()
        for k, v in data.items():
            print((k,v))
            setattr(o, k, v)
        return o
    return constructor
    
class CollectionField(fields.FormField):
    widget = CollectionWidget()
    
    def __init__(self, item_class, add_class=None,
                 item_constructor=dict,
                 **kwargs):
        class CollectionForm(Form):
            items = fields.FieldList(fields.FormField(item_class))


            
        if add_class:
            CollectionForm.add = fields.FormField(add_class)

        self.item_constructor = item_constructor
            
        super(CollectionField,self).__init__(CollectionForm, **kwargs)

    def validate(self, form, extra_validators=tuple()):
        res = self.form.items.validate(form, extra_validators)
        to_delete = None
        for idx, i in enumerate(self.form.items):
            if hasattr(i, 'collection_action'):
                print(i.collection_action)
                if i.collection_action.data:
                    to_delete = idx

        if to_delete is not None:
            self.remove_entry(to_delete)
            res = False 
        elif hasattr(self.form, 'add') \
           and hasattr(self.form.add.form, 'collection_action'):
            if self.form.add.form.collection_action.data:
                if self.form.add.validate(form, extra_validators):
                    self.add_entry(self.form.add.data)
                    self.form.add.form.clear_form()
                    res = False
                else:
                    res = False
            
        return res

    def remove_entry(self, idx):
        del self.items.entries[idx]
        self.items.last_index -= 1

    def add_entry(self, data=None):
        self.form.items.append_entry(data)


    def process(self, formdata=None, data=None, **kwargs):
        super(CollectionField, self).process(formdata, data, **kwargs)
        if data is not None:
            self.form.items.process(formdata, data, **kwargs)

    def populate_obj(self, obj, name):
        candidate = [self.item_constructor(i) for i in self.items.data]
        setattr(obj, name, candidate)

        #self.form.populate_obj(candidate)

        #return self.items.populate_obj(obj, name)
    
        
class CollectionAddButton(ButtonField):
    widget = ButtonWidget(context_class="success")

class CollectionDeleteButton(ButtonField):
    widget = ButtonWidget(context_class="danger")

class CollectionAddFormMixin(object):
    def clear_form(self):
        for i in self:
            i.data = None
            
    collection_action = CollectionAddButton("Add")

class CollectionEntryFormMixin(object):
    collection_action = CollectionDeleteButton("Remove")
    
