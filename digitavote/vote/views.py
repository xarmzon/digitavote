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
    login_required,
    current_user,
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
    Posts,
    Candidates,
    Payments,
    Votes,
    VRNs,
    Preferences,
)
from ..forms import (
    VRNLookupForm,
)
from ..utils import decorators, utils
from sqlalchemy import desc, func
from datetime import datetime as dt




vote_bp = Blueprint("vote", __name__, url_prefix="/vote")


@vote_bp.route("view/live/", methods=["GET", "POST"])
def live_view():
    
    voting_datetime = Preferences.query.first()
    voting_end =  False

    if voting_datetime:
        if voting_datetime.voting_start and voting_datetime.voting_end:
            d1 = utils.datetime_digitavote(voting_datetime.voting_end)
            now_tm = dt.now().timestamp()
            if now_tm - d1['timestamp'] >= 0:
                voting_end = True
        else:
            voting_end = True
    else:
        voting_end = True
    
    if voting_end:
        return render_template("vote/live_view.html",
                            no_vote=voting_end,
                            )

    posts = Posts.query.order_by(desc(Posts.payment)).all()
    posts_voted = [(post.id, post.post_name) for post in posts if len(post.votes.all()) > 0]

    data = []

    for post in posts_voted:
        id, name = post
        
        temp = {}
        temp['post'] = {
            "id": id,
            "name": name.upper(),
            "pcounts": Votes.query.filter_by(vote_post = id).count(),
            }

        candidates = Candidates.query.filter_by(post_apply = int(id)).all()
        
        c_temp_list = []
        for c in candidates:
            c_temp = {}
            c_temp['cname'] = c.user_data.full_name.title()
            c_temp['dp'] = c.user_data.dp_fname 
            c_temp["vcounts"] = Votes.query.filter_by(vote_for = c.id_number).count()

            percent = int(c_temp["vcounts"]) / int(temp['post']['pcounts']) * 100
            c_temp["vpercents"] = f"{percent:.1f}"
            
            c_temp_list.append(c_temp)
        
        temp["candidates"] = c_temp_list
        
        data.append(temp)
        
    #print(data)

    return render_template("vote/live_view.html",
                            data=data,
                            voting_datetime=d1,
                            )


