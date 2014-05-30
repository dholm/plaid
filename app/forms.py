from wtforms import form
from wtforms import fields
from wtforms import validators


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    email = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])
    remember_me = fields.BooleanField()
    submit = fields.SubmitField('Login')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self._schema = kwargs.get('schema')

    def validate_email(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

    def validate_password(self, field):
        user = self.get_user()

        if user and (user.password != self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        email = self.email.data.strip()
        return self._schema.User.get_by_email(email)


class RegistrationForm(form.Form):
    email = fields.TextField(validators=[validators.required(),
                                         validators.Email()])
    password = fields.PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = fields.PasswordField('Repeat Password')
    name = fields.TextField(validators=[validators.required()])
    submit = fields.SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self._schema = kwargs.get('schema')

    def validate_email(self, field):
        user = self._schema.User.get_by_email(email=self.email.data)
        if user is not None:
            raise validators.ValidationError('E-Mail already used. Did you '
                                             'forget your password?')
