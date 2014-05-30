from flask.ext import admin
from flask.ext import login
from flask.ext.admin.base import expose
from flask.ext.admin.contrib import sqla

from jinja2 import Markup


class Accessible(object):
    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized model view class
class ModelView(Accessible, sqla.ModelView):
    pass


def _create_patches_view(Patch):
    class PatchesView(ModelView):
        def _render_submitter(v, c, m, submitter):
            return Markup('<a href="mailto:%s">%s</a>' %
                          (m.submitter.email, m.submitter.name))

        # Disable model creation
        can_create = False

        # Override displayed fields
        column_list = ('submitter', 'name')
        column_formatters = dict(submitter=_render_submitter)
        column_sortable_list = (('submitter', 'submitter.name'),
                                ('name', Patch.name))

        @expose('/')
        def index_view(self):
            self._template_args['user'] = login.current_user
            self._template_args['title'] = "Patches"
            return super(PatchesView, self).index_view()

        def __init__(self, db_session, **kwargs):
            # You can pass name and other parameters if you want to
            super(PatchesView, self).__init__(Patch, db_session, **kwargs)

    return PatchesView


# Create customized index view class
class AdminIndexView(Accessible, admin.AdminIndexView):
    pass


class AdminBuilder(object):
    def __init__(self, plaid, db_session, schema):
        self._crud = admin.Admin(plaid, 'CRUD', endpoint="crud", url="/",
                                 base_template='base.html')
        PatchesView = _create_patches_view(schema.Patch)
        self._crud.add_view(PatchesView(db_session, endpoint="patches"))

        self._admin = admin.Admin(plaid, 'Auth', index_view=AdminIndexView(),
                                  endpoint="admin")
        self._admin.add_view(ModelView(schema.User, db_session))
        self._admin.add_view(ModelView(schema.Project, db_session))
        self._admin.add_view(ModelView(schema.Patch, db_session))
