from app import app, db, login_manager
from app.forms import LoginForm
from app.forms import RegistrationForm
from app.models import Patch
from app.models import Project
from app.models import Serie
from app.models import Tag
from app.models import User
from flask import Response
from flask import url_for, redirect, render_template, request, flash

from flask.ext import admin, login
from flask.ext.admin import helpers
from flask.ext.admin.base import expose
from flask.ext.admin.contrib import sqla

from jinja2 import Markup


class Accessible(object):
    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized model view class
class ModelView(Accessible, sqla.ModelView):
    pass


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

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(PatchesView, self).__init__(Patch, session, **kwargs)


# Create customized index view class
class AdminIndexView(Accessible, admin.AdminIndexView):
    pass


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title="Homepage",
                           user=login.current_user,
                           projects=Project.get_all())


@app.route('/project/<project_name>')
def project(project_name):
    project = Project.query.filter_by(name=project_name).first_or_404()
    return render_template('project.html',
                           title="Project %s" % project.name,
                           user=login.current_user,
                           project=project)


@app.route('/tag/<tag_name>')
def tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    return render_template('tag.html',
                           title="Tag %s" % tag.name,
                           user=login.current_user,
                           tag=tag)


@app.route('/tags')
def tags():
    tags = Tag.query.all()
    return render_template('tags.html',
                           title="All tags",
                           user=login.current_user,
                           tags=tags)


@app.route('/serie/<int:serie_id>')
@app.route('/serie/<int:serie_id>/<int:patch_index>')
def serie(serie_id, patch_index=1):
    serie = Serie.query.filter_by(id=serie_id).first_or_404()

    page = Patch.query.filter_by(serie_id=serie_id).order_by(Patch.date)

    page = page.paginate(patch_index, 1)

    patch = page.items[0]

    def endpoint(page_index):
        return url_for('serie', serie_id=serie_id, patch_index=page_index)

    return render_template('patch.html',
                           title=patch.name,
                           user=login.current_user,
                           patch=page.items[0],
                           serie=serie,
                           page=page,
                           endpoint=endpoint)


@app.route('/patch/<patch_id>')
@app.route('/patch/<patch_id>/<format>')
def patch(patch_id, format='html'):
    patch = Patch.query.filter_by(id=patch_id).first_or_404()
    serie = patch.serie

    if format == 'mbox':
        return Response(patch.mbox, mimetype='application/mbox')

    if format == 'patch':
        return Response(patch.content, mimetype='text/x-patch')

    if serie and len(serie.patches) > 1:
        return render_template('patch.html',
                               title=patch.name,
                               user=login.current_user,
                               patch=patch,
                               serie=serie)
    else:
        return render_template('patch.html',
                               title=patch.name,
                               user=login.current_user,
                               patch=patch)


@app.route('/login', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = form.get_user()
        if user:
            login.login_user(user, remember=form.remember_me)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash('User not found, sorry pal!', 'warning')

    return render_template('login.html',
                           title="Login",
                           user=login.current_user,
                           form=form)


@app.route('/register', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html', form=form, user=login.current_user,
                           title='Registration')


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(userid):
    return User.get_by_id(userid)


crud = admin.Admin(app, 'CRUD', endpoint="crud", url="/",
                   base_template='base.html')
crud.add_view(PatchesView(db.session, endpoint="patches"))

admin = admin.Admin(app, 'Auth', index_view=AdminIndexView(), endpoint="admin")
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Patch, db.session))
