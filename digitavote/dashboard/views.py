from flask import (
    Blueprint, 
    render_template, 
    url_for, 
    request, 
    redirect,
    flash,
    Markup,
    current_app,
)
from flask_login import (
    login_required,
    current_user,
)
from ..forms import (
    PostForm,
    UpdateForm,
    DataForm,
    AdminForm,
    PreferencesForm,
    EditCandidateForm,
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
    VRNs,
    Posts,
    Candidates,
    Payments,
    Admins,
    Preferences,
    Votes,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from sqlalchemy import desc, distinct
from ..utils import decorators
import os
import pandas as pd
import numpy as np

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@login_required
@decorators.permissions_required("admin")
def dashboard():
    
    return render_template("dashboard/admin_board.html")


@dashboard_bp.route("/list/candidates/")
@login_required
@decorators.permissions_required("admin")
def list_candidates():
    data = Candidates.query.all()

    return render_template("dashboard/list.html",
                            title="Candidates List",
                            data=data,
                            )

@dashboard_bp.route("/list/voters/")
@login_required
@decorators.permissions_required("admin")
def list_voters():
    data = Voters.query.order_by(Voters.id_number).all()

    return render_template("dashboard/list.html",
                            title="Voters List",
                            data=data,
                            )

@dashboard_bp.route("/list/posts/")
@login_required
@decorators.permissions_required("admin")
def list_posts():
    data = Posts.query.order_by(desc(Posts.payment)).all()

    return render_template("dashboard/list.html",
                            title="Posts List",
                            data=data,
                            )

@dashboard_bp.route("/list/votes/")
@login_required
@decorators.permissions_required("admin")
def list_votes():
    posts = Posts.query.order_by(desc(Posts.payment)).all()
    posts_voted = [post.post_name for post in posts if len(post.votes.all()) > 0]

    votes = Votes.query.all()

    voted_voters_list = []
    for voted_voter in votes: 
        if voted_voter.voter not in voted_voters_list:
            voted_voters_list.append(voted_voter.voter)
    
    voted_voters = []
    for voter in voted_voters_list:
        temp = {}
        temp["voter"] = voter.full_name.title()
        temp["candidates"] = []

        for vc in voter.votes.all():
            temp["candidates"].append(vc.candidate.user_data.full_name.title())

        voted_voters.append(temp)


    data = {
        "voted_posts": posts_voted,
        "voted_voters": voted_voters
    }
    total_posts =  len(data['voted_posts'])

    
    return render_template("dashboard/list.html",
                            title="Votes List",
                            data=data,
                            total_posts=total_posts,
                            )

@dashboard_bp.route("/preferences/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def preferences():
    form = PreferencesForm()
    p = Preferences.query.first()
    
    s_btn = {"value":"Save", 
                    "class_":"", 
                    "icon":"",
                    }


    if request.method == "POST":
        if form.validate_on_submit():
            '''
            2020-06-25T10:58
            2020-06-25T16:59
            '''
            try:
                
                
                if p:
                    db.session.delete(p)
                    db.session.commit()
                          
                pref = Preferences(
                        voting_start = form.voting_start_datetime.data,
                        voting_end = form.voting_end_datetime.data, 
                        reg_start = form.reg_start_datetime.data,
                        reg_end = form.reg_end_datetime.data, 
                    )
                db.session.add(pref)
                db.session.commit()
                
            except Exception as e:
                print(e)
                flash("Error occurred while processing the data", "error")
                return(redirect(url_for('dashboard.preferences')))
            else:
                flash("Voting Date/Time added successfully", "success")
                #return(redirect(url_for('dashboard.preferences')))
    else:
        if p:
            form.voting_start_datetime.data = p.voting_start
            form.voting_end_datetime.data = p.voting_end
            form.reg_start_datetime.data = p.reg_start
            form.reg_end_datetime.data = p.reg_end


    return render_template("dashboard/preferences.html",
                            title="Preferences",
                            form=form,
                            s_btn=s_btn,
                            )

@dashboard_bp.route("/add/admin/",  methods=["GET", "POST"])
@login_required
@decorators.permissions_required("super")
def add_admin():
    form = AdminForm()
    data = Admins.query.order_by(desc(Admins.id)).all()
    s_btn = {"value":"Add", 
                    "class_":"", 
                    "icon":"fa fa-plus-circle",
                    }
    error_occurred = False 

    if request.method == "POST":
    
        if form.validate_on_submit():
            try:
                new_admin = Admins(
                    full_name=form.fullname.data,
                    email=form.email.data,
                    super_mod=form.admin_level.data,
                )
                new_admin.password = form.password.data
                db.session.add(new_admin)
                db.session.commit()

            except Exception as e:
                flash("Error occurred while processing your form", "error")
                return(redirect(url_for('dashboard.add_admin')))
            else:
                flash("New Admin Added successfully", "success")
                return(redirect(url_for('dashboard.add_admin')))
        else:
            error_occurred = True

    if error_occurred:
        flash("One or more errors occurred while processing your form.", "error")
    
    return render_template("dashboard/admin_add_list.html",
                            title="Add Admin",
                            form=form,
                            data=data,
                            s_btn=s_btn,
                            )


@dashboard_bp.route("/edit/admin/<int:id>/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("super")
def edit_admin(id):
    form  = AdminForm()
    del form.password,form.email

    s_btn = {"value":"Update", 
                    "class_":"", 
                    "icon":"fa fa-up",
                    }

    admin = Admins.query.filter_by(id=id).first()
    
    form.fullname.data = admin.full_name
    form.fullname.render_kw = {"disabled":""}
        

    if request.method == "POST":
        if form.validate_on_submit():
            to_flash = False
            
            if admin.super_mod != form.admin_level.data:
                to_flash = True
                admin.super_mod = form.admin_level.data

            db.session.commit()
            
            if to_flash:
                flash("Admin updated successfully", "success")

            return redirect(url_for("dashboard.add_admin"))
        else:
            flash("Please correct the error(s)", "error")
    
    else:
        if not admin:
            flash("Invalid request, please try again", "error")
            return redirect(url_for("dashboard.add_admin"))

        form.admin_level.data = admin.super_mod

    return render_template("dashboard/edit_page.html",
                            form=form,
                            s_btn=s_btn,
                            title="Edit Admin")

@dashboard_bp.route("/edit/post/<int:id>/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def edit_post(id):
    form = PostForm()
    s_btn = {"value":"Update Post", 
                    "class_":"", 
                    "icon":"fa fa-up",
                    }
   
    if request.method == "POST":
        if form.validate_on_submit():
            
            post = Posts.query.filter_by(id=id).first()
            post.post_name = form.name.data 
            post.description = form.description.data
            post.level = form.level.data
            post.payment = form.payment.data
            
            db.session.add(post)
            db.session.commit()

            flash("Post updated successfully", "success")
            return redirect(url_for("dashboard.add_post"))
        else:
            flash("Please correct the error(s)", "error")
    
    else:
        post = Posts.query.filter_by(id=id).first()
        if not post:
            flash("The post you're requesting for not yet exist, please create it first", "error")
            return redirect(url_for("dashboard.add_post"))
        
        form.name.data = post.post_name
        form.description.data = post.description
        form.level.data = post.level
        form.payment.data = post.payment

    return render_template("dashboard/edit_page.html",
                            form=form,
                            s_btn=s_btn,
                            title="Edit Post")


#TODO: To complete later
@dashboard_bp.route("/edit/candidate/<int:id>/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def edit_candidate(id):
    form = EditCandidateForm()
    s_btn = {"value":"Update", 
                    "class_":"", 
                    "icon":"fa fa-up",
                    }
    candidate = Candidates.query.get(int(id))
    if not candidate:
        flash("Invalid request, please try again", "error")
        return redirect(url_for("dashboard.list_candidates"))
      
    posts_from_db = Posts.query.all()
    form.posts.default = candidate.post_apply
    form.posts.choices =  [(post.id, post.post_name) for post in posts_from_db]
    

    form.name.data = candidate.user_data.full_name

    if candidate.post.payment == 0:
        del form.payment
    else:
        if candidate.payment and candidate.payment.paid:
            form.payment.default = 1 # 1 - paid

    if request.method == "POST":
        if form.validate_on_submit():
            
            db.session.commit()

            flash("Candidate updated successfully", "success")
            return redirect(url_for("dashboard.list_candidates"))
        else:
            flash("Please correct the error(s)", "error")


    return render_template("dashboard/edit_page.html",
                            form=form,
                            s_btn=s_btn,
                            title="Edit Candidate")


@dashboard_bp.route("/add/post/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def add_post():
    form = PostForm()
    s_btn = {"value":"Add Post", 
                    "class_":"", 
                    "icon":"fa fa-plus-circle",
                    }
    
    recent_posts_data = {
        "data": Posts.query.order_by(desc(Posts.id)).limit(5).all(),
        "count": Posts.query.count(),
    }

    if request.method == "POST":
        if form.validate_on_submit():

            new_post = Posts(
                post_name=form.name.data,
                description=form.description.data,
                level=form.level.data,
                payment=form.payment.data
            )
            
            db.session.add(new_post)
            db.session.commit()

            flash("Post Added Successfully", "success")
            return redirect(url_for('dashboard.add_post'))

        else:
            flash("Please correct the error(s)", "error")
    
    return render_template("dashboard/new_post.html", 
                            form=form,
                            s_btn=s_btn,
                            recent_posts=recent_posts_data,
                            )

@dashboard_bp.route("/add/voter/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def add_voter():
    form = DataForm()
    del form.phone

    s_btn = {"value":"Add Voter", 
                    "class_":"", 
                    "icon":"fa fa-plus-circle",
                    }
    
    recent_voters_data = {
        "data": Voters.query.order_by(desc(Voters.id)).limit(5).all(),
        "count": Voters.query.count(),
    }

    if request.method == "POST":
        if form.validate_on_submit():
            new_voter = Voters(
                id_number=form.id.data,
                full_name = form.fullname.data.upper(),
                level = form.level.data,
                email = form.email.data
                )
            db.session.add(new_voter)
            db.session.commit()

            flash("New Voter Added Successfully", "success")
            return redirect(url_for('dashboard.add_voter'))
        else:
            flash("Please correct the error(s)", "error")
    
    return render_template("dashboard/new_voter.html", 
                            form=form,
                            s_btn=s_btn,
                            recent_voters=recent_voters_data,
                            )

@dashboard_bp.route("/edit/voter/<int:id>/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def edit_voter(id):
    form = DataForm()
    del form.phone

    s_btn = {"value":"Update Voter", 
                    "class_":"", 
                    "icon":"fa fa-up",
                    }
    voter = Voters.query.filter_by(id=id).first()

    if request.method == "POST":
        if form.validate_on_submit():
            to_update = False

            if form.id.data != voter.id_number:
                voter.id_number = form.id.data
                to_update = True

            if form.fullname.data != voter.full_name:
                voter.full_name = form.fullname.data.upper()
                to_update = True

            if form.level.data != voter.level:
                voter.level = form.level.data 
                to_update = True
            
            if form.email.data != voter.email:
                voter.email = form.email.data
                to_update = True
        
            if to_update:
                try:
                    db.session.add(voter)
                    db.session.commit()
                    flash("Voter updated successfully", "success")
                except Exception as e:
                    flash("Error occurred while processing your form", "error")

            return redirect(url_for("dashboard.add_voter"))
        else:
            flash("Please correct the error(s)", "error")
    
    else:
        if not voter:
            flash("The voter you're requesting for not yet exist, please create it first", "error")
            return redirect(url_for("dashboard.add_voter"))
        
        form.id.data = voter.id_number
        form.fullname.data = voter.full_name
        form.level.data = voter.level
        form.email.data = voter.email

    return render_template("dashboard/edit_page.html",
                            form=form,
                            s_btn=s_btn,
                            title="Edit Voter")


@dashboard_bp.route("/admin/profile/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("admin")
def admin_profile():
    form = UpdateForm()
    del form.id

    user = current_user

    ADMIN_LEVEL = ["MODERATOR", "SUPER MODERATOR"]

    form.level.data =  ADMIN_LEVEL[int(user.super_mod)]
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
                user.full_name = form.fullname.data.upper()
            
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
            
            return redirect(url_for('dashboard.admin_profile'))
        
        else:
            flash("Error(s) in your form, please fix it", "error")

    return render_template("dashboard/admin_profile.html",
                            form=form,
                            user=user,
                            level_text = form.level.data
                            )
   

@dashboard_bp.route("/upload/bulk/voter/", methods=["POST"])
@login_required
@decorators.permissions_required("admin")
def upload_voter():
    valid_ext = ("csv", "xlsx")
    max_size = 1024 * 1024 * 2 #2mb
    valid_data = False

    voters_file = request.files["voter-file"]
    dst = request.form["from"]

    voters_file.seek(0, os.SEEK_END)
    voters_file_size = voters_file.tell()
    voters_file.seek(0)

    voters_file_ext =  voters_file.filename.rsplit(".", 1)[1].lower()

    if voters_file_ext in valid_ext and \
        voters_file_size <= max_size:
        valid_data = True
    
    if valid_data:
        try:
            if voters_file_ext == valid_ext[0]:
                df = pd.read_csv(voters_file)
            elif voters_file_ext == valid_ext[1]:
                df = pd.read_excel(voters_file)

            valid_columns = ("ID", "FULL NAME", "EMAIL", "LEVEL")
            
            for col in df:
                if col.strip() not in valid_columns:
                    raise Exception("")
            df.rename(
            columns={
                "ID": "id_number",
                "FULL NAME": "full_name",
                "EMAIL": "email",
                "LEVEL": "level"
                },
            inplace=True
            )
            df["full_name"] = df["full_name"].str.title()
        except Exception as e:
            if voters_file_ext == valid_ext[0]:
                flash("Please make sure the CSV file is comma separated and provide the following valid columns(ID, FULL NAME, EMAIL, LEVEL)", "error")
            else:
                flash("Please make sure you provide the following valid columns(ID, FULL NAME, EMAIL, LEVEL)", "error")
        else:
            try:
                df.to_sql(
                    "voters", 
                    db.engine, 
                    index=False, 
                    if_exists="append",
                    chunksize=500,
                )

                flash("Voters Data uploaded successfully.", "success")
            except Exception as e:
                flash("Error occurred while processing the data. Please check for any duplicate record", "error")
    
    else:
        flash(f"Error! Only CSV/XLSX file allowed with maximum of {max_size // (1024  * 1024)}mb file size", "error")


    return redirect(dst)


