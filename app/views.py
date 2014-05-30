import abc

from app.forms import LoginForm
from app.forms import RegistrationForm
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from flask.ext import login
from flask.ext.admin import helpers
from flask.ext.login import login_required
from flask.ext.login import logout_user

from admin import AdminBuilder


class ViewBase(View, object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def dispatch_request(self, *args, **kwargs):
        raise NotImplementedError

    def render_template(self, template, **kwargs):
        return render_template(template,
                               user=login.current_user,
                               **kwargs)


class IndexView(ViewBase, object):
    def __init__(self, schema):
        super(IndexView, self).__init__()
        self._Project = schema.Project

    def dispatch_request(self):
        return self.render_template('index.html',
                                    title='Homepage',
                                    projects=self._Project.get_all())


class ProjectView(ViewBase, object):
    def __init__(self, schema):
        super(ProjectView, self).__init__()
        self._Project = schema.Project

    def dispatch_request(self, project_name):
        project = self._Project.query.filter_by(name=project_name)
        project = project.first_or_404()
        return self.render_template('project.html',
                                    title="Project %s" % project.name,
                                    project=project)


class TagView(ViewBase, object):
    def __init__(self, schema):
        super(TagView, self).__init__()
        self._Tag = schema.Tag

    def dispatch_request(self, tag_name):
        tag = self._Tag.query.filter_by(name=tag_name).first_or_404()
        return self.render_template('tag.html',
                                    title="Tag %s" % tag.name,
                                    tag=tag)


class TagsView(ViewBase, object):
    def __init__(self, schema):
        super(TagsView, self).__init__()
        self._Tag = schema.Tag

    def dispatch_request(self):
        tags = self._Tag.query.all()
        return render_template('tags.html',
                               title="All tags",
                               tags=tags)


class PatchSeriesView(ViewBase, object):
    def __init__(self, schema):
        super(PatchSeriesView, self).__init__()
        self._Series = schema.Series
        self._Patch = schema.Patch

    def dispatch_request(self, series_id, page_index=1):
        series = self._Series.query.filter_by(id=series_id).first_or_404()
        page = self._Patch.query.filter_by(serie_id=series_id)
        page = page.order_by(self._Patch.date)
        page = page.paginate(page_index, 1)
        patch = page.items[0]

        endpoint = lambda x: self._endpoint(series_id, x)
        return self.render_template('patch.html',
                                    title=patch.name,
                                    patch=page.items[0],
                                    serie=series,
                                    page=page,
                                    endpoint=endpoint)

    def _endpoint(self, series_id, page_index):
        return url_for('series', series_id=series_id, page_index=page_index)


class PatchView(ViewBase, object):
    def __init__(self, schema):
        super(PatchView, self).__init__()
        self._Patch = schema.Patch

    def dispatch_request(self, patch_id, format='html'):
        patch = self._Patch.query.filter_by(id=patch_id).first_or_404()
        series = patch.series

        if format == 'mbox':
            return Response(patch.mbox, mimetype='application/mbox')

        if format == 'patch':
            return Response(patch.content, mimetype='text/x-patch')

        if series is not None and len(series.patches) > 1:
            return self.render_template('patch.html',
                                        title=patch.name,
                                        patch=patch,
                                        series=series)
        else:
            return self.render_template('patch.html',
                                        title=patch.name,
                                        patch=patch)


class LoginView(ViewBase, object):
    methods = ['GET', 'POST']

    def __init__(self, schema):
        super(LoginView, self).__init__()
        self._schema = schema

    def dispatch_request(self):
        form = LoginForm(request.form, schema=self._schema)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            if user:
                login.login_user(user, remember=form.remember_me)
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash('User not found, sorry pal!', 'warning')

        return self.render_template('login.html',
                                    title="Login",
                                    form=form)


class RegisterView(ViewBase, object):
    methods = ['GET', 'POST']

    def __init__(self, schema):
        super(RegisterView, self).__init__()
        self._schema = schema

    def dispatch_request(self):
        form = RegistrationForm(request.form, schema=self._schema)
        if helpers.validate_form_on_submit(form):
            user = self._schema.User()
            form.populate_obj(user)
            user.create()
            self._schema.commit()

            login.login_user(user)
            return redirect(url_for('index'))

        return self.render_template('register.html',
                                    form=form,
                                    title='Registration')


class LogoutView(ViewBase, object):
    @login_required
    def dispatch_request(self):
        logout_user()
        return redirect(url_for('index'))


class ViewBuilder(object):
    def __init__(self, plaid, db_session, schema):
        self._index = IndexView.as_view('index', schema)
        plaid.add_url_rule('/', view_func=self._index)
        plaid.add_url_rule('/index', view_func=self._index)

        self._project = ProjectView.as_view('project', schema)
        plaid.add_url_rule('/project/<project_name>', view_func=self._project)

        self._tag = TagView.as_view('tag', schema)
        plaid.add_url_rule('/tag/<tag_name>', view_func=self._tag)

        self._tags = TagsView.as_view('tags', schema)
        plaid.add_url_rule('/tags', view_func=self._tags)

        self._patch_series = PatchSeriesView.as_view('series', schema)
        plaid.add_url_rule('/series/<int:series_id>',
                           view_func=self._patch_series)
        plaid.add_url_rule('/series/<int:series_id>/<int:page_index>',
                           view_func=self._patch_series)

        self._patch = PatchView.as_view('patch', schema)
        plaid.add_url_rule('/patch/<patch_id>', view_func=self._patch)
        plaid.add_url_rule('/patch/<patch_id>/<format>', view_func=self._patch)

        self._login = LoginView.as_view('login', schema)
        plaid.add_url_rule('/login', view_func=self._login)

        self._register = RegisterView.as_view('register', schema)
        plaid.add_url_rule('/register', view_func=self._register)

        self._logout = LogoutView.as_view('logout')
        plaid.add_url_rule('/logout', view_func=self._logout)

        self._admin_builder = AdminBuilder(plaid, db_session, schema)
