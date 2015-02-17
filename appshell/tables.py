from flask import render_template, jsonify, url_for, request
from markupsafe import Markup
from appshell.markup import element

class Column(object):
    def __init__(self, header):
        self.header = Markup("<th>{0}</th>").format(header)
    def get_cell_html(self, row):
        return element("td", {}, self.get_cell_inner_html(row))
    def get_cell_inner_html(self, row):
        return self.get_cell_data(row)
    def get_json_data(self, row):
        return unicode(self.get_cell_inner_html(row))

class SequenceColumn(Column):
    def __init__(self, header, index):
        Column.__init__(self, header)
        self.index = index
    def get_cell_data(self, row):
        return row[self.index]
        

class DataTable(object):
    def __init__(self, name, columns, data, options={}):
        self._options = options
        self.name = name
        self.columns = self.transform_columns(columns)
        self.data = self.transform_data(data)

    @property
    def options(self):
        return self._options

    def transform_columns(self, columns):
        return columns

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
    def transform_columns(self, columns):
        return [SequenceColumn(i, idx) for idx, i in enumerate(columns)]

class IterableDataTable(DataTable):
    row_factory = TableRow

    def __init__(self, name, columns, data, options=None):
        if options == None:
            options = {"paging": False, "fixed_header": True}
        DataTable.__init__(self, name, columns, data, options)

    def transform_data(self, data):
        return [self.row_factory(i, self.columns) for i in data]

    @property
    def column_headers(self):
        return self.columns

class PlainTable(SequenceColumnMixin, IterableDataTable):
    pass

class TableDataSource(object):
    def __init__(self, name, columns, param_string=""):
        self.name = name
        self.columns = self.transform_columns(columns)
        self.param_string = param_string
        
    def transform_columns(self, columns):
        return columns

    def data_view(self, **args):
        draw = int(request.args["draw"])
        start = int(request.args["start"])
        length = int(request.args["length"])
        search = unicode(request.args["search[value]"])

        ordering = []
        column_filters = []
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
    def __init__(self, data_source, name=None, options=None, params={}):
        if options == None:
            options = {}
        if name == None:
            name = data_source.name
        DataTable.__init__(self, name, data_source.columns, [], options)
        self.data_source = data_source
        self.params = params


    def transform_data(self, data):
        return []

    @property
    def options(self):
        res = {"ajax": url_for(self.data_source.endpoint, **self.params),
               "scrollY": -150,
               "dom": "frtS",
               "ordering": False,
               "searching": False,
               "deferRender": True,
               "serverSide": True}

        return res


    
