from app import create_app, db
from app.models import Question

app = create_app()

with app.app_context():
    # Insert a new question for the current week
    new_question = Question(text="Will Solanke score over or under 0.5 goals this game week?", week=3)  # Ensure week is not None
    db.session.add(new_question)
    
    # Insert more questions as needed
    another_question = Question(text="Will Palmer assist over or under 0.5 goals this game week?", week=3)
    db.session.add(another_question)
    
    db.session.commit()
    print("Inserted test questions into the database.")
