from flask import Flask, Blueprint, render_template
from appshell import AppShell, Module
from appshell.sql import db
from appshell.login import user_loader
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

@user_loader
class User(UserMixin):
    def __init__(self, userid):
        self.id = userid



if __name__ == '__main__':
    app.debug = True
    app.run()
