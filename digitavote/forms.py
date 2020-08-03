from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from flask import (
    session,
    request,
    url_for,
    current_app,
)
from wtforms import (
    TextField,
    StringField,
    TextAreaField,
    PasswordField,
    BooleanField,
    SubmitField,
    IntegerField,
    SelectField,
    RadioField,
    DateTimeField,
    FormField,
    ValidationError,

)
from wtforms.validators import (
    DataRequired,
    Email,
    Regexp,
    Length,
    EqualTo,
    Optional,
)
from wtforms.widgets import PasswordInput
from .models import (
    db,
    Posts, 
    Voters,
    Admins,
)
from flask_login import (
    current_user,
)
from werkzeug.security import (
    check_password_hash,
)
from datetime import datetime as dt 

class DataForm(FlaskForm):
    id = StringField("ID", validators=[DataRequired()])
    fullname = StringField("Full Name", validators=[DataRequired()])
    phone = StringField("Phone Number", render_kw={"type":"tel", "pattern":"/^0[7-9][01]\d{8}$/"}, validators=[DataRequired()])
    level = StringField("Level", validators=[DataRequired()])
    email = StringField("Email", render_kw={"type":"email"}, validators=[DataRequired(), Email()])
    
    def validate_id(self, field):
        if session.get("admin"):
            if request.url == url_for("dashboard.add_voter", _external=True):
                voter = Voters.query.filter_by(id_number = field.data).first()
                if voter:
                    raise ValidationError("Sorry! ID already exist for another voter")
    
    def validate_email(self, field):
        if session.get("admin"):
            if request.url == url_for("dashboard.add_voter", _external=True):
                voter = Voters.query.filter_by(email = field.data).first()
                if voter:
                    raise ValidationError("Sorry! email already exist for another voter")
            #admin = Admins.query.filter_by(email = field.data).first()
        
        else:
            voter = Voters.query.filter_by(email = field.data).first()
            if voter:
                if self.id.data != voter.id_number:
                    raise ValidationError("Sorry! email already exist")

    def validate_phone(self, field):
        import re
        p_reg = re.compile(r'^0[7-9][01]\d{8}$')
        match = p_reg.match(field.data)

        if not match:
            raise ValidationError("Please enter a valid Nigeria phone number")


class UpdateForm(DataForm):
    opassword = StringField("Old Password", widget=PasswordInput(hide_value=False))
    password = PasswordField("New Password")
    cpassword = PasswordField("Confirm Password", validators=[EqualTo('password', "Password mismatch")])

    def validate_opassword(self, field):

        if field.data != "":
            self.password.validators = [DataRequired()]
            
            good = False
            user = None

            if not any(['admin' in session, 'voter' in session]):
                if request.url == url_for("main.candidate", _external=True):
                    user = current_user
                else:
                    user = current_user.user_data
            else:
                user = current_user
            
            if user and user.verify_password(field.data): good = True

            if not good:
                raise ValidationError("Sorry, invalid password")
            

    def validate_password(self, field):
        if field.data != "":
            try:
                if self.opassword.data == field.data:
                    raise ValidationError("Sorry, you can't use your former password")
            except Exception  as e:
                self.password.validators = [DataRequired()]


class CUpdateForm(UpdateForm):
    tag_name = StringField("Tag Name", validators=[Optional()])
    nick_name = StringField("Nick Name", validators=[Optional()])
    agenda = TextAreaField("Agenda", validators=[Optional()])


class AdminForm(DataForm):
    admin_level = SelectField("Admin Level", coerce=int, choices=[(0, "Moderator"), (1, "Super Moderator")], default=0)
    password = PasswordField("Password", validators=[DataRequired(), Length(min=3, max=32)])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.id, self.level, self.phone


class AdminFormMaster(AdminForm):
    mpassword = PasswordField("Master Password", validators=[DataRequired(), Length(min=3, max=32)])
    
    def validate_mpassword(self, field):
        master_password = current_app.config["MASTER_PASSWORD_KEY"]
        if not master_password:
            raise ValidationError("Can't verify master password")

        if field.data != master_password:
            raise ValidationError("Invalid Master Password")


