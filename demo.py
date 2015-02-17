from flask import Flask, Blueprint, render_template
from appshell import AppShell, Module, single_view
from appshell.sql import db
from appshell.login import user_loader
from appshell.tables import PlainTable, SequenceTableDataSource, VirtualTable
from appshell.trees import PlainTreeGrid, TreeGridItem
from flask.ext.login import UserMixin

app = Flask(__name__)

app.config['SECRET_KEY'] = 'foo'

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
    return single_view(VirtualTable(vt))




app.register_blueprint(widgets)



@user_loader
class User(UserMixin):
    def __init__(self, userid):
        self.id = userid



if __name__ == '__main__':
    app.debug = True
    app.run()
