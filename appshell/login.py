from flask.ext.login import LoginManager, current_user
from flask.ext.login import login_user, logout_user, login_fresh
from flask.ext.login import fresh_login_required
from flask import Blueprint, request

from functools import wraps

login_manager = LoginManager()
user_loader = login_manager.user_loader

def register_in_app(app):
    login_manager.init_app(app)
