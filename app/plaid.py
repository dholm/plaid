from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy

from models import ModelBuilder
from render import RenderBuilder
from views import ViewBuilder


class Plaid(Flask, object):
    def __init__(self, name):
        super(Plaid, self).__init__(name)
        self.config.from_object('config')


class PlaidBuilder(object):
    def _build_schema(self, db, plaid):
        model_builder = ModelBuilder(db)
        return model_builder.schema

    def _build_login_manager(self, plaid, schema):
        login_manager = LoginManager()
        login_manager.init_app(plaid)

        @login_manager.user_loader
        def load_user(userid):
            return schema.User.get_by_id(userid)

        return login_manager

    def __init__(self, debug):
        plaid = Plaid(__name__)
        db = SQLAlchemy(plaid)
        schema = self._build_schema(db, plaid)
        self._login_manager = self._build_login_manager(plaid, schema)
        self._render_builder = RenderBuilder(plaid)
        self._view_builder = ViewBuilder(plaid, db.session, schema)

        plaid.run(debug=debug)
