from flask import (
    session, 
    url_for, 
    flash, 
    redirect,
)
from functools import wraps

def permissions_required(role="all"):

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if role == "all":
                return f(*args, **kwargs)
            elif role == "candidate" and role in session:
                return f(*args, **kwargs)
            elif role == "admin" and role in session:
                return f(*args, **kwargs)
            elif role =="super" and all(['admin' in session, role in session]):
                return f(*args, **kwargs)
            elif role =="voters" and any(['candidate' in session, 'voter' in session]):
                return f(*args, **kwargs)
            else:
                flash("Please make sure you're logged in with the right permissions in order to view that page", "error")
                if 'admin' in session:
                    return redirect(url_for("dashboard.dashboard"))
                else:
                    return redirect(url_for("main.index"))
        return wrapper
    return decorator
                