from app import create_app, db
from app.models import User, Prediction, Question, Match

app = create_app()

with app.app_context():
    print("Users:")
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")

    print("\nPredictions:")
    predictions = Prediction.query.all()
    for prediction in predictions:
        print(f"ID: {prediction.id}, User ID: {prediction.user_id}, Question ID: {prediction.question_id}, Answer: {prediction.answer}")

    print("\nQuestions:")
    questions = Question.query.all()
    for question in questions:
        print(f"ID: {question.id}, Text: {question.text}, Week: {question.week}")

    print("\nMatches:")
    matches = Match.query.all()
    for match in matches:
        print(f"ID: {match.id}, Home Team: {match.home_team}, Away Team: {match.away_team}, Week: {match.week}")