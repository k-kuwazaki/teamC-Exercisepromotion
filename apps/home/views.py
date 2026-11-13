from flask import Blueprint, render_template, redirect, url_for, session
from functools import wraps

home = Blueprint(
    "home",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/home_static",
)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login.login"))
        return f(*args, **kwargs)

    return decorated


@home.route("/")
@login_required
def index():
    return render_template("home/index.html")


@home.route("/goal")
@login_required
def goal():
    return render_template("goal/goal.html")


@home.route("/chat")
@login_required
def chat():
    return render_template("chat/chat.html")


@home.route("/history")
@login_required
def history():
    return render_template("history/history.html")


@home.route("/friend")
@login_required
def friend():
    return redirect(url_for("friend.index"))


@home.route("/implementation")
@login_required
def implementation():
    return render_template("implementation/implementation.html")


@home.route("/help")
@login_required
def help():
    return render_template("help/help.html")


@home.route("/register")
def register():
    return render_template("register/register.html")
