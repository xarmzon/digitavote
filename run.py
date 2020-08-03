from flask import (
    session, 
    Markup, 
    request, 
    session, 
    url_for
)
from digitavote import create_app
from digitavote.config import DevelopmentConfig, ProductionConfig
from digitavote.models import db, Voters, OTPs, Admins, Candidates 
from digitavote import login_manager

app = create_app(DevelopmentConfig())

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Voters=Voters, OTPs=OTPs, Admins=Admins)

@login_manager.user_loader
def load_user(user_id):
    if not request.url == url_for("vote.vote_summary", _external=True):
        session.pop("vote_completed", None)

    if 'admin' in session and session["admin"] == True:
        return Admins.query.get(int(user_id))
    elif 'candidate' in session and session["candidate"] == True:
        return Candidates.query.get(int(user_id))
    else:
        return Voters.query.get(int(user_id))

#filters
@app.template_filter()
def limit_text(txt, len_= 45, read_more=None):
    if len(txt) > len_:
        if read_more:
            return txt[:len_+1] + "..."  +  \
                    Markup(f'<a href="{read_more}"> read more</a>')
        else:
            return txt[:len_+1] + "..." 
    else:
        return txt

if __name__ == "__main__":
    app.run()
#C:\Users\mr\E-VotinApp>c:\users\mr\rastademy\ven\scripts\python.exe run.py