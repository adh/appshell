from flask import render_template, jsonify, request
from markupsafe import Markup
from appshell.markup import element, link_button, button, xmltag
from appshell.urls import res_url, url_or_url_for
from appshell.templates import widgets, dropdowns, modals
import iso8601
import datetime

from flask.ext.babelex import Babel, Domain

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext

class Column(object):
    orderable = True

    def __init__(self, 
                 name, 
                 filter=None,
                 options={},
                 orderable=None,
                 convert=None,
                 data_proc=None,
                 **kwargs):
        self.name = name
        self.header = Markup("<th>{0}</th>").format(name)
        self.filter = filter
        self._options = options
        self.convert = convert
        if orderable != None:
            self.orderable = orderable
        if data_proc:
            self.get_cell_data = data_proc

    @property
    def options(self):
        o = dict(self._options)
        o["orderable"] = self.orderable
        return o

    def get_cell_html(self, row):
        return element("td", {}, self.get_cell_inner_html(row))

    def get_cell_inner_html(self, row):
        if self.convert:
            return self.convert(self.get_cell_data(row))

        return self.get_cell_data(row)

    def get_json_data(self, row):
        return unicode(self.get_cell_inner_html(row))

    def get_filter_html(self, column_index, table):
        if self.filter:
            return self.filter.get_filter_html(column_index,
                                               self,
                                               table)
        else:
            return ""


class Filter(object):
    def __init__(self, filter_value=None, filter_value_proc=None, **kwargs):
        self.filter_value = filter_value
        self.filter_value_proc = filter_value_proc

    def get_filter_value(self):
        fs = self.filter_value
        if self.filter_value_proc:
            fs= self.filter_value_proc()
        if fs == None:
            fs = ""
        return fs
    

class TextFilter(Filter):
    def get_filter_html(self, column_index, column, table):
        return Markup('''<input type="text" 
                                value="{2}"
                                class="tablefilter form-control input-sm" 
                                data-tablefilter-column="{0}"
                                data-tablefilter-target="{1}"/>''')\
            .format(column_index, table.name, 
                    self.get_filter_value())


class SelectFilter(Filter):
    def __init__(self,
                 filter_data=None,
                 filter_data_proc=None,
                 **kwargs):
        super(SelectFilter, self).__init__(filter_data=filter_data,
                                           filter_data_proc=filter_data_proc,
                                           **kwargs)
        self.filter_data = filter_data
        self.filter_data_proc = filter_data_proc

    def get_filter_data(self):
        fd = self.filter_data
        if self.filter_data_proc:
            fd= self.filter_data_proc()
        return fd
    

    def get_filter_html(self, column_index, column, table):
        return widgets.select("filter_" + str(id(self)), 
                              self.get_filter_value(), 
                              [('', '')] + self.get_filter_data(),
                              select_attrs={"data-tablefilter-column": column_index,
                                            "data-tablefilter-target": table.name},
                              select_classes="tablefilter input-sm")
    
class MultiSelectFilter(SelectFilter):
    def get_filter_html(self, column_index, column, table):
        return modals.modal_checklist("filter_"+str(id(self)),
                                      self.get_filter_value(),
                                      self.get_filter_data(),
                                      input_attrs={"data-tablefilter-column": column_index,
                                                   "data-tablefilter-target": table.name},
                                      input_classes="tablefilter")

class MultiSelectTreeFilter(MultiSelectFilter):
    def get_filter_html(self, column_index, column, table):
        return modals.modal_checktree("filter_"+str(id(self)),
                                      self.get_filter_value(),
                                      self.get_filter_data(),
                                      input_attrs={"data-tablefilter-column": column_index,
                                                   "data-tablefilter-target": table.name},
                                      input_classes="tablefilter")
    

class RangeFilter(Filter):
    def get_filter_value(self):
        v = super(RangeFilter, self).get_filter_value()
        if v:
            return v
        else:
            return ';'

    def parse_filter_data(self, data):
        if data:
            return data.split(';')
        else:
            return [None, None]
    def get_filter_html(self, column_index, column, table):
        return widgets.rangeinput("filter_"+str(id(self)),
                                  self.parse_filter_data(self.get_filter_value()),
                                  classes="tablefilter-range",
                                  root_attrs={"data-tablefilter-column": column_index,
                                              "data-tablefilter-target": table.name})

