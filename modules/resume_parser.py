import pdfplumber
import json
from groq import Groq
import os

import os
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(uploaded_file) -> str:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_skills_and_generate_questions(resume_text: str) -> dict:
    prompt = f"""
You are an expert technical interviewer. Analyze the resume below and extract key information.

Resume:
{resume_text}

Based on the resume, do two things:

1. Extract:
   - skills (programming languages, tools, frameworks)
   - projects (name and brief description)
   - certifications (if any)

2. Generate exactly 7 interview questions that are SPECIFIC to this person's resume.
   - Ask about their actual projects
   - Ask about the specific skills they mentioned
   - Ask about certifications if present
   - Make questions feel personalized, not generic

Return ONLY a valid JSON object with these exact keys:
{{
  "candidate_name": "<name from resume or Unknown>",
  "skills": [<list of skills>],
  "projects": [<list of project names>],
  "certifications": [<list of certifications>],
  "questions": [
    {{
      "topic": "<skill or project this question is about>",
      "question": "<the interview question>",
      "ideal_answer": "<what a good answer should cover>"
    }}
  ]
}}

No explanation outside the JSON. No markdown. Just the JSON object.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. Analyze the resume and generate personalized interview questions based ONLY on the skills, projects, and certifications mentioned in the resume."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        # Fix invalid control characters inside JSON strings
        import re
        text = re.sub(r'(?<!\\)\n', '\\n', text)
        text = re.sub(r'(?<!\\)\t', '\\t', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

        return json.loads(text)
    except Exception as e:
        print(f"Resume parsing error: {e}")
        return None
    
def generate_questions_for_role(role: str, weak_areas: list = None) -> list:
    import re

    if weak_areas:
        weak_areas_text = f"""
Focus MORE on these weak areas from the candidate's previous interview: {', '.join(weak_areas)}
Give 4 questions from weak areas and 3 from other topics.
"""
    else:
        weak_areas_text = ""

    if role == "Java Developer":
        snippet_instruction = """
Question mix for Java Developer:
- 2 questions: Basic Java theory (definitions, concepts)
- 2 questions: Intermediate Java theory (OOP, collections, exceptions)
- 1 question: Advanced Java theory (multithreading, Java 8+)
- 2 questions: Code snippet questions — include a short Java code block and ask ONE of these:
    * "What is the output of this code?"
    * "Find the bug in this code"
    * "What OOP concept does this code demonstrate?"

For snippet questions, put the code inside the question field using this format:
"Look at the following code:\\n\\n```java\\n<your code here>\\n```\\n\\n<your question about the code>"
"""
    elif role == "OOPs":
        snippet_instruction = """
Question mix for OOPs:
- 2 questions: Basic OOP concepts (classes, objects, encapsulation, abstraction)
- 3 questions: Intermediate OOP (inheritance, polymorphism, interfaces, abstract classes)
- 2 questions: Advanced OOP (SOLID principles, design patterns, composition vs inheritance)
"""
    elif role == "DBMS":
        snippet_instruction = """
Question mix for DBMS:
- 2 questions: Basic DBMS concepts (ACID properties, normalization, keys, indexes)
- 2 questions: Intermediate DBMS (joins, transactions, stored procedures, views)
- 2 questions: SQL scenario questions — describe a simple table and ask about a query
- 1 question: Advanced DBMS (query optimization, indexing strategies, CAP theorem)

Keep SQL examples simple and short. Do not use newlines inside query strings.
"""
    else:
        snippet_instruction = """
Question mix:
- 2 questions: Basic/Fundamental (definitions, concepts a fresher should know)
- 3 questions: Intermediate (applied knowledge, how things work)
- 2 questions: Advanced (complex scenarios, trade-offs, design decisions)
"""

    prompt = f"""
You are an expert technical interviewer conducting an interview for a {role} position.

{snippet_instruction}

{weak_areas_text}

IMPORTANT RULES:
- Each question must test a DIFFERENT subtopic
- Do not repeat similar concepts
- Keep all text on single lines inside JSON strings, use \\n for line breaks
- Do not use raw newlines or tab characters inside JSON string values

Return ONLY a valid JSON array:
[
  {{
    "topic": "<subtopic name>",
    "question": "<the interview question>",
    "ideal_answer": "<what a good answer should cover>",
    "difficulty": "<Basic/Intermediate/Advanced>"
  }}
]

No explanation outside the JSON. No markdown. Just the JSON array.
"""

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                   {
                       "role": "system",
                       "content": f"You are a technical interviewer specializing in {role}. Generate ONLY questions relevant to {role} technical concepts. Do NOT generate questions about journalism, investigative reporting, or unrelated domains. Focus purely on {role} technical knowledge."
                   },
                   {
                       "role": "user",
                       "content": prompt
                   }
                ],
                temperature=0.9
            )
            text = response.choices[0].message.content.strip()

            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            text = re.sub(r'(?<!\\)\n', '\\n', text)
            text = re.sub(r'(?<!\\)\t', '\\t', text)
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

            questions = json.loads(text)
            if questions and len(questions) > 0:
                return questions

        except Exception as e:
            print(f"Question generation error (attempt {attempt + 1}): {e}")
            continue

    return None