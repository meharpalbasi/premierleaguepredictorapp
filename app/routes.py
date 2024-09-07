from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from urllib.parse import urlparse
from wtforms import RadioField
from wtforms.validators import DataRequired
from . import db
from .models import User, Prediction, Match, Question
from .forms import RegistrationForm, LoginForm, PredictionForm, QuestionForm  # We'll create this form next
from sqlalchemy.exc import IntegrityError

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html', title='Home')

@main.route('/predictions', methods=['GET', 'POST'])
@login_required
def predictions():
    current_week = get_current_week()
    
    # Check if the user has already made predictions for this week
    existing_prediction = Prediction.query.filter_by(user_id=current_user.id, week=current_week).first()
    if existing_prediction:
        flash('You have already entered predictions for this week.')
        return redirect(url_for('main.index'))
    
    questions = Question.query.filter_by(week=current_week).all()
    # Dynamically create a form class with fields for each question
    class DynamicPredictionForm(FlaskForm):
        pass
    for question in questions:
        form_field_name = f"question_{question.id}"
        setattr(DynamicPredictionForm, form_field_name, RadioField(
            label=question.text,
            choices=[('over', 'Over'), ('under', 'Under')],
            validators=[DataRequired()]
        ))
    # Instantiate the dynamically created form
    form = DynamicPredictionForm()
    if form.validate_on_submit():
        try:
            for question in questions:
                form_field_name = f"question_{question.id}"
                answer = getattr(form, form_field_name).data
                prediction = Prediction(
                    user_id=current_user.id,
                    question_id=question.id,
                    answer=answer,
                    week=current_week
                )
                db.session.add(prediction)
            db.session.commit()
            flash('Your predictions have been submitted!')
            return redirect(url_for('main.index'))
        except IntegrityError:
            db.session.rollback()
            flash('You have already entered predictions for this week.')
            return redirect(url_for('main.index'))
    return render_template('predictions.html', form=form)

@main.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.order_by(User.score.desc()).limit(10).all()
    
    # Get the current user's predictions for the current week
    current_week = get_current_week()
    user_predictions = Prediction.query.filter_by(user_id=current_user.id, week=current_week).all()
    
    # Create a list of dictionaries containing question text and user's answer
    predictions_data = []
    for prediction in user_predictions:
        question = Question.query.get(prediction.question_id)
        predictions_data.append({
            'question': question.text,
            'answer': prediction.answer,
            'is_correct': prediction.is_correct
        })
    
    return render_template('leaderboard.html', users=users, predictions=predictions_data)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)  # This hashes the password
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# You'll need to implement these helper functions
def get_current_week():
    return 3
    # Logic to determine the current Premier League week
    #pass

def update_scores():
    # Logic to update user scores based on their predictions
    pass

@main.route('/test')
def test():
    return "Hello, World!"

@main.route('/debug/users')
def debug_users():
    users = User.query.all()
    return render_template('debug_table.html', items=users, title="Users")

@main.route('/debug/predictions')
def debug_predictions():
    predictions = Prediction.query.all()
    return render_template('debug_table.html', items=predictions, title="Predictions")

@main.route('/debug/questions')
def debug_questions():
    questions = Question.query.all()
    return render_template('debug_table.html', items=questions, title="Questions")

@main.route('/debug/matches')
def debug_matches():
    matches = Match.query.all()
    return render_template('debug_table.html', items=matches, title="Matches")

from app.models import Prediction, Question, Match
from app import db

def update_prediction_results():
    with current_app.app_context():
        # Get all predictions that haven't been marked as correct or incorrect yet
        pending_predictions = Prediction.query.filter_by(is_correct=None).all()

        for prediction in pending_predictions:
            question = Question.query.get(prediction.question_id)
            match = Match.query.filter_by(week=prediction.week).first()

            if match and match.is_finished:
                # Logic to determine if the prediction is correct
                if question.text.startswith("Will"):
                    actual_goals = match.home_team_goals if "home team" in question.text else match.away_team_goals
                    predicted_over = prediction.answer == 'over'
                    threshold = float(question.text.split()[-2])

                    prediction.is_correct = (actual_goals > threshold) == predicted_over
                
                db.session.add(prediction)

        db.session.commit()
        print(f"Updated {len(pending_predictions)} predictions.")

