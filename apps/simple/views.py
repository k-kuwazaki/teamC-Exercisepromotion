from flask import Blueprint, render_template, session

simple = Blueprint("simple", __name__, template_folder="templates", static_folder="static", url_prefix="/simple")


@simple.route("/")
def index():
    session.pop("selected_exercises", None)
    session.pop("selected_plan_conditions", None)
    session.pop("implementation_result", None)
    session.pop("plan_options", None)
    session.pop("plan_conditions", None)
    return render_template("simple/simple_index.html")