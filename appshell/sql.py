from flask.ext.wtf import Form
from appshell.forms import OrderedForm
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms_alchemy import model_form_factory
from appshell.tables import TableDataSource, SequenceTableDataSource, \
    SelectFilter, MultiSelectFilter, Column, TextFilter, ActionColumnMixin,\
    RangeFilter, DateRangeFilter, MultiSelectTreeFilter, PlainTable, \
    ObjectColumn, Action, ActionObjectColumn
from sqlalchemy.sql import expression as ex
from sqlalchemy import desc, func
import json
from appshell.forms import FormEndpoint
from flask.ext.babelex import Babel, Domain
from appshell import View, url_for
from flask import flash, request, redirect
from appshell.endpoints import ConfirmationEndpoint

db = SQLAlchemy()

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext

BaseModelForm = model_form_factory(OrderedForm)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

def register_in_app(appshell, app):
    db.init_app(app)

class SQLColumn(Column):
    def __init__(self, name, expression, **kwargs):
        super(SQLColumn, self).__init__(name, 
                                        expression=expression, 
                                        **kwargs)
        self.expression = expression
        
    def get_sql_select_columns(self):
        return [self.expression]

    def get_cell_data(self, row):
        return row[self.expression]

class SQLActionColumn(ActionColumnMixin, SQLColumn):
    pass
    
class SQLFilter(object):
    def __init__(self, filter_expr=None,
                 **kwargs):
        super(SQLFilter, self).__init__(filter_expr=filter_expr,
                                        **kwargs)
        self.filter_expr = filter_expr

    def get_column_to_filter(self, column):
        if self.filter_expr:
            return self.filter_expr
        else:
            return column.get_sql_select_columns()[0]

    def sql_append_where(self, column, q, filter_data):
        raise NotImplemented

class SQLPrefixFilter(SQLFilter, TextFilter):
    def sql_append_where(self, column, q, filter_data):
        return q.where(self.get_column_to_filter(column).like(filter_data+'%'))

class SQLCasefoldingPrefixFilter(SQLFilter, TextFilter):
    def sql_append_where(self, column, q, filter_data):
        col = self.get_column_to_filter(column)
        return q.where(func.lower(col).like(filter_data.lower()+'%'))
    
class SQLSelectFilter(SQLFilter, SelectFilter):
    def sql_append_where(self, column, q, filter_data):
        filter_data = json.loads(filter_data)
        return q.where(self.get_column_to_filter(column) == filter_data)

class SQLRangeFilter(SQLFilter, RangeFilter):
    def sql_append_where(self, column, q, filter_data):
        f, t = self.parse_filter_data(filter_data)
        if f:
            q = q.where(self.get_column_to_filter(column) > f)
        if t:
            q = q.where(self.get_column_to_filter(column) < t)
        return q
    
class SQLDateRangeFilter(SQLRangeFilter, DateRangeFilter):
    pass

class SQLMultiSelectFilter(SQLFilter, MultiSelectFilter):
    def sql_append_where(self, column, q, filter_data):
        fl = [i for i in filter_data.split(';') if i != '']
        return q.where(self.get_column_to_filter(column).in_(fl))

class SQLLeafMultiSelectTreeFilter(SQLFilter, MultiSelectTreeFilter):
    def sql_append_where(self, column, q, filter_data):
        fl = [i.rpartition("/")[2] for i in filter_data.split(';') if i != '']
        return q.where(self.get_column_to_filter(column).in_(fl))
    

class SQLTableDataSource(TableDataSource):
    def __init__(self, name, columns, 
                 prefilter=None,
                 where=[],
                 **kwargs):
        super(SQLTableDataSource, self).__init__(name, 
                                                 columns,
                                                 prefilter=prefilter,
                                                 where=where,
                                                 **kwargs)
        self.prefilter = prefilter
        self.where = where

    def get_selectable(self):
        if self.selectable_proc:
            return self.selectable_proc()
        else:
            return self.selectable

    def get_sql_columns(self):
        cs = []

        for c in self.columns:
            if hasattr(c, 'get_sql_select_columns'):
                cs += c.get_sql_select_columns() 
        return cs

    def get_select(self):
        return ex.select(self.get_sql_columns())

    def apply_filters(self, q, filter_data):
        for idx, i in enumerate(self.columns):
            if i.filter and filter_data[idx]:
                q = i.filter.sql_append_where(i, q, filter_data[idx])
        return q

    def get_data(self, start, length, search, ordering, column_filters, **args):
        q = self.get_select()
        qc = self.get_select()

        if self.prefilter:
            q = self.prefilter(q, **args)

        for i in self.where:
            q = q.where(i)

        total = db.session.execute(q.alias('for_count').count()).first()[0]

        q = self.apply_filters(q, column_filters)
        
        filtered = db.session.execute(q.alias('for_count').count()).first()[0]

        for i, d in ordering:
            col = self.columns[i].get_sql_select_columns()[0]
            if d == 'desc':
                col = desc(col)
            q =q.order_by(col)

        q = q.limit(length).offset(start)
        return db.session.execute(q), total, filtered

