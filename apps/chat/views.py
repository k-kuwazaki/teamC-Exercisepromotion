from flask import Blueprint, render_template
#各種リンク先は後々それ用のファイルに移動させる
chat = Blueprint("chat", __name__, template_folder="templates", static_folder="static")


# トップページ
@chat.route("/")
def index():
    return render_template("home/index.html")

