from flask import Flask, Blueprint
from appshell import AppShell, Module, single_view, render_template
from appshell.sql import db
from appshell.login import user_loader
from appshell.tables import PlainTable, SequenceTableDataSource, VirtualTable
from appshell.trees import PlainTreeGrid, TreeGridItem
from flask.ext.login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
import iso8601
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'foo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

shell = AppShell('AppShell demo', 'simple.hello', app,
                 components=['.sql', '.login'])

simple = Module('simple', __name__, template_folder='templates')
simple.label('Simple module')
@simple.route('/')
@simple.menu('Hello world')
def hello():
    return render_template('hello.html')

@simple.route('/mnau')
@simple.menu('Mnau!')
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
    return single_view(t)

tree_data = [TreeGridItem(("foo", "Foo"), 
                          [TreeGridItem(("foo/bar", "Foobar"), [
                              TreeGridItem(("foo/bar/quux", "Foobarquux"), [])]),
                           TreeGridItem(("foo/baz", "Foobaz"), [])]),
             TreeGridItem(("spam", "Spam"), [])]

@widgets.route('/widgets/tree')
@widgets.menu('Treegrid')
def treegrid():
    t = PlainTreeGrid("treeegrid",
                      ("Name", "Description"), tree_data)
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
    return ds[start:start+length], total, filtered


@widgets.route('/widgets/virtual')
@widgets.menu('Virtual table')
def virtual():
    return single_view(VirtualTable(vt, filters='bottom', 
                                    options={"scrollY": -200,
                                             "ordering": True,
                                             "autoWidth": False}))

@widgets.route('/widgets/dropdowns')
@widgets.menu('Dropdowns')
def dropdowns():
    t = PlainTable("simple_table",
                   ("Column 1", "Column 2", "Column 3"),table_data, 
                   options={"scrollY": 400, "pagingType": "simple"},
                   attrs={"style": "width: 680px"})
    tg = PlainTreeGrid("treeegrid",
                      ("Name", "Description"), tree_data)
    return render_template('dropdowns.html', table=t, tree=tg)

@widgets.route('/widgets/components')
@widgets.menu('Components')
def components():
    return render_template('components.html')



app.register_blueprint(widgets)



@user_loader
class User(UserMixin):
    def __init__(self, userid):
        self.id = userid


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
