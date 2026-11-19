from flask import Blueprint, render_template, redirect, url_for, session
from functools import wraps
from datetime import date,timedelta
from flask import session
from apps.app import db
from apps.situation.models import Situation
from sqlalchemy import func
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
    # 未登録の運動メニューと実施途中のデータを破棄
    session.pop("selected_exercises", None)
    session.pop("selected_plan_conditions", None)
    session.pop("implementation_result", None)

    today_date = date.today()
    week_start = today_date - timedelta(days=today_date.weekday())

    exercise_records = (
        Situation.query
        .filter_by(
            user_id=session["user_id"],
            kind="registration",
        )
        .filter(func.date(Situation.created_at) >= week_start.isoformat())
        .filter(func.date(Situation.created_at) <= today_date.isoformat())
        .all()
    )

    today_records = [
        record
        for record in exercise_records
        if record.created_at.date() == today_date
    ]

    today_minutes = sum(
        int(record.duration)
        for record in today_records
        if record.duration and record.duration.isdigit()
    )

    today_input = bool(today_records)
    week_days = len({
        record.created_at.date()
        for record in exercise_records
    })

    return render_template(
        "home/index.html",
        today_minutes=today_minutes,
        today_input=today_input,
        week_days=week_days,
    )

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

@home.route("/test")
@login_required
def test():
    return render_template("test/test.html")