class ModelTableDataSource(TableDataSource):
    def __init__(self, name, columns, 
                 query=None,
                 query_proc=None,
                 **kwargs):
        super(SQLTableDataSource, self).__init__(name, 
                                                 columns,
                                                 prefilter=prefilter,
                                                 where=where,
                                                 **kwargs)
        self.query = self.query
        if query_proc:
            self.query_proc = self.query_proc

    def query_proc(self):
        return self.query

    def apply_filters(self, q, filters):
        for idx, i in enumerate(self.columns):
            if i.filter and filter_data[idx]:
                q = i.filter.model_filter(i, q, filter_data[idx])
        return q

    def get_data(self, start, length, search, ordering, column_filters, **args):
        q = self.query_proc()

        total = q.count()

        q = self.apply_filters(q, column_filters)
        filtersed = q.count()

        return q.all(), total, filtered

class UpdatingFormEndpoint(FormEndpoint):
    def create_form(self, id):
        self.obj = self.model_class.query.get(id)
        form = self.form_class(request.form, self.obj)
        form.populate_obj(self.obj)
        return form

    def confirm_submit(self):
        flash(_("Data saved"), "success")

    def post_populate(self):
        return
        
    def submitted(self, id):
        self.form.populate_obj(self.obj)
        self.post_populate()
        db.session.commit()
        return self.confirm_submit()

class CreatingFormEndpoint(FormEndpoint):
    detail_endpoint = None
    listing_endpoint = None
    
    def create_form(self):
        return self.form_class()

    def confirm_submit(self):
        flash(_("Data saved"), "success")
        if self.detail_endpoint:
            return redirect(url_for(self.detail_endpoint, id=self.obj.id))
        if self.listing_endpoint:
            return redirect(url_for(self.listing_endpoint))

    def post_populate(self):
        return
                
    def submitted(self):
        self.obj = self.model_class()
        self.form.populate_obj(self.obj)
        self.post_populate()
        db.session.add(self.obj)
        db.session.commit()
        return self.confirm_submit()

class DeletingEndpoint(ConfirmationEndpoint):
    methods = ("GET", "POST")
    confirmation_format = lazy_gettext("Really delete {}?")
    flash_format = lazy_gettext("{} was deleted")

    def prepare(self, id):
        self.obj = self.model_class.query.get(id)
        print self.obj
    
    @property
    def confirmation_message(self):
        return self.confirmation_format.format(self.obj)

    @property
    def flash_message(self):
        return self.flash_format.format(self.obj), 'success'
            
    def do_it(self, id):
        db.session.delete(self.obj)
        db.session.commit()
    
    
class ModelTableEndpoint(View):
    columns = ()
    actions = ()
    methods = ('GET',)
    action_column_name = lazy_gettext('Actions')
    primary_key_attr = 'id'
    action_factory=Action
    
    def transform_actions(self, actions):
        return [i if isinstance(i, Action) else self.action_factory(*i)
                for i in actions]
    
    def get_data(self):
        return self.model_class.query.all()

    def build_table(self, **kwargs):
        data = self.get_data(**kwargs)
        if self.actions:
            columns = list(self.columns)
            actions = self.transform_actions(self.actions)
            columns.append(ActionObjectColumn(self.action_column_name,
                                              attr=self.primary_key_attr,
                                              actions=actions))
        else:
            columns = self.columns
        
        t = PlainTable(self.__class__.__name__,
                       columns,
                       data)
        t = self.wrap(t)
        return t

    def wrap(self, t):
        return t
    
    def dispatch_request(self, **kwargs):
        return self.render_template(self.build_table(**kwargs))
