import json
import re
from groq import Groq

import os
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_feedback(question: str, ideal_answer: str, student_answer: str, similarity_score: float) -> dict:
    prompt = f"""You are a technical interviewer. Evaluate this answer.

Q: {question}
Expected: {ideal_answer}
Student: {student_answer}
Similarity: {similarity_score}/10

Rules:
- CODE questions (output/bug/what does this do): short correct answer = full marks. Never penalize for missing explanation.
- THEORY questions: score on accuracy, depth, clarity.
- Correctness: factual accuracy only. Correct in different words = high score. Min 7 if core concept is right.
- Depth: short=1-4, covers main points=5-7, detailed with examples=8-10. CODE questions: full marks if correct.
- Clarity: confusing=1-4, ok=5-7, clear and structured=8-10
- Overall = (correctness*0.4 + depth*0.4 + clarity*0.2), calculate exactly
- missing_points: only GENUINELY missing points. Never list "explanation" for code questions. Empty list only if score=10.
- suggested_answer: write as one line only, use | as separator between points instead of newlines.

Return JSON only. All values must be on a single line. No line breaks inside any string value:
{{"correctness_score":int,"depth_score":int,"clarity_score":int,"missing_points":["..."],"suggested_answer":"...","overall_score":int}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        # Remove all control characters and fix newlines
        text = re.sub(r'[\x00-\x1f\x7f]', lambda m: '\\n' if m.group() == '\n' else '', text)

        result = json.loads(text)
        return result

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response was: {text}")
        return {
            "correctness_score": 0,
            "depth_score": 0,
            "clarity_score": 0,
            "missing_points": ["Could not evaluate. Please try again."],
            "suggested_answer": ideal_answer,
            "overall_score": 0
        }
    except Exception as e:
        print(f"Groq Error: {e}")
        return {
            "correctness_score": 0,
            "depth_score": 0,
            "clarity_score": 0,
            "missing_points": ["Could not evaluate. Please try again."],
            "suggested_answer": ideal_answer,
            "overall_score": 0
        }