
from flask import Flask, Blueprint
from appshell import AppShell, Module, single_view, render_template
from appshell.sql import db, SQLColumn, SQLTableDataSource, SQLPrefixFilter, \
    SQLSelectFilter, SQLMultiSelectFilter, SQLDateRangeFilter
from appshell.login import current_user, PasswordAuthenticationModule
from appshell.tables import PlainTable, SequenceTableDataSource, VirtualTable,\
    CustomSelectSequenceColumn, CheckBoxSequenceColumn
from appshell.trees import PlainTreeGrid, TreeGridItem
from appshell.leaflet import Map, Marker
from appshell import table_export 
from flask.ext.login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, orm
import iso8601
import json
import time
from markupsafe import Markup
from wtforms import StringField, PasswordField, SubmitField, SelectField, \
    TextField, TextAreaField, DateTimeField
from wtforms.widgets import TextArea, CheckboxInput, ListWidget, CheckboxInput
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, Required, EqualTo, ValidationError
from flask_wtf import Form
from appshell.forms import BootstrapMarkdown, FormView, VerticalFormView, \
    HorizontalFormView

app = Flask(__name__)

app.config['SECRET_KEY'] = 'foo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

shell = AppShell('AppShell demo', 'simple.hello', app,
                 components={'sql': {}})

simple = Module('simple', __name__, template_folder='templates')
simple.label('Simple module')
@simple.route('/')
@simple.menu('Hello world')
def hello():
    return render_template('hello.html')

@simple.route('/mnau')
@simple.menu('Mnau!')
@simple.local_menu('Mnau')
@simple.access(lambda **kwa: False)
def mnau():
    return render_template('hello.html')
app.register_blueprint(simple)

widgets = Module('widgets', __name__, template_folder='templates')
widgets.label('Widgets')

table_data = [("%d-1" % i, "%d-2" % i, "%d-3" % i) for i in range(100)]

@widgets.route('/widgets/table')
@widgets.menu('Simple table')
def simple_table():
    t = PlainTable("simple_table",
                   ("Column 1", "Column 2", "Column 3"),table_data)
    return single_view(t,
                       layout='fluid')

tree_data = [TreeGridItem(("foo", "Foo"), 
                          [TreeGridItem(("foo/bar", "Foobar"), [
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), []),
                          ]),
                        
                           TreeGridItem(("foo/baz", "Foobaz"), [])]),
             TreeGridItem(("spam", "Spam"), [])]

@widgets.route('/widgets/tree')
@widgets.menu('Treegrid')
def treegrid():
    t = PlainTreeGrid("treeegrid",
                      ("Name", "Description"), tree_data,
                      search=True)
    return single_view(t)

vt = SequenceTableDataSource("virtual_table",
                     ("Name", "Description"))
vt.register_view(widgets)
@vt.data_source
def virtual_data_source(start, length, search, ordering, column_filters):
    total = 1000
    filtered = 1000
    ds = [[i, i] 
          for i in xrange(total)]
    time.sleep(0.3)
    return ds[start:start+length], total, filtered


@widgets.route('/widgets/virtual')
@widgets.menu('Virtual table')
def virtual():
    return single_view(VirtualTable(vt, filters='bottom', 
                                    options={"scrollY": -200,
                                             "ordering": True,
                                             "autoWidth": False}),
                       layout='fluid')

@widgets.route('/widgets/dropdowns')
@widgets.menu('Dropdowns')
def dropdowns():
    t = PlainTable("simple_table",
                   ("Column 1", "Column 2", "Column 3"),table_data, 
                   options={"scrollY": 400, "pagingType": "simple"},
                   attrs={"style": "width: 680px"})
    tm = PlainTable("msimple_table",
                    ("Column 1", "Column 2", "Column 3"),table_data, 
                    options={"scrollY": 400, "pagingType": "simple"},
                    attrs={"style": "width: 680px"})
    tg = PlainTreeGrid("treeegrid",
                       ("Name", "Description", CustomSelectSequenceColumn("",
                                                                          index=0)), 
                       tree_data)
    tgm = PlainTreeGrid("mtreeegrid",
                      ("Name", "Description", CustomSelectSequenceColumn("",
                                                                          index=0)), tree_data)
    tgc = PlainTreeGrid("ctreeegrid",
                      (CheckBoxSequenceColumn("Name", index=0),
                       "Description"), tree_data)
    tgmc = PlainTreeGrid("mctreeegrid",
                      (CheckBoxSequenceColumn("Name", index=0),
                       "Description"), tree_data)


    return render_template('dropdowns.html', table=t, tree=tg, m_tree=tgm, ctree=tgc, mctree=tgmc)

