from flask import (
    Blueprint, 
    render_template, 
    url_for, 
    request, 
    redirect,
    flash,
    session,
    current_app,
)
from ..models import (
    db, 
    Voters, 
    OTPs, 
    VRNs,
    Posts,
    Candidates,
    Payments,
    Admins,
    GenPassword
)
from flask_login import (
    login_required,
    current_user,
)
from ..forms import (
    UpdateForm,
    CUpdateForm,
    DataLookupForm,
)
from ..utils.security import (
    generate_sign_token,

    validate_sign_token,
    generate_token,
    generate_secure_filename,
)
from sqlalchemy import desc
from ..utils import decorators, email
import os
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def index():
    return render_template("main/index.html")

@main_bp.route("/apply/")
def apply():
    posts = Posts.query.order_by(desc(Posts.payment)).all()
    return render_template("main/apply.html", posts=posts)

@main_bp.route("/apply/post/details/<int:id>/")
def apply_post_details(id):
    post = Posts.query.get(int(id))
    if not post:
        flash("Invalid Request. Please try again", "error")
        return redirect(url_for("main.index"))
    return render_template("main/apply.html", post=post)


@main_bp.route("/candidate/profile/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("candidate")
def candidate():
    form = CUpdateForm()
    user = current_user.user_data

    form.id.data = user.id_number
    form.id.render_kw = {"disabled":""}
    
    form.level.data = user.level
    form.level.render_kw = {"disabled":""}

    if not form.fullname.data:
        form.fullname.data = user.full_name
    
    if user.email and not form.email.data:
        form.email.data = user.email
    
    if user.phone and not form.phone.data:
        form.phone.data = user.phone
    
    if current_user.tag_name and not form.tag_name.data:
        form.tag_name.data = current_user.tag_name

    if current_user.nick_name and not form.nick_name.data:
        form.nick_name.data = current_user.nick_name

    if current_user.agenda and not form.agenda.data:
        form.agenda.data = current_user.agenda
 
    if request.method == "POST":
        if form.validate_on_submit():
            to_flash = False
            
            if form.fullname.data != user.full_name:
                to_flash = True
                user.full_name = form.fullname.data
            
            if form.email.data != user.email:
                to_flash = True
                user.email = form.email.data
            
            if form.phone.data != user.phone:
                to_flash = True
                user.phone = form.phone.data
            
            if current_user.tag_name != form.tag_name.data:
                to_flash = True
                current_user.tag_name = form.tag_name.data

            if current_user.nick_name != form.nick_name.data:
                to_flash = True
                current_user.nick_name = form.nick_name.data

            if current_user.agenda != form.agenda.data:
                to_flash = True
                current_user.agenda = form.agenda.data
            
            if form.password.data:
                to_flash = True
                current_user.password = form.password.data

            if to_flash:
                flash("Your profile has been updated successfully", "success")
                db.session.add(current_user)
                db.session.commit()
            
            return redirect(url_for('main.candidate'))
        
        else:
            flash("Error(s) in your form, please fix it", "error")

    return render_template("main/candidate_main.html",
                            form=form,
                            )


@main_bp.route("/voter/profile/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("voters")
def voters_profile():
    form = UpdateForm()
    user = current_user if not session.get('candidate') \
        else current_user.user_data

    form.id.data = user.id_number
    form.id.render_kw = {"disabled":""}
    
    form.level.data = user.level
    form.level.render_kw = {"disabled":""}

    if not form.fullname.data:
        form.fullname.data = user.full_name
    
    if user.email and not form.email.data:
        form.email.data = user.email
    
    if user.phone and not form.phone.data:
        form.phone.data = user.phone

    if request.method == "POST":
        if form.validate_on_submit():
            to_flash = False
            
            if form.fullname.data != user.full_name:
                to_flash = True
                user.full_name = form.fullname.data
            
            if form.email.data != user.email:
                to_flash = True
                user.email = form.email.data
            
            if form.phone.data != user.phone:
                to_flash = True
                user.phone = form.phone.data
            
            if form.password.data:
                to_flash = True
                user.password = form.password.data

            if to_flash:
                flash("Your profile has been updated successfully", "success")
                db.session.add(user)
                db.session.commit()
            
            return redirect(url_for('main.voters_profile'))
        
        else:
            flash("Error(s) in your form, please fix it", "error")

    return render_template("main/voters_main.html",
                            form=form,
                            user=user,
                            )

@main_bp.route("/factory/password/")
def pf_chooser():
    return render_template("main/pf_chooser.html")

@main_bp.route("/factory/password/generate/", methods=["GET", "POST"])
def gen_password():
    form = DataLookupForm()
    del form.user_type

    title ="Generate Password"
    
    if request.method == "POST":
        if form.validate_on_submit():
            user = Voters.query.filter_by(id_number = form.id.data).first()
            if user:
                details = {
                  "id": user.id_number,
                  "fullname": user.full_name  
                }

                if user.email and not user.gen_pass:
                    passkey = generate_token(user.id_number, length=8)
                
                    pass_ = GenPassword(voter=user)
                    pass_.password = passkey

                    db.session.add(user)
                    db.session.commit()
                    
                    subject = "Account Password - DigitaVote"
                    sender = ("DigitaVote", "digitavote@outlook.com")
                    recipients = [user.email]
                    text_body = render_template("message/pass_email_template.txt",user=user,password=passkey)
                    html_body = render_template("message/pass_email_template.html",user=user,password=passkey)
                    app = current_app._get_current_object()

                    email.send_mail(subject,sender, recipients, text_body, html_body, app)
                
                    details["success"] = f"Your password has been sent to your email({user.email})"
                elif user.gen_pass:
                    details["error"] = "Sorry, you can't generate password twice. Kindly use the reset option."
                else:
                    details["error"] = "Sorry, no email attached to this account, please contact your administrator"
                

                return render_template("main/password_factory.html",
                            title=title,
                            form=form,
                            details=details)
        
        flash("Incorrect Identification Number", "error")
    
    return render_template("main/password_factory.html",
                            title=title,
                            form=form,)

@main_bp.route("/factory/password/reset/", methods=["GET", "POST"])
def reset_password():
    form = DataLookupForm()
    title ="Reset Password"
    
    if request.method == "POST":
        if form.validate_on_submit():
            user_type = int(form.user_type.data)
            type_dict = {1: "voter", 2: "candidate", 3: "admin"}
            user = None

            if user_type == 1: #voter
                user = Voters.query.filter_by(id_number = form.id.data).first()
                if user:
                    details = {
                    "id": user.id_number,
                    "fullname": user.full_name  
                    }
            elif user_type == 2: #candidate
                candidate = Candidates.query.filter_by(id_number = form.id.data).first()
                if candidate:
                    user = candidate.user_data
                if user:
                    details = {
                    "id": user.id_number,
                    "fullname": user.full_name  
                    }
            elif user_type == 3: #admin
                user = Admins.query.filter_by(email = form.id.data).first()
                if user:
                    details = {
                    "id": user.email,
                    "fullname": user.full_name  
                    }
            else:
                pass

            if user:
                if user.email:
                    subject = "Reset Password - DigitaVote"
                    sender = ("DigitaVote", "digitavote@outlook.com")
                    recipients = [user.email]
                    app = current_app._get_current_object()
                        
                    uts = URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="reset-link")
                        
                    if user_type == 1: #voter
                        token = uts.dumps(
                                {
                                    "id": user.id_number
                                }
                            )
                    else: #candidate / admin
                        if user_type == 2 or user_type == 3:
                            token = uts.dumps(
                                {
                                    "id": user.email,
                                    "user_type": type_dict[user_type]
                                }
                            )
                        
                    text_body = render_template("message/reset_email_template.txt",user=user,token=token)
                    html_body = render_template("message/reset_email_template.html",user=user,token=token)
                    email.send_mail(subject,sender, recipients, text_body, html_body, app)
                        
                    if user_type != 3:
                        details["success"] = f"Password reset link has been sent to your email({user.email})"
                    else:
                        details["success"] = "Password reset link has been sent to your email"
                else:
                    details["error"] = "Sorry, no email attached to this account, please contact your administrator"
                    

                return render_template("main/password_factory.html",
                                title=title,
                                form=form,
                                details=details,
                                reset=True)
        
        if user_type and user_type == 3:
            flash("Sorry, no user with that email address", "error")
        else:
            flash("Incorrect Identification Number", "error")
    
    return render_template("main/password_factory.html",
                            title=title,
                            form=form,
                            reset=True)

@main_bp.route("/password/reset/<token>/", methods=["GET", "POST"])
def reset_password_pass(token):
    if current_user.is_authenticated:
            flash("You're not allowed to view that page", "error")
            if session.get('admin'):
                return redirect(url_for('dashboard.dashboard'))
            elif session.get('candidate'):
                return redirect(url_for('main.candidate'))
            elif session.get('voter'):
                return redirect(url_for('main.voters_profile'))
            else:
                return redirect(url_for('main.index'))
    
    form = UpdateForm()
    del form.id, form.email, form.phone, form.level, form.fullname, form.opassword

    title ="Reset Password"

    error = True
    error_message = None

    try:
        expiry_time = current_app.config["RESET_TOKEN_EXPIRY_TIME"]
        uts = URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="reset-link")
        
        user_data = uts.loads(token, max_age=expiry_time)
        error = False
        
    except Exception as e:
        error_message = "Expired or invalid token supplied".upper()

    if error:
        return render_template("main/password_factory.html",
                            error_message=error_message,
                            error=error,
                            title=title,
                            reset_pass=True)
    else:
        if request.method == "POST":
            if form.validate_on_submit():
                if user_data.get("user_type"):
                    user_type = user_data["user_type"]
                    if user_type == "admin":
                        user = Admins.query.filter_by(email=user_data['id']).first()
                    elif user_type == "candidate":
                        pre_user = Voters.query.filter_by(email = user_data['id']).first()
                        if pre_user:
                            user = pre_user.candidate
                    else:
                        pass
                else:
                    user = Voters.query.filter_by(id_number=user_data['id']).first()
 
                if user:
                    user.password = form.password.data
                    db.session.add(user)
                    db.session.commit()
                    flash("Your password has been changed successfully", "success")
                else:
                    flash("Sorry, no user found", "error")
                return redirect(url_for("main.index"))

        return render_template("main/password_factory.html",
                                title=title,
                                form=form,
                                reset_pass=True)



