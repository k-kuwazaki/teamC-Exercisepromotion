from flask import Blueprint, render_template
#各種リンク先は後々それ用のファイルに移動させる
body_input = Blueprint("body_input", __name__, template_folder="templates", static_folder="static")


# トップページ
@body_input.route("/")
def index():
    return render_template("home/index.html")

