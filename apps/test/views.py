from flask import Blueprint, render_template

test = Blueprint("test", __name__, template_folder="templates", static_folder="static", url_prefix="/test")


@test.route("/")
def index():
    return render_template("test/test.html")