from datetime import date, timedelta
from functools import wraps

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func

from apps.situation.models import Situation


home = Blueprint(
    "home",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/home_static",
)


def login_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login.login"))
        return view(*args, **kwargs)

    return decorated


@home.route("/")
@login_required
def index():
    # ホームへ戻ったとき、未登録の運動内容を破棄
    session.pop("selected_exercises", None)
    session.pop("selected_plan_conditions", None)
    session.pop("implementation_result", None)
    session.pop("plan_options", None)
    session.pop("plan_conditions", None)

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

    template = (
       "simple/simple_index.html"
       if session.get("display_mode") == "simple"
       else "home/index.html"
    )

    return render_template(
        template,
        today_minutes=today_minutes,
        today_input=today_input,
        week_days=week_days,
    )


@home.route("/mode", methods=["POST"])
@login_required
def set_mode():
    session["display_mode"] = (
        "normal" if request.form.get("simple_mode") == "1" else "simple"
    )
    return redirect(url_for("home.index"))


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
    return redirect(url_for("implementation.index", source="home"))


@home.route("/help")
@login_required
def help():
    return render_template("help/help.html")


@home.route("/register")
def register():
    return render_template("register/register.html")
