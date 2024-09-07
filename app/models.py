from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates
from sqlalchemy import event

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))  # Updated to store the hashed password
    score = db.Column(db.Integer, default=0)
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic')
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # Hashes the password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Checks the hashed password

from . import db


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer = db.Column(db.String(10), nullable=False)
    is_correct = db.Column(db.Boolean)
    week = db.Column(db.Integer, nullable=False)
    
    # Remove this line:
    # __table_args__ = (db.UniqueConstraint('user_id', 'week', name='uq_user_week'),)

    @validates('week')
    def validate_week(self, key, week):
        if week is None:
            if self.question:
                return self.question.week
            else:
                raise ValueError("Week must be set if question is not available")
        return week

@event.listens_for(Prediction, 'before_insert')
def set_week_from_question(mapper, connection, target):
    if target.week is None:
        if target.question_id is not None:
            # Fetch the question to get its week
            stmt = db.select(Question.week).where(Question.id == target.question_id)
            question_week = connection.scalar(stmt)
            if question_week is not None:
                target.week = question_week
            else:
                raise ValueError(f"No question found with id {target.question_id}")
        else:
            raise ValueError("question_id must be set")
        

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    predictions = db.relationship('Prediction', backref='question', lazy=True)
    result = db.Column(db.String(10))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
