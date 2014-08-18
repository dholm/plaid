import sys
import traceback

from email import message_from_file

from flask.ext.script import Manager, Command, Option
from flask.ext.script.commands import InvalidCommand
from flask.ext.migrate import Migrate, MigrateCommand

from app import app
from app import db
from app.models import Role
from app.models import User

from mailparse import Project
from mailparse import import_mail
from mailparse import import_mailbox


class CreateProject(Command):
    description = 'This command allows you to create a project'
    option_list = (
        Option('--name', '-n', required=True, dest='name', type=unicode,
               help="Set the project name to NAME."),
        Option('--listid', '-i', required=True, dest='listid', type=unicode,
               help="Set the project listid to LISTID."),
        Option('--linkname', '-l', required=True, dest="linkname",
               type=unicode,
               help="Set the project linkname to LINKNAME."),
        Option('--description', '-d', required=True, dest='description',
               type=unicode,
               help="Set the project description to DESCRIPTION."),
    )

    def run(self, name, listid, linkname, description):
        p = Project(name=name, listid=listid, linkname=linkname,
                    description=description)
        db.session.add(p)
        db.session.commit()


class CreateUser(Command):
    description = 'This command allows you to create a user account'
    option_list = (
        Option('--name', '-n', required=False, dest='name', type=unicode,
               help="Set the user name to NAME."),
        Option('--email', '-e', required=True, dest='email', type=unicode,
               help="Set the user's email address to EMAIL."),
        Option('--password', '-p', required=True, dest="password",
               type=unicode,
               help="Set the user's password to PASSWORD."),
        Option('--role', '-r', required=False, dest="role", default="user",
               type=unicode,
               help="Role (admin, maintainer)")
    )

    def run(self, name, email, password, role):
        u = User(name=name,
                 password=password,
                 email=email)
        try:
            u.role = getattr(Role, role)
        except:
            raise InvalidCommand("The role %s is not supported." % (role))

        print('Creating user %s' % u)
        db.session.add(u)
        db.session.commit()


class ImportMails(Command):
    """Import projects data from a mailing list or a mailbox"""

    option_list = (
        Option('--mailbox', '-m', dest='mailbox'),
    )

    def import_mail_from_stdin(self):
        mail = message_from_file(sys.stdin)
        import_mail(mail)

    def run(self, mailbox):
        if mailbox:
            try:
                import_mailbox(mailbox)
            except Exception as e:
                traceback.print_exc(e)
        else:
            self.import_mail_from_stdin()

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('user', CreateUser())
manager.add_command('project', CreateProject())
manager.add_command('import', ImportMails())

if __name__ == '__main__':
    manager.run()
