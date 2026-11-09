from flask import Blueprint, render_template
#各種リンク先は後々それ用のファイルに移動させる
registration = Blueprint("registration", __name__, template_folder="templates", static_folder="static")

# トップページ
@registration.route("/")
def index():
    return render_template("home/index.html")

# 振り返り
@registration.route("/lookingback")
def lookingback():
    return render_template("lookingback/lookingback.html")