@vote_bp.route("view/details/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("voters")
def view_vote():
    form = VRNLookupForm()

    if request.method == "POST":
        vrn = VRNs.query.filter_by(vrn=form.ref.data).first()
        #votes_by_ref = Votes.query.filter_by(vote_ref = form.ref.data).all()
        if vrn:
            votes_by_ref = vrn.votes.all()
            if votes_by_ref:
                data = {
                    "voter": {
                        "id": votes_by_ref[0].voter.id_number.title(),
                        "name": votes_by_ref[0].voter.full_name.title(),
                        "vrn": votes_by_ref[0].voter.vrn.vrn.upper(),
                    }, 
                    "details": [],
                }
                for vote in votes_by_ref:
                    temp = {
                        "name": vote.candidate.user_data.full_name.upper(),
                        "nickname": vote.candidate.nick_name.title(),
                        "tagname": vote.candidate.tag_name.title(),
                        "level": vote.candidate.user_data.level.upper(),
                        "dp": vote.candidate.user_data.dp_fname,
                        "agenda": vote.candidate.agenda,
                        "post": vote.post.post_name.upper(),
                    }
                    data["details"].append(temp)
                
                if data:
                    return render_template("vote/vote_details.html",
                                        form=form,
                                        details=data,)
            else:
                flash("No votes attached to this VRN, please vote first")
        else:
            flash("Invalid VRN supplied. Please try again", "error")

    
    return render_template("vote/vote_details.html",
                            form=form,)


@vote_bp.route("voter/details/")
@login_required
@decorators.permissions_required("voters")
def voter_summary():
    title = "Voter's Details"
    btn_data = {
        "text" : "Vote",
        "attribs" : {
            "href" : url_for("vote.poll"),
            },
        "class" : "btn-success btn-sm",
        "icon" : "fa fa-poll",
    }


    voter = current_user if not session.get('candidate') \
        else current_user.user_data
    
    details = {
        "head": voter.full_name.upper(),
        "body": [
            Markup(f"{voter.id_number}"),
            Markup(f"<b>Reference Number:</b><br/>{voter.vrn.vrn}"),
        ],
        "dp_name": voter.dp_fname,

    }

    return render_template("vote/summary.html", 
                            title=title, 
                            btn=btn_data,
                            details = details)

@vote_bp.route("poll/", methods=["GET", "POST"])
@login_required
@decorators.permissions_required("voters")
def poll():
    voter = current_user if not session.get('candidate') \
        else current_user.user_data

    data = []
    posts = Posts.query.order_by(desc(Posts.payment)).all()
    candidates = Candidates.query.all() # TODO: FILTER BY REGISTRATION STATUS
    
    voting_datetime = Preferences.query.first()
 
    if not voting_datetime:
        flash("Sorry! you can't vote yet. Contact your Administrator for voting date/time", "error")
        return redirect(url_for('main.voters_profile'))
    else:
        if voting_datetime.voting_start and voting_datetime.voting_end:
            d1 = utils.datetime_digitavote(voting_datetime.voting_end)
        else:
            flash("Sorry! you can't vote yet. Contact your Administrator for voting date/time", "error")
            return redirect(url_for('main.voters_profile'))



    for post in posts:
        temp = {}
        temp["data"] = {"name": post.post_name.upper(),
                        "post-id": f"post-{post.id}",
                        }

        temp["candidates"] = [{"name": c.user_data.full_name,
                                "agenda": c.agenda,
                                "nick_name": c.nick_name,
                                "tag_name": c.tag_name,
                                "id_number": c.id_number,
                                "dp": c.user_data.dp_fname,  
                                } for c in candidates if c.post_apply == post.id]
        if temp['candidates']:
            data.append(temp)


    votes_by_user = Votes.query.filter_by(vote_by = voter.id_number).all()
    if votes_by_user and len(votes_by_user) ==  len(data):
        flash("Invalid request, you can't vote twice", "error")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        form = request.form
        votes = []
        
        try:
            for key, value in form.items():
                if key.startswith("post"):
                    post_id = int(key.split("-")[1])
                    for p in posts:
                        if p.id == post_id:
                            post = p
                            break

                    for c in candidates:
                        if c.id_number == value:
                            candidate = c
                            break
                    

                    vote = Votes(
                        vrn = voter.vrn,
                        post = post,
                        voter = voter,
                        candidate = candidate,
                    )

                    votes.append(vote)

            if len(votes) != len(data):
                raise ValueError("")

            db.session.add_all(votes)
            db.session.commit()

        except ValueError as e:
            flash("Error occurred while processing your votes. Kindly pick a candidate from each group", "error")
        except:
            flash("Error occurred while processing your votes. Please try again", "error")
        
        else:
            session["vote_completed"]  = True
            return redirect(url_for('vote.vote_summary'))




    return render_template("vote/poll.html",
                            voter=voter,
                            data=data,
                            voting_datetime=d1,
                            )



@vote_bp.route("summary/")
@login_required
@decorators.permissions_required("voters")
def vote_summary():

    if not session.get("vote_completed"):
        flash("Invalid request, you can't access that page", "error")
        return redirect(url_for("main.index"))
        
    title = "Vote Summary"
    voter = current_user if not session.get('candidate') \
        else current_user.user_data
    details = {
        "head": Markup('<span class="text-success">THANK YOU</span>'),
        "body": [
            Markup(f"Your vote has been processed."),
            Markup(f"<b>Reference Number:</b><br/>{voter.vrn.vrn}"),
        ],
        "dp_name": voter.dp_fname,

    }
    return render_template("vote/summary.html", 
                            title=title,
                            details = details)


@vote_bp.before_request
def cleaner():
    if request.url == url_for("vote.live_view", _external=True):
        pass
    elif not current_user.is_authenticated or session.get("admin"):
        flash("Please make sure you're logged in with the right permissions in order to view that page", "error")
        if 'admin' in session:
            return redirect(url_for("dashboard.dashboard"))
        else:
            return redirect(url_for("main.index"))
    else:
        voter = current_user if not session.get('candidate') \
            else current_user.user_data
        
        if not voter.has_vrn():
            voter.create_vrn()