class OTPForm(FlaskForm):
    id_number = StringField("Identification Number", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

    def validate_form(self):
        pass


class VotersLoginForm(FlaskForm):
    id_number = StringField("Identification Number", validators=[DataRequired()])
    otp = StringField("OTP", validators=[DataRequired()])


class BasicLoginForm(FlaskForm):
    email = StringField("Email", render_kw={"type":"email"}, validators=[DataRequired(), Email("Please Enter a valid email addres")])
    password = PasswordField("Password", validators=[DataRequired()])
    

class PostForm(FlaskForm):
    name = StringField("Post Name", validators=[DataRequired(), Length(min=3, message="The length of the Post Name is too small")])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10, max=230)])
    level = StringField("Level", validators=[DataRequired(), Length(min=3, message="The length is too small")])
    payment = IntegerField("Payment")

    """
    def validate_name(self, field):
        if Posts.query.filter_by(post_name = field.data).first():
            raise ValidationError(f"{field.data} in database already, please add another post")
    """
    def validate_payment(self, field):
        try:
            if field.data < 0:
                raise ValidationError("Payment can't be less than zero")
        except Exception as e:
            raise ValidationError("Payment can't be less than zero")


class SearchCandidateRegForm(FlaskForm):
    post = SelectField("Post", coerce=int, validators=[DataRequired()])
    id_number = StringField("Identification Number", validators=[DataRequired()])

    def validate_id_number(self, field):
        user = Voters.query.filter_by(id_number=field.data).first()
        if not user:
            raise ValidationError("Sorry, invalid ID supplied")


class CandidateRegForm(FlaskForm):
    id = StringField("ID", render_kw={"disabled":""}, validators=[DataRequired()])
    fullname = StringField("Full Name", render_kw={"disabled":""}, validators=[DataRequired()])
    post = StringField("Post", render_kw={"disabled":""}, validators=[DataRequired()])
    level = StringField("Level", render_kw={"disabled":""}, validators=[DataRequired()])
    email = StringField("Email", render_kw={"type":"email"}, validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    cpassword = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password', "Password mismatch")])
    tag_name = StringField("Tag Name", validators=[Optional()])
    nick_name = StringField("Nick Name", validators=[Optional()])
    agenda = TextAreaField("Agenda", validators=[Optional()])


class PhotoUploadForm(FlaskForm):
    photo = FileField(validators=[FileRequired()])


class DataLookupForm(FlaskForm):
    user_type = SelectField("User Type", coerce=int, choices=[(1, "Voter"), (2, "Candidate"), (3,"Admin")], default=1, validators=[DataRequired()])
    id = StringField("Identification Number", validators=[DataRequired()])


class VRNLookupForm(FlaskForm):
    ref = StringField("Vote Reference Number(VRN)", validators=[DataRequired()])


class PreferencesForm(FlaskForm):
    reg_start_datetime = StringField("Registration Start Date/Time", render_kw={"type":"datetime-local"})
    reg_end_datetime = StringField("Registration End Date/Time", render_kw={"type":"datetime-local"})
    voting_start_datetime = StringField("Voting Start Date/Time", render_kw={"type":"datetime-local"})
    voting_end_datetime = StringField("Voting End Date/Time", render_kw={"type":"datetime-local"})


    def validate_data(self, field1, field2, f_name):
        if field2.data:
            try:
                date1, time1 = field1.data.split("T")
                date2, time2 = field2.data.split("T")

                year1, month1, day1 = date1.split("-")
                hour1, minutes1 = time1.split(":")

                year2, month2, day2 = date2.split("-")
                hour2, minutes2 = time2.split(":")

                d1 = dt(year=int(year1), month=int(month1), day=int(day1), hour=int(hour1), minute=int(minutes1))
                d2 = dt(year=int(year2), month=int(month2), day=int(day2), hour=int(hour2), minute=int(minutes2))

                d1 = d1.timestamp()
                d2 = d2.timestamp()
                

            except Exception as e:
                print(e) 
                raise ValidationError("Invalid Date/Time")
            else:
                if (d1 - d2) <= 0:
                    raise ValidationError(f"{f_name} end date/time must be greater than start date/time")

    def validate_reg_end_datetime(self, field):
        self.validate_data(field, self.reg_start_datetime, "Registration")
    
    def validate_voting_end_datetime(self, field):
        self.validate_data(field, self.voting_start_datetime, "Voting")

class EditCandidateForm(FlaskForm):
    name = StringField("Full Name", render_kw={"disabled": ""})
    posts = SelectField("Post", coerce=int)
    payment = SelectField("Payment", coerce=int, choices=[(0, "Pending"), (1, "Paid")])
