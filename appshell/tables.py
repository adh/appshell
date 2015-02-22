from flask import render_template, jsonify, request
from markupsafe import Markup
from appshell.markup import element, link_button
from appshell.urls import res_url, url_or_url_for

class Column(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.header = Markup("<th>{0}</th>").format(name)
    def get_cell_html(self, row):
        return element("td", {}, self.get_cell_inner_html(row))
    def get_cell_inner_html(self, row):
        return self.get_cell_data(row)
    def get_json_data(self, row):
        return unicode(self.get_cell_inner_html(row))

    def get_filter_html(self, column_index, table_name):
        return Markup('''<input type="text" 
                                class="tablefilter form-control" 
                                data-tablefilter-column="{0}"
                                data-tablefilter-target="{1}"/>''')\
            .format(column_index, table_name)

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
        return getattr(row, self.attr)

class DescriptorColumn(Column):
    def __init__(self, name, descriptor, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.descriptor = descriptor
    def get_cell_data(self, row):
        return self.descriptor.fget(row)
        

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
        return url_or_url_for(self.endpoint, params)

    def get_button(self, data, size=None):
        return link_button(self.get_url(data),
                           self.text,
                           context_class=self.context_class,
                           size=size)

class ActionColumnMixin(object):
    actions = []
    def __init__(self, name, actions=None, **kwargs):
        super(ActionColumnMixin, self).__init__(name, 
                                                actions=actions, 
                                                **kwargs)
        if actions:
            self.actions = actions

    def get_cell_inner_html(self, row):
        res = [i.get_button(self.get_cell_data(row)) for i in self.actions]

class ActionSequenceColumn(ActionColumnMixin, SequenceColumn):
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
        return self._options


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
    def __init__(self, name, columns, param_string=""):
        self.name = name
        self.columns = self.transform_columns(columns)
        self.param_string = param_string
        
    def data_view(self, **args):
        draw = int(request.args["draw"])
        start = int(request.args["start"])
        length = int(request.args["length"])
        search = unicode(request.args["search[value]"])

        ordering = []
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
                        "data": data})

    def register_view(self, f):
        endpoint = "data-source/" + self.name

        f.add_url_rule("/appshell/data-source/table/{0}/{1}{2}.json"
                       .format(f.name,
                               self.name, 
                               self.param_string),
                       endpoint=endpoint,
                       view_func=self.data_view)

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
        res = {"ajax": res_url(self.data_source.endpoint, **self.params),
               "scrollY": -150,
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


    