class DateRangeFilter(RangeFilter):
    def __init__(self, default_last=None, **kwargs):
        super(DateRangeFilter, self).__init__(default_last=default_last, 
                                              **kwargs)
        self.default_last = default_last

    def get_filter_value(self):
        v = super(DateRangeFilter, self).get_filter_value()
        if v and v != ';':
            return v
        if self.default_last:
            t = datetime.date.today() + datetime.timedelta(days=1)
            f = (t - datetime.timedelta(days=self.default_last))
            return f.isoformat() + ';' + t.isoformat()
        return ';'


    def parse_filter_data(self, data):
        f, t = [iso8601.parse_date(i).date() if i else '' 
                for i in data.split(';')]
        return f, t

    def get_filter_html(self, column_index, column, table):
        return widgets.daterange("filter_"+str(id(self)),
                                 self.parse_filter_data(self.get_filter_value()),
                                 classes="tablefilter-range",
                                 root_attrs={"data-tablefilter-column": column_index,
                                             "data-tablefilter-target": table.name})


class SequenceColumn(Column):
    def __init__(self, name, index, **kwargs):
        super(SequenceColumn, self).__init__(name, index=index, **kwargs)
        self.index = index
    def get_cell_data(self, row):
        return row[self.index]

class ObjectColumn(Column): 
    def __init__(self, name, attr, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.attr = attr
    def get_cell_data(self, row):
        r = row
        for i in self.attr.split('.'):
            r = getattr(r, i)
            if r is None:
                return None
        return r

class DescriptorColumn(Column):
    def __init__(self, name, descriptor, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.descriptor = descriptor
    def get_cell_data(self, row):
        return self.descriptor.fget(row)

class CustomSelectColumnMixin(object):
    def __init__(self, name, label=None, text_proc=None, **kwargs):
        super(CustomSelectColumnMixin, self).__init__(name, 
                                                      text_proc=text_proc, 
                                                      label=label,
                                                      **kwargs)

        if label is None:
            label = lazy_gettext("Select")
        if text_proc is None:
            text_proc = lambda d, r: d

        self.text_proc = text_proc
        self.label = label

    def get_cell_inner_html(self, row):
        d = self.get_cell_data(row)
        return button(self.label, "custom-select-item",
                      size="sm",
                      attrs={"data-value": d,
                             "data-text": self.text_proc(d, row)})
        
class CustomSelectSequenceColumn(CustomSelectColumnMixin, SequenceColumn):
    pass
    
class CheckBoxColumnMixin(object):
    def __init__(self, name, text_proc=None, checkbox_attrs={}, **kwargs):
        super(CheckBoxColumnMixin, self).__init__(name, 
                                                  text_proc=text_proc, 
                                                  checkbox_attrs=checkbox_attrs,
                                                  **kwargs)
        if text_proc is None:
            text_proc = lambda d, r: d

        self.text_proc = text_proc
        self.checkbox_attrs = checkbox_attrs

    def get_cell_inner_html(self, row):
        d = self.get_cell_data(row)
        attrs = {"value": d, "type": "checkbox"}
        attrs.update(self.checkbox_attrs)
        return Markup("<label>{0}{1}</label>")\
            .format(xmltag("input", attrs), self.text_proc(d, row))

class CheckBoxSequenceColumn(CheckBoxColumnMixin, SequenceColumn):
    pass
                       

class Action(object):
    __slots__ = ('text', 'endpoint', 'params', 'data_param', 'context_class')
    def __init__(self, 
                 text, 
                 endpoint, 
                 data_param='id', 
                 context_class='default', 
                 **params):
        self.text = text
        self.endpoint = endpoint
        self.data_param = data_param
        self.context_class = context_class
        self.params = params

    def get_url(self, data):
        params = dict(self.params)
        params[self.data_param] = data
        return url_or_url_for(self.endpoint, **params)

    def get_button(self, data, size=None):
        return link_button(self.get_url(data),
                           self.text,
                           context_class=self.context_class,
                           size=size)

class ActionColumnMixin(object):
    orderable = False
    actions = []
    def __init__(self, name, actions=None, **kwargs):
        super(ActionColumnMixin, self).__init__(name, 
                                                actions=actions, 
                                                **kwargs)
        if actions:
            self.actions = actions

    def get_cell_inner_html(self, row):
        res = [i.get_button(self.get_cell_data(row), size='xs') for i in self.actions]
        return Markup("").join(res)

class ActionColumn(ActionColumnMixin, Column):
    pass
class ActionSequenceColumn(ActionColumnMixin, SequenceColumn):
    pass
class ActionObjectColumn(ActionColumnMixin, ObjectColumn):
    pass

class ColumnsMixin(object):
    def transform_columns(self, columns):
        return [i if isinstance(i, Column) else self.column_factory(i, 
                                                                    index=idx) 
                for idx, i in enumerate(columns)]

    def column_factory(self, i, index):
        return i


class DataTable(ColumnsMixin):
    def __init__(self, 
                 name, 
                 columns, 
                 data, 
                 options={}, 
                 filters=None, 
                 attrs=None,
                 **kwargs):
        if attrs == None:
            attrs = {"cellspacing": "0",
                     "width": "100%"}

        self.attrs = attrs
        self._options = options
        self.name = name
        self.columns = self.transform_columns(columns)
        self.data = self.transform_data(data)
        self.filters = filters

    @property
    def options(self):
        o = dict(self._options)
        o["columns"] = [ c.options for c in self.columns]
        return o

    def default_filters(self):
        return [ {"search": c.filter.get_filter_value() if c.filter else None} 
                 for c in self.columns ]

    def __html__(self):
        return render_template('appshell/datatable.html',
                               table=self)


class TableRow(object):
    def __init__(self, data, columns):
        self.data = data
        self.columns = columns
    
    def get_row_contents(self):
        cols = []
        for i in self.columns:
            cols.append(i.get_cell_html(self.data))
        return Markup("").join(cols)

    def __html__(self):
        return element("tr", 
                       self.get_element_attrs(), 
                       self.get_row_contents())

    def get_element_attrs(self):
        classes = " ".join(self.get_element_classes())
        if classes:
            return {"class": classes}
        else:
            return {}

    def get_element_classes(self):
        return []
        

class SequenceColumnMixin(object):
    column_factory=SequenceColumn

class IterableDataTable(DataTable):
    row_factory = TableRow

    def __init__(self, name, columns, data, options=None, **kwargs):
        if options == None:
            options = {"paging": False, "fixed_header": {"bottom": True}}
        super(IterableDataTable, self).__init__(name, columns, data, 
                                                options=options, 
                                                **kwargs)

    def transform_data(self, data):
        return [self.row_factory(i, self.columns) for i in data]

    @property
    def column_headers(self):
        return self.columns

class PlainTable(SequenceColumnMixin, IterableDataTable):
    pass

class TableDataSource(ColumnsMixin):
    def __init__(self, name, columns, param_string="", **kwargs):
        self.name = name
        self.columns = self.transform_columns(columns)
        self.param_string = param_string
        
    def data_view(self, **args):
        draw = int(request.args["draw"])
        start = int(request.args["start"])
        length = int(request.args["length"])
        search = unicode(request.args["search[value]"])

        ordering = []
        i = 0
        while "order[{0}][column]".format(i) in request.args:
            ordering.append((int(request.args["order[{0}][column]".format(i)]),
                             request.args["order[{0}][dir]".format(i)]))
            i +=1

        column_filters = [ request.args["columns[{0}][search][value]"
                                        .format(i)]
                           for i in xrange(len(self.columns))]
        

        data, total, filtered = self.get_data(start, length, search, 
                                              ordering, column_filters,
                                              **args)
        jdata = [[c.get_json_data(i) for c in self.columns] 
                 for i in data]

        return jsonify({"draw": draw,
                        "recordsTotal": total,
                        "recordsFiltered": filtered,
                        "data": jdata})

    def register_view(self, f):
        endpoint = "data-source/" + self.name

        f.add_url_rule("/appshell/data-source/table/{0}/{1}{2}.json"
                       .format(f.name,
                               self.name, 
                               self.param_string),
                       endpoint=endpoint,
                       view_func=self.data_view,
        )

        self.endpoint = f.name + "." + endpoint

    def data_source(self, fn):
        self.get_data = fn

class SequenceTableDataSource(SequenceColumnMixin, TableDataSource):
    pass



class VirtualTable(DataTable):
    def __init__(self, data_source, name=None, options=None, params={}, **kwargs):
        if options == None:
            options = {}
        if name == None:
            name = data_source.name
        super(VirtualTable, self).__init__(name=name, 
                                           columns=data_source.columns, 
                                           data=[], 
                                           options=options, **kwargs)

        self.data_source = data_source
        self.params = params


    def transform_data(self, data):
        return []

    @property
    def options(self):
        orig = super(VirtualTable, self).options
        res = {"ajax": 
               {
                   "url": res_url(self.data_source.endpoint, **self.params),
               },
               "scrollY": -150,
               "scrollX": True,
               "dom": "rtS",
               "ordering": False,
               "searching": True,
               "deferRender": True,
               "serverSide": True}
        for k, v in orig.iteritems():
            if v == None:
                del res[k]
            else:
                res[k] = v
        return res


    
