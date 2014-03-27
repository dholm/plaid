from app import db
from datetime import date, datetime
from sqlalchemy.orm import backref

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id       = db.Column(db.Integer, primary_key = True)
    name     = db.Column(db.String(128), index = True)
    email    = db.Column(db.String(120), index = True, unique = True)
    role     = db.Column(db.SmallInteger, default = ROLE_USER)
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return "<" + self.email + ">"

    def __repr__(self):
        return '<User %r>' % (self.email)

    def get_name(self):
        return self.name

    @staticmethod
    def get_by_id(userid):
        return db.session.query(User).filter_by(id=userid).first()

class Submitter(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), index = True)
    email = db.Column(db.String(120), index = True, unique = True)

    # Required for administrative interface
    def __unicode__(self):
        if not self.name:
            return  "<" + self.email + ">"
        return self.name + "<" + self.email + ">"

    def __init__(self, name, email):
        self.name  = name
        self.email = email

    @classmethod
    def get_or_create(self, name, email):
        instance = self.query.filter_by(email=email).first()
        if not instance:
            instance = Submitter(name=name, email=email)
            db.session.add(instance)
            db.session.commit()
        return instance


class Project(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    linkname = db.Column(db.String(128))
    name = db.Column(db.String(128))
    listid = db.Column(db.String(128),unique=True)
    listemail = db.Column(db.String(128))
    web_url = db.Column(db.String(128))
    scm_url = db.Column(db.String(128))
    webscm_url = db.Column(db.String(128))
    notifications = db.Column(db.Boolean())

    def __unicode__(self):
        return self.name

    @staticmethod
    def get_all():
        return Project.query.all()

class EmailMixin(object):
    msgid   = db.Column(db.String(255))
    name    = db.Column(db.String(255))
    date    = db.Column(db.DateTime(), default=datetime.now)
    headers = db.Column(db.Text)
    content = db.Column(db.Text)

    def __unicode__(self):
        return self.name

class Patch(EmailMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref='patches')
    pull_url = db.Column(db.String(255))
    commit_ref = db.Column(db.String(255), default=None)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', backref=backref('patches', lazy='dynamic'))
    ancestor_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    ancestor = db.relationship('Patch', backref="successor", remote_side=[id])
    serie_id = db.Column(db.Integer, db.ForeignKey('serie.id'))
    serie = db.relationship('Serie', backref='patches', order_by='Patch.date')
    state = db.Column(db.Integer, default=0)

    def filename(self):
        fname_re = re.compile('[^-_A-Za-z0-9\.]+')
        str = fname_re.sub('-', self.name)
        return str.strip('-') + '.patch'

    @property
    def mbox(self):
        from email.mime.nonmultipart import MIMENonMultipart
        from email.encoders import encode_7or8bit
        from email.parser import HeaderParser
        from email.header import Header

        body = ''
        if self.comments[0].msgid == self.msgid:
            body += self.comments[0].content + '\n'
        body += self.content

        mbox = MIMENonMultipart('text', 'plain', charset='utf-8')

        mbox['Subject'] = self.name
        mbox['From'] = '%s <%s>' % (self.submitter.name, self.submitter.email)
        mbox['Message-Id'] = self.msgid

        mbox.set_payload(body.encode('utf-8'))
        encode_7or8bit(mbox)

        return mbox.as_string()

    def __init__(self, name, pull_url, content, date, headers, tags):
        self.name = name
        self.pull_url = pull_url
        self.content = content
        self.date = date
        self.headers = headers
        self.tags = tags

class Comment(EmailMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref='comments')
    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = db.relationship('Patch', backref='comments', order_by='Comment.date')

'''
class PatchSerie(db.Model):
    serie_id = db.Column(db.Integer, db.ForeignKey('serie.id'))
    serie = relationship('Serie')
    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = relationship('Patch', backref=backref("patch_serie"))
    serial = db.Column(db.Integer)
)
'''

class Serie(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    uid  = db.Column(db.String(255), unique=True, nullable=True)
    date = db.Column(db.DateTime(), default=datetime.now)

    @classmethod
    def get_or_create(self, uid, name=None):
        instance = self.query.filter_by(uid=uid).first()
        if not instance:
            if not name:
                name = "git-send-email-" + uid
            instance = Serie(name=name, uid=uid)
            db.session.add(instance)
            db.session.commit()
        return instance

##    def next(self):

topics = db.Table('topics',
    db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
    db.Column('topic.id', db.Integer, db.ForeignKey('topic.id')),
)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=topics, backref="topics")


tags = db.Table('tags',
    db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
    db.Column('tag.id', db.Integer, db.ForeignKey('tag.id')),
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=tags, backref="tags")

    @classmethod
    def get_or_create(self, name):
        instance = self.query.filter_by(name=name).first()
        if not instance:
            instance = Tag(name=name)
            db.session.add(instance)
            db.session.commit()
        return instance