@widgets.route('/widgets/components')
@widgets.menu('Components')
def components():
    return render_template('components.html')



app.register_blueprint(widgets)


auth = PasswordAuthenticationModule('auth', __name__, template_folder='templates')

class User(UserMixin):
    def get_name(self):
        return "Test user"
    def get_id(self):
        return "test"
    
    @classmethod
    def load_user(cls, user_id):
        if user_id == "test":
            return cls()
        else:
            return None

    @classmethod
    def authenticate(cls, login, password):
        print login, password
        if login == "test" and password == "test":
            return cls()
        else:
            return None


auth.userclass = User
app.register_blueprint(auth)

class DemoEntity(db.Model):
    __tablename__ = 'demo'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    created = Column(DateTime)
    company = Column(String)
    address = Column(String)
    city = Column(String)
    gps = Column(String)
    iban = Column(String)


data = Module('data', __name__, template_folder='templates')
data.label('Data')
dds = SQLTableDataSource(name="sql_table",
                         columns=[SQLColumn("Name", 
                                            DemoEntity.__table__.c.name,
                                            filter=SQLPrefixFilter()),
                                  SQLColumn("Email",
                                            DemoEntity.__table__.c.email,
                                            filter=SQLPrefixFilter()),
                                  SQLColumn("Created",
                                            DemoEntity.__table__.c.created,
                                            filter=SQLDateRangeFilter(default_last=7))],
                         selectable=DemoEntity.__table__)
dds.register_view(data)

dds.register_action("mnua", "Mnau", lambda x:"mnau!")
table_export.all(dds)

@data.route('/data/sql-query')
@data.menu('Arbitrary SQL')
def sql_query():
    return single_view(VirtualTable(dds, filters='bottom', 
                                    options={"scrollY": -220,
                                             "ordering": True,
                                             "autoWidth": False},
                                    ),
                       layout='fluid')


app.register_blueprint(data)

class M:
    def __init__(self, lat,lng):
        self.lat = lat
        self.lng = lng

maps = Module('maps', __name__, template_folder='templates')
maps.label('Maps')
@maps.route('/maps/simple')
@maps.menu('Simple map')
def simple_map():
    m = Map()
    m.add(Marker([50,13]), fit=True)
    m.add(Marker([50,14]), fit=True)
    return m.render()

app.register_blueprint(maps)


forms = Module('forms', __name__, template_folder='templates')
forms.label('Forms')

class ArticleForm(Form):
    title = TextField('Title')
    slug = TextField('Slug')
    summary = TextAreaField('Summary',
                            widget=BootstrapMarkdown(rows=5))
    content = TextAreaField('Content',
                            widget=BootstrapMarkdown(rows=15))
    published = DateTimeField('Published since')


def define_form_view(i):
    fv = i()
    @forms.route('/forms/'+i.__name__,
                 endpoint=i.__name__)
    def form_view():
        f = ArticleForm()
        return single_view(fv(f))
    form_view.__name__ = i.__name__ # XXX
    forms.menu(i.__name__)(i) # XXX

for i in FormView, VerticalFormView, HorizontalFormView:
    define_form_view(i)

app.register_blueprint(forms)

@app.before_first_request
def init_db():
    db.create_all()
    dd = json.load(open("demo_data.json", "r"))
    s = db.session()
    for i in dd:
        o = DemoEntity()
        for k, v in i.iteritems():
            if k in ("created",):
                v = iso8601.parse_date(v)
            setattr(o, k, v)
        s.add(o)
    s.commit()

if __name__ == '__main__':
    app.debug = True
    app.run(port=5050, host="0.0.0.0")
