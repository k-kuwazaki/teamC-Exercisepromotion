from apps.app import db
from sqlalchemy import case
from datetime import datetime


class Friend(db.Model):
    __tablename__ = "friends"
    __table_args__ = (
        db.UniqueConstraint("requester_id", "addressee_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    addressee_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    goals = db.relationship("FriendGoal", backref="friend", lazy=True)


class FriendGoal(db.Model):
    __tablename__ = "friend_goals"

    id = db.Column(db.Integer, primary_key=True)
    friend_id = db.Column(
        db.Integer, db.ForeignKey("friends.id"), nullable=False, index=True
    )
    goal_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    status = db.Column(
        db.String(20), nullable=False, default="active", server_default="active"
    ) 
    deadline = db.Column(db.DateTime, nullable=True)
    checked_by_friend = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    

class FriendReaction(db.Model):
    __tablename__ = "friend_reactions"
    __table_args__ = (
        db.UniqueConstraint("from_user_id", "lookingback_id", "reaction_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    lookingback_id = db.Column(
        db.Integer, db.ForeignKey("lookingbacks.id"), nullable=False, index=True
    )
    reaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)


db.Index(
    "uq_friends_user_pair",
    case(
        [(Friend.requester_id < Friend.addressee_id, Friend.requester_id)],
        else_=Friend.addressee_id,
    ),
    case(
        [(Friend.requester_id < Friend.addressee_id, Friend.addressee_id)],
        else_=Friend.requester_id,
    ),
    unique=True,
)