@main_bp.route("/upload/dp/", methods=["POST"])
@login_required
def upload_dp():
    if any(['voter' in session, 'candidate' in session, 'admin' in session]):
        photo = request.files['photo']
        dest = request.form["from"]
        user = current_user if not session.get('candidate') \
                else current_user.user_data
        
        if not photo:
            flash("Please upload a valid image with the right size", "error")
        
        if validate_photo(photo):
            if not session.get("admin"):
                sfile_name = generate_secure_filename(user.id_number.replace("/","-"))
            else:
                sfile_name = generate_secure_filename(user.email)

            file_name = f"{sfile_name}.{photo.filename.rsplit('.',1)[1]}"
            
            save_photo(photo, file_name)
            update_database(user, file_name)
            
            flash("Your profile photo has been updated successfully", "success")
        else:
            flash("Please upload a valid image with the right size.", "error")
    
    else:
        flash("Sorry, Login required", "error")

    return redirect(dest)

def validate_photo(photo):
    valid_ext = ('jpg', 'jpeg', 'png')
    fname = photo.filename
    photo_ext = fname.rsplit(".",1)[1]
    
    photo_max_size = 1024 * 50 #50kb

    photo.seek(0, os.SEEK_END)
    fsize = photo.tell()
    photo.seek(0) #move the pointer back

    if fname == "" or "." not in fname  or photo_ext.lower() not in valid_ext:
        return False
    elif fsize > photo_max_size:
        return False
    else:
        return True

def save_photo(photo, file_name):
    folder = current_app.config["PHOTO_UPLOAD_PATH"]
    photo.save(os.path.join(folder, file_name))


def update_database(user, file_name):
    if user.dp_fname:
        old = user.dp_fname
        folder = current_app.config["PHOTO_UPLOAD_PATH"]
        
        try:
            os.remove(os.path.join(folder, old))
        except Exception as e:
            pass

    user.dp_fname = file_name
    db.session.add(user)
    db.session.commit()




@main_bp.before_request
def cleaner():
    if request.url == url_for("main.gen_password", _external=True) \
        or request.url == url_for("main.reset_password", _external=True) \
        or request.url == url_for("main.pf_chooser", _external=True):
        
        if current_user.is_authenticated:
            flash("You're not allowed to view that page", "error")
            if session.get('admin'):
                return redirect(url_for('dashboard.dashboard'))
            elif session.get('candidate'):
                return redirect(url_for('main.candidate'))
            elif session.get('voter'):
                return redirect(url_for('main.voters_profile'))
            else:
                return redirect(url_for('main.index'))

