
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
from apps.friend.models import Friend, FriendGoal, FriendReaction
from apps.user.models import User
from datetime import date, datetime, timedelta
from apps.lookingback.models import LookingBack
from apps.situation.models import Situation


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
    done_count = 0
    total_count = 0
    i_did_today = False

    if g.friend_user is not None:
        user_id = g.friend_user.id
        today = date.today()

        i_did_today = LookingBack.query.filter_by(
            user_id=user_id, date=today
        ).first() is not None

        relationships = Friend.query.filter(
            Friend.status == "accepted",
            or_(Friend.requester_id == user_id, Friend.addressee_id == user_id),
        ).all()
        friend_ids = [
            item.addressee_id if item.requester_id == user_id else item.requester_id
            for item in relationships
        ]
        if friend_ids:
            done_today_map = {
                r.user_id: r
                for r in LookingBack.query.filter(
                    LookingBack.user_id.in_(friend_ids),
                    LookingBack.date == today,
                ).all()
            }

            # 今日のlookingback_idに対して自分が送ったリアクションを取得
            today_lookingback_ids = [r.id for r in done_today_map.values()]
            my_reactions = set()
            if today_lookingback_ids:
                my_reactions = {
                    (r.lookingback_id, r.reaction_type)
                    for r in FriendReaction.query.filter(
                        FriendReaction.from_user_id == user_id,
                        FriendReaction.lookingback_id.in_(today_lookingback_ids),
                    ).all()
                }

            # フレンドの各記録に対するリアクション集計
            reaction_counts = {}
            if today_lookingback_ids:
                for r in FriendReaction.query.filter(
                    FriendReaction.lookingback_id.in_(today_lookingback_ids)
                ).all():
                    key = (r.lookingback_id, r.reaction_type)
                    reaction_counts[key] = reaction_counts.get(key, 0) + 1

            latest_situations = {}
            for s in (
                Situation.query
                .filter(
                    Situation.user_id.in_(friend_ids),
                    Situation.kind == "registration",
                )
                .order_by(Situation.created_at.desc())
                .all()
            ):
                if s.user_id not in latest_situations:
                    latest_situations[s.user_id] = s

            friend_users = (
                User.query.filter(User.id.in_(friend_ids))
                .order_by(User.username)
                .all()
            )
            friends = sorted(
                [
                    {
                        "user": u,
                        "done_today": u.id in done_today_map,
                        "lookingback": done_today_map.get(u.id),
                        "latest_situation": latest_situations.get(u.id),
                        "my_reactions": my_reactions,
                        "reaction_counts": reaction_counts,
                    }
                    for u in friend_users
                ],
                key=lambda x: x["done_today"],
                reverse=True,
            )
            total_count = len(friends)
            done_count = sum(1 for f in friends if f["done_today"])

    return render_template(
        "friend/friend.html",
        friends=friends,
        action_form=FriendActionForm(),
        done_count=done_count,
        total_count=total_count,
        i_did_today=i_did_today,
    )


