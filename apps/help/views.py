from flask import Blueprint, render_template

help = Blueprint("help", __name__, template_folder="templates", static_folder="static", url_prefix="/help")


@help.route("/")
def index():
    return render_template("help/help.html")