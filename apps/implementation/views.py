from flask import Blueprint, render_template, session
#各種リンク先は後々それ用のファイルに移動させる
implementation = Blueprint("implementation", __name__, template_folder="templates", static_folder="static")

# トップページ
@implementation.route("/")
def index():
    return render_template("home/index.html")

# 実施登録画面
@implementation.route("/registration")
def registration():
    return render_template(
        "registration/registration.html",
        selected_exercises=session.get("selected_exercises", []),
    )
# 履歴機能
@implementation.route("/history")
def history():
    return render_template("history/history.html")
