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
    AdminFormMaster,
)
from ..utils.security import (
    generate_sign_token,
    validate_sign_token,
    generate_token,
    generate_secure_filename,
)
from ..models import (
    db, 
    Admins,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from ..utils import decorators



master_bp = Blueprint("master", __name__, url_prefix="/master")


@master_bp.route("/add/admin/",  methods=["GET", "POST"])
def add_admin():
    form = AdminFormMaster()

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
                return(redirect(url_for('master.add_admin')))
            else:
                flash("New Admin Added successfully", "success")
                return(redirect(url_for('master.add_admin')))
        else:
            error_occurred = True

    if error_occurred:
        flash("One or more errors occurred while processing your form.", "error")
    
    return render_template("master/add_admin.html",
                            title="Add Admin",
                            form=form,
                            s_btn=s_btn,
                            )






