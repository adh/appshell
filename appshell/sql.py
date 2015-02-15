from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms_alchemy import model_form_factory

db = SQLAlchemy()

BaseModelForm = model_form_factory(Form)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

def register_in_app(app):
    db.init_app(app)