@friend.route("/search")
def search():
    user_id = g.friend_user.id if g.friend_user is not None else None
    habit = request.args.get("habit", "").strip()
    goal_keyword = request.args.get("goal", "").strip()
    username = request.args.get("username", "").strip()

    related_user_ids = set()
    if user_id is not None:
        relationships = Friend.query.filter(
            or_(Friend.requester_id == user_id, Friend.addressee_id == user_id)
        ).all()
        related_user_ids = {
            item.addressee_id if item.requester_id == user_id else item.requester_id
            for item in relationships
        }

    users_query = User.query
    if user_id is not None:
        users_query = users_query.filter(User.id != user_id)
    if related_user_ids:
        users_query = users_query.filter(~User.id.in_(related_user_ids))
    if habit:
        users_query = users_query.filter(User.exercise_habit == habit)
    if goal_keyword:
        users_query = users_query.filter(User.goal.ilike(f"%{goal_keyword}%"))
    if username:
        users_query = users_query.filter(User.username.ilike(f"%{username}%"))

    search_results = users_query.order_by(User.username).limit(50).all()

    # オンライン状態の判定
    now = datetime.now()
    online_threshold = now - timedelta(minutes=5)

    for user in search_results:
        user.is_online = (
            user.last_seen is not None
            and user.last_seen >= online_threshold
        )
    
    return render_template(
        "friend/search.html",
        habit=habit,
        username=username,
        goal_keyword=goal_keyword,
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
        return redirect(url_for("friend.search", habit=request.args.get("habit", ""), goal=request.args.get("goal", ""), username=request.args.get("username", "")))

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
        return redirect(url_for("friend.search", habit=request.args.get("habit", ""), goal=request.args.get("goal", ""), username=request.args.get("username", "")))

    flash(f"{target.username}さんに友達申請を送りました。", "success")
    return redirect(url_for("friend.search", habit=request.args.get("habit", ""), goal=request.args.get("goal", ""), username=request.args.get("username", "")))


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


@friend.route("/reactions/<int:lookingback_id>/<reaction_type>", methods=["POST"])
def send_reaction(lookingback_id, reaction_type):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.index"))

    if reaction_type not in ("like",):
        abort(400)

    lookingback = LookingBack.query.get_or_404(lookingback_id)

    # フレンドの記録かどうか確認
    relationship = _get_active_friend_relationship(actor.id, lookingback.user_id)
    if relationship is None:
        abort(403)

    # 重複チェック
    existing = FriendReaction.query.filter_by(
        from_user_id=actor.id,
        lookingback_id=lookingback_id,
        reaction_type=reaction_type,
    ).first()
    if existing is None:
        db.session.add(FriendReaction(
            from_user_id=actor.id,
            lookingback_id=lookingback_id,
            reaction_type=reaction_type,
        ))
        db.session.commit()

    return redirect(url_for("friend.index"))


def _get_active_friend_relationship(actor_id, friend_user_id):
    return Friend.query.filter(
        Friend.status == "accepted",
        or_(
            (Friend.requester_id == actor_id) & (Friend.addressee_id == friend_user_id),
            (Friend.requester_id == friend_user_id) & (Friend.addressee_id == actor_id),
        ),
    ).first()


def _calc_deadline(choice):
    now = datetime.now()
    if choice == "today":
        return now.replace(hour=23, minute=59, second=59, microsecond=0)
    if choice == "week":
        days_until_sunday = 6 - now.weekday() if now.weekday() != 6 else 0
        return (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59, microsecond=0)
    if choice == "month":
        next_month = now.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day
        return now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
    return None


@friend.route("/<int:friend_user_id>/goals")
def goal_index(friend_user_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    friend_user = db.session.get(User, friend_user_id)
    if friend_user is None:
        abort(404)

    goal = FriendGoal.query.filter(
        FriendGoal.friend_id == relationship.id,
        FriendGoal.status.in_(["active", "pending"]),
    ).first()

    past_goals = FriendGoal.query.filter(
        FriendGoal.friend_id == relationship.id,
        FriendGoal.status.in_(["achieved", "failed"]),
    ).order_by(FriendGoal.created_at.desc()).all()

    return render_template(
        "friend/goal.html",
        friend_user=friend_user,
        relationship=relationship,
        goal=goal,
        past_goals=past_goals,
        actor=actor,
        action_form=FriendActionForm(),
    )


@friend.route("/<int:friend_user_id>/goals/new", methods=["GET", "POST"])
def goal_new(friend_user_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    existing = FriendGoal.query.filter(
        FriendGoal.friend_id == relationship.id,
        FriendGoal.status.in_(["active", "pending"]),
    ).first()
    if existing is not None:
        flash("現在進行中の目標があります。達成または未達成にしてから新しい目標を作成してください。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    if request.method == "POST":
        if not FriendActionForm().validate_on_submit():
            flash("操作を確認できませんでした。もう一度お試しください。", "error")
            return redirect(url_for("friend.goal_new", friend_user_id=friend_user_id))

        goal_type = request.form.get("goal_type")
        content = request.form.get("content", "").strip()
        deadline_choice = request.form.get("deadline", "")

        if goal_type not in ("shared", "declaration", "promise"):
            flash("目標タイプを選択してください。", "error")
            return redirect(url_for("friend.goal_new", friend_user_id=friend_user_id))
        if not content:
            flash("目標内容を入力してください。", "error")
            return redirect(url_for("friend.goal_new", friend_user_id=friend_user_id))

        status = "pending" if goal_type == "promise" else "active"
        deadline = _calc_deadline(deadline_choice)

        db.session.add(FriendGoal(
            friend_id=relationship.id,
            goal_type=goal_type,
            content=content,
            created_by=actor.id,
            status=status,
            deadline=deadline,
        ))
        db.session.commit()
        flash("目標を作成しました。", "success")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    friend_user = db.session.get(User, friend_user_id)
    return render_template(
        "friend/goal_new.html",
        friend_user=friend_user,
        action_form=FriendActionForm(),
    )


@friend.route("/<int:friend_user_id>/goals/<int:goal_id>/promise_accept", methods=["POST"])
def goal_promise_accept(friend_user_id, goal_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    goal = FriendGoal.query.filter_by(
        id=goal_id, friend_id=relationship.id, status="pending"
    ).first_or_404()

    if goal.created_by == actor.id:
        flash("自分が作成した約束は自分で承認できません。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    goal.status = "active"
    db.session.commit()
    flash("約束を承認しました。", "success")
    return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))


@friend.route("/<int:friend_user_id>/goals/<int:goal_id>/promise_reject", methods=["POST"])
def goal_promise_reject(friend_user_id, goal_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    goal = FriendGoal.query.filter_by(
        id=goal_id, friend_id=relationship.id, status="pending"
    ).first_or_404()

    if goal.created_by == actor.id:
        flash("自分が作成した約束は自分で拒否できません。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    db.session.delete(goal)
    db.session.commit()
    flash("約束を拒否しました。", "success")
    return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))


@friend.route("/<int:friend_user_id>/goals/<int:goal_id>/check", methods=["POST"])
def goal_check(friend_user_id, goal_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    goal = FriendGoal.query.filter_by(
        id=goal_id, friend_id=relationship.id, status="active", goal_type="declaration"
    ).first_or_404()

    if goal.created_by == actor.id:
        flash("自分の宣言は自分でチェックできません。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    goal.checked_by_friend = True
    db.session.commit()
    flash("達成を確認しました。", "success")
    return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))


@friend.route("/<int:friend_user_id>/goals/<int:goal_id>/achieve", methods=["POST"])
def goal_achieve(friend_user_id, goal_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    goal = FriendGoal.query.filter_by(
        id=goal_id, friend_id=relationship.id, status="active"
    ).first_or_404()

    if goal.created_by != actor.id:
        flash("目標の達成は作成者のみ記録できます。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    if goal.goal_type == "declaration" and not goal.checked_by_friend:
        flash("フレンドのチェックが必要です。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    goal.status = "achieved"
    db.session.commit()
    flash("目標を達成しました！おめでとうございます🎉", "success")
    return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))


@friend.route("/<int:friend_user_id>/goals/<int:goal_id>/fail", methods=["POST"])
def goal_fail(friend_user_id, goal_id):
    actor = _current_user_for_action()
    if actor is None:
        return redirect(url_for("friend.index"))
    if not _action_form_is_valid():
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    relationship = _get_active_friend_relationship(actor.id, friend_user_id)
    if relationship is None:
        abort(404)

    goal = FriendGoal.query.filter_by(
        id=goal_id, friend_id=relationship.id, status="active"
    ).first_or_404()

    if goal.created_by != actor.id:
        flash("目標の未達成記録は作成者のみできます。", "error")
        return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))

    goal.status = "failed"
    db.session.commit()
    flash("目標を未達成として記録しました。次は頑張りましょう！", "success")
    return redirect(url_for("friend.goal_index", friend_user_id=friend_user_id))
