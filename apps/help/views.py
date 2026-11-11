from flask import Blueprint, render_template
#各種リンク先は後々それ用のファイルに移動させる
help = Blueprint("help", __name__, template_folder="templates", static_folder="static")


# トップページ
@help.route("/")
def index():
    return render_template("home/index.html")