from flask.ext.wtf import FlaskForm
from appshell.forms import OrderedForm
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms_alchemy import model_form_factory
from appshell.tables import TableDataSource, SequenceTableDataSource, \
    SelectFilter, MultiSelectFilter, Column, TextFilter, ActionColumnMixin,\
    RangeFilter, DateRangeFilter, MultiSelectTreeFilter, PlainTable, \
    ObjectColumn, Action, ActionObjectColumn, Filter
from sqlalchemy.sql import expression as ex
from sqlalchemy import desc, func
import json
from appshell.forms import FormEndpoint
from flask.ext.babelex import Babel, Domain
from appshell import View, url_for
from flask import flash, request, redirect
from appshell.endpoints import ConfirmationEndpoint
from appshell.markup import Toolbar

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

class SQLAlchemyColumn(Column):
    def __init__(self, name, expression, **kwargs):
        super(SQLAlchemyColumn, self).__init__(name, 
                                        expression=expression, 
                                        **kwargs)
        self.expression = expression
        self.id = str(expression).replace('.', '__')
        
    def get_sql_select_columns(self):
        return [self.expression]

    def get_cell_data(self, row):
        return row[self.expression]


class SQLColumn(SQLAlchemyColumn):
    def sql_append_where(self, q):
        return q
    
class SQLActionColumn(ActionColumnMixin, SQLColumn):
    pass

class SQLFKColumn(SQLColumn):
    def __init__(self, name, expression, fk, pk, **kwargs):
        super(SQLFKColumn, self).__init__(name, expression=expression, **kwargs)
        self.fk = fk.label(str(fk))
        self.pk = pk.label(str(fk))

    def sql_append_where(self, q):
        return q.where(self.fk == self.pk)

class SQLAlchemyFilter(Filter):
    def __init__(self, filter_expr=None,
                 **kwargs):
        super(SQLAlchemyFilter, self).__init__(filter_expr=filter_expr,
                                               **kwargs)
        self.filter_expr = filter_expr

    def get_filter_clause(self, column, filter_data):
        raise NotImplemented
        
class SQLFilter(SQLAlchemyFilter):
    def get_column_to_filter(self, column):
        if self.filter_expr is not None:
            return self.filter_expr
        else:
            return column.get_sql_select_columns()[0]

    def sql_append_where(self, column, q, filter_data):
        return q.where(self.get_filter_clause(column, filter_data))
    
class PrefixFilter(TextFilter):
    #def sql_append_where(self, column, q, filter_data):
    #    return q.where(self.get_column_to_filter(column).like(filter_data+'%'))

    def get_filter_clause(self, column, filter_data):
        return self.get_column_to_filter(column).like(filter_data+'%')

class SQLPrefixFilter(PrefixFilter, SQLFilter):
    pass
    
class CasefoldingPrefixFilter(TextFilter):
    def get_filter_clause(self, column, filter_data):
        col = self.get_column_to_filter(column)
        return func.lower(col).like(filter_data.lower()+'%')

class SQLCasefoldingPrefixFilter(CasefoldingPrefixFilter, SQLFilter):
    pass
    
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
                 fake_count=False,
                 select_from=None,
                 **kwargs):
        super(SQLTableDataSource, self).__init__(name, 
                                                 columns,
                                                 prefilter=prefilter,
                                                 where=where,
                                                 **kwargs)
        self.prefilter = prefilter
        self.where = where
        self.fake_count = fake_count
        self.select_from = select_from
        
    def get_sql_columns(self):
        cs = []

        for c in self.columns:
            if hasattr(c, 'get_sql_select_columns'):
                cs += c.get_sql_select_columns() 
        return cs

    def get_select(self):
        q = ex.select(self.get_sql_columns(), use_labels=True)
        if self.select_from is not None:
            q = q.select_from(self.select_from)
        for i in self.columns:
            q = i.sql_append_where(q)
        return q

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

        if not self.fake_count:
            total = db.session.execute(q.alias('for_count').count()).first()[0]

        q = self.apply_filters(q, column_filters)
        
        filtered = db.session.execute(q.alias('for_count').count()).first()[0]
        if self.fake_count:
            total = filtered

        for i, d in ordering:
            col = self.columns[i].get_sql_select_columns()[0]
            if d == 'desc':
                col = desc(col)
            q =q.order_by(col)

        if length is not None:
            q = q.limit(length).offset(start)
            
        return db.session.execute(q), total, filtered

