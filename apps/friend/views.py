
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from apps.app import db
from apps.friend.forms import FriendActionForm
from apps.friend.models import Friend
from apps.user.models import User


friend = Blueprint(
    "friend",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/friends",
)


@friend.before_request
def load_current_user():
    try:
        user_id = int(session.get("user_id"))
    except (TypeError, ValueError):
        user_id = None

    g.friend_user = db.session.get(User, user_id) if user_id is not None else None


def _current_user_for_action():
    if g.friend_user is None:
        flash("操作するユーザー情報がありません。", "error")
        return None
    return g.friend_user


def _related_user_requests(friend_requests, user_id_attribute):
    user_ids = [getattr(item, user_id_attribute) for item in friend_requests]
    users = {
        user.id: user
        for user in User.query.filter(User.id.in_(user_ids)).all()
    }
    return [
        {"id": item.id, "username": users[getattr(item, user_id_attribute)].username}
        for item in friend_requests
        if getattr(item, user_id_attribute) in users
    ]


def _action_form_is_valid():
    if FriendActionForm().validate_on_submit():
        return True

    flash("操作を確認できませんでした。もう一度お試しください。", "error")
    return False


@friend.route("/")
def index():
    friends = []
    if g.friend_user is not None:
        user_id = g.friend_user.id
        relationships = Friend.query.filter(
            Friend.status == "accepted",
            or_(Friend.requester_id == user_id, Friend.addressee_id == user_id),
        ).all()
        friend_ids = [
            item.addressee_id if item.requester_id == user_id else item.requester_id
            for item in relationships
        ]
        friends = (
            User.query.filter(User.id.in_(friend_ids))
            .order_by(User.username)
            .all()
            if friend_ids
            else []
        )
    return render_template(
        "friend/friend.html",
        friends=friends,
        action_form=FriendActionForm(),
    )


@friend.route("/search")
def search():
    user_id = g.friend_user.id if g.friend_user is not None else None
    query = request.args.get("q", "").strip()
    related_user_ids = set()
    if user_id is not None:
        relationships = Friend.query.filter(
            or_(Friend.requester_id == user_id, Friend.addressee_id == user_id)
        ).all()
        related_user_ids = {
            item.addressee_id if item.requester_id == user_id else item.requester_id
            for item in relationships
        }

    search_results = []
    if query:
        users_query = User.query.filter(User.username.ilike(f"%{query}%"))
        if user_id is not None:
            users_query = users_query.filter(User.id != user_id)
        if related_user_ids:
            users_query = users_query.filter(~User.id.in_(related_user_ids))
        search_results = (
            users_query.order_by(User.username).limit(50).all()
        )

    return render_template(
        "friend/search.html",
        query=query,
        search_results=search_results,
        action_form=FriendActionForm(),
    )


@friend.route("/requests/<int:target_user_id>", methods=["POST"])
def send_request(target_user_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.search"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.search"))

    target = db.session.get(User, target_user_id)
    if target is None:
        abort(404)
    if target.id == actor.id:
        flash("自分自身には友達申請できません。", "error")
        return redirect(url_for("friend.search"))

    existing = Friend.query.filter(
        or_(
            (Friend.requester_id == actor.id)
            & (Friend.addressee_id == target.id),
            (Friend.requester_id == target.id)
            & (Friend.addressee_id == actor.id),
        )
    ).first()

    if existing is not None:
        if existing.status == "accepted":
            flash("このユーザーとはすでにフレンドです。", "info")
        elif existing.requester_id == target.id:
            existing.status = "accepted"
            db.session.commit()
            flash(f"{target.username}さんからの申請を承認しました。", "success")
            return redirect(url_for("friend.index"))
        else:
            flash("このユーザーにはすでに申請しています。", "info")
        return redirect(url_for("friend.search", q=request.args.get("q", "")))

    db.session.add(
        Friend(
            requester_id=actor.id,
            addressee_id=target.id,
            status="pending",
        )
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = Friend.query.filter(
            or_(
                (Friend.requester_id == actor.id)
                & (Friend.addressee_id == target.id),
                (Friend.requester_id == target.id)
                & (Friend.addressee_id == actor.id),
            )
        ).first()
        if existing is None:
            raise

        if existing.status == "accepted":
            flash("このユーザーとはすでにフレンドです。", "info")
        elif existing.requester_id == target.id:
            existing.status = "accepted"
            db.session.commit()
            flash(f"{target.username}さんからの申請を承認しました。", "success")
            return redirect(url_for("friend.index"))
        else:
            flash("このユーザーにはすでに申請しています。", "info")
        return redirect(url_for("friend.search", q=request.args.get("q", "")))

    flash(f"{target.username}さんに友達申請を送りました。", "success")
    return redirect(url_for("friend.search", q=request.args.get("q", "")))


@friend.route("/incoming")
def incoming():
    incoming_requests = (
        Friend.query.filter_by(
            addressee_id=g.friend_user.id,
            status="pending",
        ).order_by(Friend.id.desc()).all()
        if g.friend_user is not None
        else []
    )
    return render_template(
        "friend/incoming.html",
        incoming_requests=_related_user_requests(
            incoming_requests, "requester_id"
        ),
        action_form=FriendActionForm(),
    )


@friend.route("/requests/<int:request_id>/accept", methods=["POST"])
def accept_request(request_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.incoming"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.incoming"))

    friend_request = Friend.query.filter_by(
        id=request_id,
        addressee_id=actor.id,
        status="pending",
    ).first_or_404()
    friend_request.status = "accepted"
    db.session.commit()
    flash("友達申請を承認しました。", "success")
    return redirect(url_for("friend.index"))


@friend.route("/requests/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.incoming"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.incoming"))

    friend_request = Friend.query.filter_by(
        id=request_id,
        addressee_id=actor.id,
        status="pending",
    ).first_or_404()
    db.session.delete(friend_request)
    db.session.commit()
    flash("友達申請を拒否しました。", "success")
    return redirect(url_for("friend.incoming"))


@friend.route("/pending")
def pending():
    pending_requests = (
        Friend.query.filter_by(
            requester_id=g.friend_user.id,
            status="pending",
        ).order_by(Friend.id.desc()).all()
        if g.friend_user is not None
        else []
    )
    return render_template(
        "friend/pending.html",
        pending_requests=_related_user_requests(
            pending_requests, "addressee_id"
        ),
        action_form=FriendActionForm(),
    )


@friend.route("/requests/<int:request_id>/cancel", methods=["POST"])
def cancel_request(request_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.pending"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.pending"))

    friend_request = Friend.query.filter_by(
        id=request_id,
        requester_id=actor.id,
        status="pending",
    ).first_or_404()
    db.session.delete(friend_request)
    db.session.commit()
    flash("友達申請を取り消しました。", "success")
    return redirect(url_for("friend.pending"))


@friend.route("/<int:friend_user_id>/remove", methods=["POST"])
def remove_friend(friend_user_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.index"))

    relationship = Friend.query.filter(
        Friend.status == "accepted",
        or_(
            (Friend.requester_id == actor.id)
            & (Friend.addressee_id == friend_user_id),
            (Friend.requester_id == friend_user_id)
            & (Friend.addressee_id == actor.id),
        ),
    ).first_or_404()
    db.session.delete(relationship)
    db.session.commit()
    flash("フレンドを解除しました。", "success")
    return redirect(url_for("friend.index"))


