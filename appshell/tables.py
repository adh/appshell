from flask import render_template, render_template_string
from markupsafe import Markup

def table_view(columns, data, options=None):

    return render_template("appshell/table_view.html", 
                           columns=columns,
                           data=data,
                           options=options)

class Column(object):
    def __init__(self, header):
        self.header = Markup("<th>{0}</th>").format(header)
    def get_cell_html(self, row):
        return Markup("<td>{0}</td>").format(self.get_cell_contents(row))

class ListColumn(Column):
    def __init__(self, header, index):
        Column.__init__(self, header)
        self.index = index
    def get_cell_contents(self, row):
        return row[self.index]

class DataTable(object):
    def __init__(self, name, columns, rows, options={}):
        self.options = options
        self.name = name
        self.columns = columns
        self.rows = rows

    def __html__(self):
        return render_template('appshell/datatable.html',
                               table=self)

class StaticRow(object):
    def __init__(self, data, columns):
        self.data = data
        self.columns = columns
    
    def __html__(self):
        cols = []
        for i in self.columns:
            cols.append(i.get_cell_html(self.data))
            

        return Markup("<tr>{0}</tr>").format(Markup("").join(cols))

class StaticTable(DataTable):
    
    def __init__(self, name, columns, data, options=None):
        if options == None:
            options = {"paging": False, "fixed_header": True}
        self.options = options
        self.name = name
        self.columns = [ListColumn(i, idx) for idx, i in enumerate(columns)]

        self.data = [StaticRow(i, self.columns) for i in data]

    @property
    def column_headers(self):
        return self.columns