@main.route('/update_results', methods=['POST'])
@login_required
def update_results():
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        update_prediction_results()
        update_user_scores()
        flash('Prediction results have been updated.')
    else:
        flash('You do not have permission to perform this action.')
    return redirect(url_for('main.index'))

def update_user_scores():
    with current_app.app_context():
        users = User.query.all()
        for user in users:
            correct_predictions = Prediction.query.filter_by(user_id=user.id, is_correct=True).count()
            user.score = correct_predictions
        db.session.commit()
        print(f"Updated scores for {len(users)} users.")

# Remove this line as it's causing the context issue:
# update_user_scores()

@main.route('/admin/update_results', methods=['GET', 'POST'])
@login_required
def admin_update_results():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))

    # Get all available weeks
    available_weeks = db.session.query(Question.week.distinct()).order_by(Question.week).all()
    available_weeks = [week[0] for week in available_weeks]

    # Get the selected week from the query parameter, default to the latest week
    selected_week = request.args.get('week', type=int, default=max(available_weeks))

    # Get questions for the selected week
    questions = Question.query.filter_by(week=selected_week).order_by(Question.id).all()

    if request.method == 'POST':
        for question in questions:
            result = request.form.get(f'question_{question.id}')
            if result:
                # Update the question's result
                question.result = result
        
        db.session.commit()
        update_prediction_results()
        update_user_scores()
        flash('Results have been updated successfully.')
        return redirect(url_for('main.admin_update_results', week=selected_week))

    return render_template('admin_update_results.html', questions=questions, selected_week=selected_week, available_weeks=available_weeks)

# Update these existing functions
def update_prediction_results():
    predictions = Prediction.query.filter_by(is_correct=None).all()
    for prediction in predictions:
        if prediction.question.result:
            prediction.is_correct = prediction.answer == prediction.question.result
    db.session.commit()

def update_user_scores():
    users = User.query.all()
    for user in users:
        correct_predictions = Prediction.query.filter_by(user_id=user.id, is_correct=True).count()
        user.score = correct_predictions
    db.session.commit()

@main.route('/admin/add_question', methods=['GET', 'POST'])
@login_required
def admin_add_question():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))

    form = QuestionForm()
    if form.validate_on_submit():
        new_question = Question(text=form.text.data, week=form.week.data)
        db.session.add(new_question)
        db.session.commit()
        flash('New question added successfully.')
        return redirect(url_for('main.admin_add_question'))

    return render_template('admin_add_question.html', form=form)

@main.route('/admin/manage_questions', methods=['GET', 'POST'])
@login_required
def admin_manage_questions():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))

    form = QuestionForm()
    if form.validate_on_submit():
        if form.question_id.data:
            # Modify existing question
            question = Question.query.get(form.question_id.data)
            if question:
                question.text = form.text.data
                question.week = form.week.data
                db.session.commit()
                flash('Question updated successfully.')
            else:
                flash('Question not found.')
        else:
            # Add new question
            new_question = Question(text=form.text.data, week=form.week.data)
            db.session.add(new_question)
            db.session.commit()
            flash('New question added successfully.')
        return redirect(url_for('main.admin_manage_questions'))

    questions = Question.query.order_by(Question.week, Question.id).all()
    return render_template('admin_manage_questions.html', form=form, questions=questions)

@main.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@login_required
def admin_delete_question(question_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))

    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully.')
    else:
        flash('Question not found.')
    return redirect(url_for('main.admin_manage_questions'))
