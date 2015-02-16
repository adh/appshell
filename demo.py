from flask import Flask, Blueprint, render_template
from appshell import AppShell, Module, single_view
from appshell.sql import db
from appshell.login import user_loader
from appshell.tables import StaticTable
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

tables = Module('tables', __name__, template_folder='templates')
tables.label('Data tables')
@tables.route('/tables/simple')
@tables.menu('Simple table')
def simple_table():
    t = StaticTable("simple_table",
                    ("Column 1", "Column 2", "Column 3"),
                    [("%d-1" % i, "%d-2" % i, "%d-3" % i) for i in range(100)])
    return single_view(t)

@tables.route('/tables/dropdown')
@tables.menu('Table in dropdown')
def dropdown_table():
    return render_template('dropdown_table.html')



app.register_blueprint(tables)



@user_loader
class User(UserMixin):
    def __init__(self, userid):
        self.id = userid



if __name__ == '__main__':
    app.debug = True
    app.run()
