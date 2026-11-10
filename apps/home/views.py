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
    return render_template("goal/goal.html")


# AIチャット画面
@home.route("/chat")
def chat():
    return render_template("chat/chat.html")



# 履歴機能
@home.route("/history")
def history():
    return render_template("history/history.html")


# 身体情報入力・おなおし
@home.route("/body-input")
def body_input():
    return render_template("body_input/body_input.html")


# フレンド機能
@home.route("/friend")
def friend():
    return render_template("friend/friend.html")

# 運動実施
@home.route("/implementation")
def implementation():
    return render_template("implementation/implementation.html")

# ヘルプ・使い方
@home.route("/help")
def help():
    return render_template("help/help.html")

@home.route("/register")
def register():
    return render_template("register/register.html")

