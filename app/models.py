
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    account = relationship(
        "Account",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    records = relationship(
        "Record",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    records = relationship(
        "Record",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    balance = db.Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    user = relationship(
        "User",
        back_populates="account",
    )


class Record(db.Model):
    __tablename__ = "records"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category_id = db.Column(
        db.Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    amount = db.Column(
        Numeric(12, 2),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="records",
    )

    category = relationship(
        "Category",
        back_populates="records",
    )
