from flask import Flask, Blueprint, Markup, request, current_app
from werkzeug.local import LocalProxy

current_appshell = LocalProxy(lambda: current_app.extensions['appshell'])

