import sys
import traceback

from flask.ext.migrate import Migrate
from flask.ext.migrate import MigrateCommand
from flask.ext.script import Command
from flask.ext.script import Manager
from flask.ext.script import Option
from flask.ext.sqlalchemy import SQLAlchemy

from app.plaid import Plaid
from app.models import ModelBuilder

from mailparse import MailImporter


def _create_create_project(schema):
    class CreateProject(Command):
        description = 'This command allows you to create a project'
        option_list = (
            Option('--name', '-n', required=True, dest='name',
                   type=unicode,
                   help="Set the project name to NAME."),
            Option('--listid', '-i', required=True, dest='listid',
                   type=unicode,
                   help="Set the project listid to LISTID."),
            Option('--linkname', '-l', required=True, dest="linkname",
                   type=unicode,
                   help="Set the project linkname to LINKNAME."),
        )

        def run(self, name, listid, linkname):
            p = schema.Project(name=name, listid=listid, linkname=linkname)
            p.create()
            schema.commit()

    return CreateProject


def _create_create_user(schema):
    class CreateUser(Command):
        description = 'This command allows you to create a user account'
        option_list = (
            Option('--name', '-n', required=False, dest='name',
                   type=unicode,
                   help="Set the user name to NAME."),
            Option('--email', '-e', required=True, dest='email',
                   type=unicode,
                   help="Set the user's email address to EMAIL."),
            Option('--password', '-p', required=True, dest="password",
                   type=unicode,
                   help="Set the user's password to PASSWORD."),
            Option('--role', '-r', required=False, dest="role", default="0",
                   type=unicode,
                   help="Role (0 or 1)")
        )

        def run(self, name, email, password, role):
            if role != "0" and role != "1":
                raise Exception('Role should be 0 or 1')
            u = schema.User(name=name,
                            password=password,
                            email=email,
                            role=int(role))
            print('Creating user %s' % u)
            u.create()
            schema.commit()

    return CreateUser


def _create_import_mails(mail_importer):
    class ImportMails(Command):
        """Import projects data from a mailing list or a mailbox"""

        option_list = (
            Option('--mailbox', '-m', dest='mailbox'),
        )

        def import_mail_from_stdin(self):
            mail = message_from_file(sys.stdin)
            mail_importer.import_mail(mail)

        def run(self, mailbox):
            if mailbox:
                try:
                    mail_importer.import_mailbox(mailbox)
                except Exception as e:
                    traceback.print_exc(e)
            else:
                self.import_mail_from_stdin()

    return ImportMails


class MigrateBuilder(object):
    def _build_schema(self, db):
        model_builder = ModelBuilder(db)
        return model_builder.schema

    def __init__(self):
        plaid = Plaid(__name__)
        db = SQLAlchemy(plaid)
        schema = self._build_schema(db)
        mail_importer = MailImporter(schema)
        self._migrate = Migrate(plaid, db)

        manager = Manager(plaid)
        manager.add_command('db', MigrateCommand)
        CreateUser = _create_create_user(schema)
        manager.add_command('user', CreateUser())
        CreateProject = _create_create_project(schema)
        manager.add_command('project', CreateProject())
        ImportMails = _create_import_mails(mail_importer)
        manager.add_command('import', ImportMails())
        manager.run()

if __name__ == '__main__':
    MigrateBuilder()
