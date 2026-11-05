from flask import Blueprint, render_template
#各種リンク先は後々それ用のファイルに移動させる
home = Blueprint("home", __name__, template_folder="templates", static_folder="static")


# トップページ
@home.route("/")
def index():
    return render_template("home/index.html")



# 目標入力画面
@home.route("/goal")
def goal():
    return render_template("home/goal.html")


# AIチャット画面
@home.route("/chat")
def chat():
    return render_template("home/chat.html")


# 履歴機能
@home.route("/history")
def history():
    return render_template("home/history.html")


# 身体情報入力・おなおし
@home.route("/body-input")
def body_input():
    return render_template("home/body_input.html")