class ModelTableDataSource(TableDataSource):
    def __init__(self, name, columns, 
                 query=None,
                 query_proc=None,
                 **kwargs):
        super(ModelTableDataSource, self).__init__(name, 
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

        #total = q.count()

        q = self.apply_filters(q, column_filters)
        filtered = q.count()
        total = filtered
        
        return q.all(), total, filtered
    
class UpdatingFormEndpoint(FormEndpoint):
    detail_endpoint = None
    listing_endpoint = None
    listing_endpoint_args = {}

    def create_form(self, id):
        self.obj = db.session.query(self.model_class).get(id)
        form = self.form_class(obj=self.obj)
        form.populate_obj(self.obj)
        return form

    def confirm_submit(self):
        flash(_("Data saved"), "success")
        return self.do_redirect()

    def do_redirect(self):
        if self.detail_endpoint:
            return redirect(url_for(self.detail_endpoint, id=self.obj.id))
        if self.listing_endpoint:
            return redirect(url_for(self.listing_endpoint,
                                    **self.listing_endpoint_args))
        
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
    listing_endpoint_args = {}
    
    def create_form(self, **kwargs):
        return self.form_class()

    def confirm_submit(self, **kwargs):
        flash(_("Data saved"), "success")
        return self.do_redirect()

    def do_redirect(self):
        if self.detail_endpoint:
            return redirect(url_for(self.detail_endpoint, id=self.obj.id))
        if self.listing_endpoint:
            return redirect(url_for(self.listing_endpoint,
                                    **self.listing_endpoint_args))

        
    def post_populate(self):
        return
                
    def submitted(self, **kwargs):
        self.obj = self.model_class()
        self.form.populate_obj(self.obj)
        self.post_populate(**kwargs)
        db.session.add(self.obj)
        db.session.commit()
        return self.confirm_submit(**kwargs)

class DeletingEndpoint(ConfirmationEndpoint):
    methods = ("GET", "POST")
    confirmation_format = lazy_gettext("Really delete {}?")
    flash_format = lazy_gettext("{} was deleted")
    listing_endpoint = None
    listing_endpoint_args = {}

    def prepare(self, id):
        self.obj = db.session.query(self.model_class).get(id)
        if self.listing_endpoint:
            self.redirect_to = url_for(self.listing_endpoint,
                                       **self.listing_endpoint_args)
        
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
    table_args = {}
    
    def transform_actions(self, actions):
        return [i if isinstance(i, Action) else self.action_factory(*i)
                for i in actions]
    
    def get_data(self):
        return self.model_class.query.all()

    def build_table(self, **kwargs):
        data = self.get_data(**kwargs)
        if self.actions:
            columns = list(self.columns)
            print(repr(self.columns))
            actions = self.transform_actions(self.actions)
            columns.append(ActionObjectColumn(self.action_column_name,
                                              attr=self.primary_key_attr,
                                              actions=actions))
        else:
            columns = self.columns

        print(repr(columns))
            
        t = PlainTable(self.__class__.__name__,
                       columns,
                       data,
                       **self.table_args)
        t = self.wrap(t)
        return t

    def wrap(self, t):
        return t
    
    def dispatch_request(self, **kwargs):
        return self.render_template(self.build_table(**kwargs))

class ModelCRUDEditor:
    columns = []
    actions = []

    toolbar = None

    table_base = ModelTableEndpoint
    
    delete_base = DeletingEndpoint
    delete_text = lazy_gettext('Delete')
    
    edit_base = UpdatingFormEndpoint
    edit_text = lazy_gettext('Edit')
    
    create_base = CreatingFormEndpoint
    create_text = lazy_gettext('Create...')

    form_class = None
    create_form_class = None
    model_class = None
    
    decorators = []
    table_decorators = []
    create_decorators = []
    delete_decorators = []
    edit_decorators = []
    
    def __init__(self, basename):
        self.basename = basename

        if self.create_form_class is None:
            self.create_form_class = self.form_class
        
        if self.edit_base:
            self.actions = self.actions\
                           + [self.table_base.action_factory(self.edit_text,
                                                             "."+self.edit_endpoint)]

        if self.delete_base:
            self.actions = self.actions\
                           + [self.table_base.action_factory(self.delete_text,
                                                             "."+self.delete_endpoint)]
            
        if self.create_base:
            if self.toolbar is None:
                self.toolbar = Toolbar()
            self.toolbar.add_button(self.create_text,
                                    "."+self.create_endpoint,
                                    context_class="success")
            
    @property
    def table_endpoint(self):
        return self.basename + "_table"
    @property
    def create_endpoint(self):
        return self.basename + "_create"
    @property
    def edit_endpoint(self):
        return self.basename + "_edit"
    @property
    def delete_endpoint(self):
        return self.basename + "_delete"
            
    def make_table_endpoint(self):
        ta = dict(self.table_base.table_args)
        ta["toolbar"] = self.toolbar
        class XModelTableEndpoint(self.table_base):
            table_args = ta
            columns = self.columns
            actions = self.actions
            model_class = self.model_class
        return XModelTableEndpoint

    def make_create_endpoint(self):
        class XCreatingFormEndpoint(self.create_base):
            form_class = self.create_form_class
            model_class = self.model_class
            listing_endpoint = "." + self.table_endpoint
        return XCreatingFormEndpoint

    def make_edit_endpoint(self):
        class XUpdatingFormEndpoint(self.edit_base):
            form_class = self.form_class
            model_class = self.model_class
            listing_endpoint = "." + self.table_endpoint
        return XUpdatingFormEndpoint

    def make_delete_endpoint(self):
        class XDeletingEndpoint(self.delete_base):
            model_class = self.model_class
            listing_endpoint = "." + self.table_endpoint
        return XDeletingEndpoint

    def register_route(self, bp, route, decorators=[], **kwargs):
        t = self.make_table_endpoint()
        t.route(bp,
                route,
                name=self.table_endpoint,
                decorators=(decorators
                            + self.decorators
                            + self.table_decorators),
                **kwargs)

        if self.create_base:
            c = self.make_create_endpoint()
            c.route(bp,
                    route + 'create',
                    decorators=(decorators
                                + [bp.subendpoint('.'+self.table_endpoint)]
                                + self.decorators
                                + self.create_decorators),
                    name=self.create_endpoint,
                    **kwargs)

        if self.edit_base:
            c = self.make_edit_endpoint()
            c.route(bp,
                    route + '<id>/edit',
                    name=self.edit_endpoint,
                    decorators=(decorators
                                + [bp.subendpoint('.'+self.table_endpoint)]
                                + self.decorators
                                + self.edit_decorators),
                    **kwargs)

        if self.delete_base:
            c = self.make_delete_endpoint()
            c.route(bp,
                    route + '<id>/delete',
                    name=self.delete_endpoint,
                    decorators=(decorators
                                + [bp.subendpoint('.'+self.table_endpoint)]
                                + self.decorators
                                + self.delete_decorators),
                    **kwargs)
    
    @classmethod
    def route(cls, bp, route, name=None, decorators=[], **kwargs):
        if name is None:
            name = cls.__name__

        i = cls(name)
        i.register_route(bp, route, decorators, **kwargs)
