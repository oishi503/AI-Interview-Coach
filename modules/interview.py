import json
import random

def load_questions(filepath: str, topic_filter: str = None):
    with open(filepath, "r") as f:
        questions = json.load(f)
    if topic_filter:
        questions = [q for q in questions if q["topic"] == topic_filter]
    random.shuffle(questions)
    return questions

def get_question(questions: list, index: int):
    if index < len(questions):
        return questions[index]
    return None