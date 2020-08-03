from flask import (
    Blueprint, 
    render_template, 
    url_for, 
    request, 
    redirect,
    flash,
    Markup,
    current_app,
    session,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from ..forms import (
    OTPForm, 
    VotersLoginForm, 
    BasicLoginForm,
    SearchCandidateRegForm,
    CandidateRegForm,
)
from ..utils.security import (
    generate_sign_token,
    validate_sign_token,
    generate_token,
    generate_secure_filename,
)
from ..models import (
    db, 
    Voters, 
    OTPs,
    Admins,
    Posts,
    Candidates,
    Preferences,
)
from ..utils import decorators, email, utils
from datetime import datetime as dt


auth_bp = Blueprint('auth', __name__, url_prefix="/auth")

otp_max_age = current_app.config["OTP_MAX_AGE"]



@auth_bp.route("/apply/<int:id>/", methods=["GET", "POST"])
def apply_details(id):
    post = Posts.query.get(int(id))
    if not post:
        flash("Invalid Request. Please try again", "error")
        return redirect(url_for("main.index"))
    
    form = SearchCandidateRegForm()
    choices = []
    other_choices = Posts.query.filter(Posts.id != int(id)).all()

    choices.append((post.id, post.post_name))
    for choice in other_choices:
        choices.append((choice.id, choice.post_name))
        
    form.post.choices = choices
    
    form.post.data = form.post.choices[0][0]
    if request.method == "POST":
        if form.validate_on_submit():
            user = Voters.query.filter_by(id_number = form.id_number.data).first()
            post = Posts.query.get(int(form.post.data))
            details = {
                "id": user.id_number,
                "fullname": user.full_name,
                "level": user.level,
                "post": post.post_name,
            }

            reg_datetime = Preferences.query.first()
            reg_end =  False
            reg_start = False

            if reg_datetime:
                if reg_datetime.reg_start and reg_datetime.reg_end:
                    d1 = utils.datetime_digitavote(reg_datetime.reg_start)
                    d2 = utils.datetime_digitavote(reg_datetime.reg_end)
                    
                    now_tm = dt.now().timestamp()

                    if now_tm - d1['timestamp'] >= 0:
                        reg_start = True

                    if now_tm - d2['timestamp'] >= 0:
                        reg_end = True
                    
                else:
                    reg_end = True
            else:
                reg_end = True
                
            if reg_end:
                details['reg_closed'] = True
            elif not reg_start:
                details['reg_not_start'] = True
            else:
                past_post = Candidates.query.filter_by(id_number=user.id_number).first()
                
                if post.level != user.level:
                    details["error"] = "Sorry! this post is not for your level"
                elif past_post:
                    details["error"] = "Sorry! You have already applied for "
                    if past_post.post.post_name == post.post_name:
                        details["error"] += "this post. "
                    else:
                        details["error"] += f"the post of {past_post.post.post_name.upper()}. "
                    url = url_for('auth.candidate_login')
                    details["error"] += Markup(f'<a style="color: #0E7B65;" href="{url}">Please login here</a>')
                else:
                    session["candidate_reg_info"] = {"id": user.id, "post": post.id}
                    session.modified = True

            return render_template("main/apply.html", 
                    apply_post=post,
                    form=form,
                    details=details)
                
        else:
            flash("Error in your form, please fix it.", "error")
    
    else:
        form.post.default = id
    
    return render_template("main/apply.html", 
                apply_post=post,
                form=form)



@auth_bp.route("/voter/login/", methods=["GET", "POST"])
def voters_login():
    form = VotersLoginForm()
    s_btn = {"value":"Login", 
                    "class_":"btn-round", 
                    "icon":"fa fa-sign-in-alt",
                    }
    
    if request.method == "POST":
        
        if form.validate_on_submit():

            voter = Voters.query.filter_by(id_number=form.id_number.data).first()
            
            if voter:
                if not voter.valid_otp(form.otp.data) \
                    or voter.otp_expired(otp_max_age):
                    
                    otp_url = url_for("auth.otp_gen")
                    message = "Sorry! invalid or expired OTP supplied, "
                    message += "please "
                    message += Markup(f'<a class="text-warning" href="{otp_url}">Resend here</a>')
                    flash(message,"error")
                
                else:
                    remove_session() #remove registration info
                    login_user(voter)
                    session["voter"] = True

                    next_ = request.args.get("next")
                    if next_:
                        return redirect(url_for(next_))
                    else:
                        return redirect(url_for("main.voters_profile"))
            
            else:
                flash("Invalid ID or expired OTP provided","error")
        
        else:
            flash("Invalid Details suplied","error")

    return render_template("auth/login.html", form=form, 
                                title="Voter's Login",
                                s_btn=s_btn)


@auth_bp.route("/gen/otp/", methods=["GET", "POST"])
def otp_gen():
    form = OTPForm()
    s_btn = {"value":"Send OTP", 
                    "class_":"btn-round", 
                    "icon":"fa fa-paper-plane",
                    }
    if request.method == "POST":
        
        if form.validate_on_submit():
            
            voter = Voters.query.filter_by(id_number=form.id_number.data).first()
            
            if voter:
                passkey = False
                if voter.password and voter.verify_password(form.password.data):
                    passkey = True
                else:
                    if voter.gen_pass:
                        if voter.gen_pass.verify_password(form.password.data):
                            voter.password = form.password.data
                            db.session.add(voter)
                            db.session.commit()
                            passkey = True
                if passkey:
                    if voter.has_otp():
                        if voter.otp_expired(otp_max_age):
                            voter.add_otp(type_="new")
                                 
                            email.send_otp(voter, voter.get_sms_otp())

                            otp_redirect_smessage()
                            return redirect(url_for("auth.voters_login"))
                        else:
                            from datetime import datetime

                            otp_ts = int(voter.otp.time_generated)
                            current_ts = int(datetime.timestamp(datetime.now()))
                            
                            mins = datetime.fromtimestamp(current_ts - otp_ts).minute
                            mins = (otp_max_age // 60) - mins

                            message = f"Please wait for {mins}"
                            message += "mins" if mins > 1 else "min"
                            message += " before generating another OTP."
                            
                            flash(message, "warning")
                            return render_template("auth/login.html", form=form, 
                                    title="Generate OTP",
                                    s_btn=s_btn)
                    else:
                        voter.add_otp()
                        email.send_otp(voter, voter.get_sms_otp())

                        otp_redirect_smessage()
                        return redirect(url_for("auth.voters_login"))
                
            flash("Wrong Identification Number or Password","error")
        else:
            flash("Invalid Details suplied","error")       
            

    return render_template("auth/login.html", form=form, 
                                title="Generate OTP",
                                s_btn=s_btn)


@auth_bp.route("admin/login/", methods=["GET", "POST"])
def admin_login():
    form = BasicLoginForm()
    s_btn = {"value":"Goto Dashboard", 
                    "class_":"btn-round", 
                    "icon":"fa fa-sign-in-alt",
                    }
    
    if request.method == "POST":
        if form.validate_on_submit():
            admin = Admins.query.filter_by(email=form.email.data).first()
            if admin and admin.verify_password(form.password.data):
                login_user(admin)
                remove_session() #remove registration info
                session["admin"] = True
                if admin.super_mod == True:
                    session["super"] = True
                
                flash("Hello, Welcome to DigitaVote Dashboard","success")
                return redirect(url_for("dashboard.dashboard"))
            else:
                flash("Invalid email or password","error")
        
        else:
            flash("Invalid Details suplied","error")

    return render_template("auth/login.html", form=form, 
                                title="Administrator's Login",
                                s_btn=s_btn)

@auth_bp.route("candidate/login/", methods=["GET", "POST"])
def candidate_login():
    title = "Candidate Login"
    type_ = "login"
    form = BasicLoginForm()
    s_btn = {"value":"Goto Profile", 
                    "class_":"btn-round", 
                    "icon":"fa fa-sign-in-alt",
                    }
    
    if request.method == "POST":
        if form.validate_on_submit():
            
            user = Voters.query.filter_by(email=form.email.data).first()
            if user:
                candidate = Candidates.query.filter_by(id_number=user.id_number).first()
                if candidate and candidate.verify_password(form.password.data):
                    login_user(candidate)
                    remove_session() #remove registration info
                    session["candidate"] = True
                    
                    nick = candidate.nick_name
                    if not nick:
                        nick = candidate.user_data.full_name.split()[0]
                    
                    flash(f"Hello {nick}, Welcome back","success")
                    return redirect(url_for("main.candidate"))
            
        flash("Invalid email or password","error")
        
    return render_template("auth/candidate.html",
                            title=title,
                            type_=type_,
                            form=form,
                            s_btn=s_btn,
                            )

@auth_bp.route("candidate/register/", methods=["GET", "POST"])
def candidate_register():
    data = session.get('candidate_reg_info')
    title = "Registration Form"
    type_ = "register"
    
    form = CandidateRegForm()

    user = Voters.query.get_or_404(int(data['id']))
    post = Posts.query.get_or_404(int(data['post']))

    c_exist = Candidates.query.filter_by(id_number = user.id_number).first()
    if c_exist:
        flash("Sorry, you can't register twice")
        remove_session() #remove registration info
        return redirect(url_for('main.index'))
    
    s_btn = {"value":"Submit" if post.payment == 0 else "Make Payment", 
                    "class_":"btn-round", 
                    "icon":"",
                    }

    form.id.data = user.id_number
    form.fullname.data = user.full_name
    form.post.data = post.post_name
    form.level.data = user.level

    if user.email:
        form.email.data = user.email
        form.email.render_kw = {"disabled":""}

    if request.method == "POST":
        if form.validate_on_submit():
            if not user.email:
                user.email = form.email.data
            new_candidate = Candidates(
                                            agenda=form.agenda.data,
                                            tag_name=form.tag_name.data,
                                            nick_name=form.nick_name.data,
                                            user_data=user,
                                            post=post
                                            )
            new_candidate.password = form.password.data
            session["candidate"] = True
            
            if post.payment == 0:
                new_candidate.registered = True
                db.session.add(new_candidate)
                db.session.commit()
                login_user(new_candidate)

                flash("Your application has been proccessed and created successfully", "success")
                return redirect(url_for("main.candidate"))
            else:
                db.session.add(new_candidate)
                db.session.commit()
                login_user(new_candidate)
                return redirect(url_for("auth.payment"))
        else:
            flash("Error(s) in your form, please fix it", "error")

    return render_template("auth/candidate.html",
                            title=title,
                            type_=type_,
                            form=form,
                            s_btn=s_btn,
                            )

@auth_bp.route("candidate/payment/")
@login_required
@decorators.permissions_required("candidate")
def payment():
    remove_session() #remove registration info
    return render_template("auth/payment.html")

@auth_bp.route("login/chooser/")
def login_chooser():
    return render_template("auth/chooser.html")

@auth_bp.route("logout/")
@login_required
def logout():
    remove_session() #remove registration info
    logout_user()
    session.pop("candidate", None)
    session.pop("voter", None)
    session.pop("admin", None)
    session.pop("super", None)
    return redirect(url_for("main.index"))


def otp_redirect_smessage():
    otp_url = url_for("auth.otp_gen")
    message = Markup(f'OTP Sent, check your mail box or <a class="text-primary" href="{otp_url}">Resend here</a>')
    flash(message, "success")


@auth_bp.before_request
def cleaner():
    if request.url == url_for("auth.otp_gen", _external=True):
        if  current_user.is_authenticated:
            flash("Sorry, you're not allowed to make that request", "error")
            return redirect(url_for('main.index'))
    
    if request.url == url_for("auth.payment", _external=True):
        if not session.get("candidate"):
            flash("Sorry, we can't complete your request", "error")
            return redirect(url_for('main.index'))

        if current_user.is_authenticated and current_user.registered:
            if current_user.post.payment > 0:
                flash("Sorry, your payment has been proccessed already", "error")    
            else:
                flash("Sorry, your post has no payment attached to it", "error")    
        
            return redirect(url_for('main.index'))
    
    if request.url == url_for("auth.candidate_register", _external=True):
        if not session.get('candidate_reg_info'):
            if current_user.is_authenticated:
                flash("Please Logout first before you can make that request", "error")
            else:
                flash("Sorry, apply for a post first before you can make that request", "error")
            
            return redirect(url_for('main.index'))
    
    if request.url == url_for("auth.admin_login", _external=True) \
        or request.url == url_for("auth.voters_login", _external=True) \
        or request.url == url_for("auth.login_chooser", _external=True) \
        or request.url == url_for("auth.otp_gen", _external=True) \
        or request.url == url_for("auth.candidate_login", _external=True):
        
        if current_user.is_authenticated:
            flash("Please Logout first before you can make that request", "error")
            if session.get('admin'):
                return redirect(url_for('dashboard.dashboard'))
            elif session.get('candidate'):
                return redirect(url_for('main.candidate'))
            elif session.get('voter'):
                return redirect(url_for('main.voters_profile'))
            else:
                return redirect(url_for('main.index'))


def remove_session(name="candidate_reg_info"):
    session.pop(name,None)


                    