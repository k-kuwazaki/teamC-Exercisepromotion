from apps.app import db
from sqlalchemy import case


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