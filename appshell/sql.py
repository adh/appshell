from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms_alchemy import model_form_factory
from appshell.tables import TableDataSource, SequenceTableDataSource, \
    SelectFilter, MultiSelectFilter, Column, TextFilter, ActionColumnMixin
from sqlalchemy.sql import expression as ex
from sqlalchemy import desc

db = SQLAlchemy()

BaseModelForm = model_form_factory(Form)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

def register_in_app(app):
    db.init_app(app)

class SQLColumn(Column):
    def __init__(self, name, expression, **kwargs):
        super(SQLColumn, self).__init__(name, 
                                        expression=expression, 
                                        **kwargs)
        self.expression = expression
        
    def get_sql_select_column(self):
        return self.expression

    def get_cell_data(self, row):
        return row[self.expression]

class SQLActionColumn(ActionColumnMixin, SQLColumn):
    pass
    
class SQLFilter(object):
    def __init__(self, column, **kwargs):
        super(SQLColumnFilterMixin, self).__init__(column=column, **kwargs)
        self.column = column

    def get_column_to_filter(self, column):
        if self.filter_expr:
            return self.filter_expr
        else:
            return column.get_sql_select_column()

    def sql_append_where(self, column, q, filter_data):
        raise NotImplemented

class SQLPrefixFilter(TextFilter, SQLFilter):
    def sql_append_where(self, column, q, filter_data):
        return q.where(self.get_column_to_filter(column).like(filter_data+'%'))
    
class SQLSelectFilter(SelectFilter, SQLFilter):
    def sql_append_where(self, column, q, filter_data):
        return q.where(self.get_column_to_filter(column) == filter_data)

class SQLMultiSelectFilter(MultiSelectFilter, SQLFilter):
    def sql_append_where(self, column, q, filter_data):
        fl = [i for i in filter_data.split(';') if i != '']
        return q.where(self.get_column_to_filter(column).in_(fl))
    

class SQLTableDataSource(TableDataSource):
    def __init__(self, name, columns, 
                 selectable=None,
                 selectable_proc=None,
                 **kwargs):
        super(SQLTableDataSource, self).__init__(name, 
                                                 columns,
                                                 selectable=selectable,
                                                 selectable_proc=selectable_proc,
                                                 **kwargs)
        self.selectable = selectable
        self.selectable_proc = selectable_proc
        
    def get_selectable(self):
        if self.selectable_proc:
            return self.selectable_proc()
        else:
            return self.selectable

    def get_select(self):
        cs = [c.get_sql_select_column() 
              for c in self.columns if hasattr(c, 'get_sql_select_column')]

        print repr(cs)

        return ex.select(cs)

    def apply_filters(self, q, filter_data):
        for idx, i in enumerate(self.columns):
            if i.filter and filter_data[idx]:
                q = i.filter.sql_append_where(i, q, filter_data[idx])
        return q

    def get_data(self, start, length, search, ordering, column_filters, **args):
        q = self.get_select()
        total = db.session.execute(q.count()).first()[0]

        q = self.apply_filters(q, column_filters)
        
        filtered = db.session.execute(q.count()).first()[0]

        for i, d in ordering:
            col = self.columns[i].get_sql_select_column()
            if d == 'desc':
                col = desc(col)
            q =q.order_by(col)

        q = q.limit(length).offset(start)
        return db.session.execute(q), total, filtered
