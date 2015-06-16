from flask import render_template
from markupsafe import Markup
from appshell.tables import TableRow, SequenceColumnMixin, Column, ColumnsMixin

class TreeGridItem(object):
    def __init__(self, data, children=None):
        self.data = data
        if children == None:
            children = []
        self.children = children

    def get_id(self):
        return id(self)

    def materialize_rows(self, row_factory, columns, parent=None):
        res = [row_factory(self, parent, columns)]
        for i in self.children:
            res.extend(i.materialize_rows(row_factory, columns, self))
        return res
        

class TreeGridRow(TableRow):
    def __init__(self, item, parent, columns):
        TableRow.__init__(self, item.data, columns)
        self.my_id = item.get_id()
        self.parent_id = parent.get_id() if parent else None

    def get_element_classes(self):
        res = super(TreeGridRow, self).get_element_classes()
        res.append("treegrid-{0}".format(self.my_id))
        if self.parent_id != None: 
            res.append("treegrid-parent-{0}".format(self.parent_id))
        return res


class TreeGrid(ColumnsMixin):
    row_factory = TreeGridRow
    def __init__(self, name, columns, items, options=None, search=False):
        if (options == None):
            options = {"initialState": "collapsed",
                       'expanderExpandedClass': 'glyphicon glyphicon-folder-open',
                       'expanderCollapsedClass': 'glyphicon glyphicon-folder-close',
                       "saveState": True,
                       "saveStateName": "appshell-treegrid-"+name}
        self.options = options
        self.name = name
        self.columns = self.transform_columns(columns)
        self.items = items
        self._rows = None
        self.data = self.materialize_rows()
        self.search = search


    def materialize_rows(self):
        res = []
        for i in self.items:
            res.extend(i.materialize_rows(self.row_factory, self.columns))
        return res


    def __html__(self):
        return render_template('appshell/treegrid.html', treegrid=self)

class PlainTreeGrid(SequenceColumnMixin, TreeGrid):
    pass
