# 🎯 AI Interview Coach

An AI-powered mock interview platform that generates personalized interview questions, evaluates answers in real-time, and tracks your progress over time.

**Live Demo:** [Click here to try the app](https://ai-interview-coach-9jmaema5qgzthtotl2ssh9.streamlit.app/)

## ✨ Features

- **6 Interview Tracks** — AIML Engineer, Java Developer, DSA, OOPs, DBMS, Resume-Based
- **AI-Generated Questions** — Fresh questions every session using Groq LLM
- **Real-time Evaluation** — Scored on Correctness, Depth, and Clarity
- **Semantic Similarity** — Uses sentence-transformers to measure answer quality
- **Resume-Based Interview** — Upload your resume for personalized questions
- **Progress Tracking** — Dashboard with topic-wise performance charts
- **Weak Area Practice** — Targeted sessions based on your weak topics
- **User Accounts** — Login/signup with session history saved to database

## 📊 How It Works

1. **Select a track** or upload your resume
2. **Answer 7 questions** of mixed difficulty (Basic / Intermediate / Advanced)
3. **Get instant feedback** — scores, missing points, suggested answer
4. **View your report** — overall score, strengths, weak areas, topic chart
5. **Practice weak areas** — targeted follow-up sessions
6. **Track history** — all sessions saved to your profile

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq API (llama-3.3-70b-versatile) |
| NLP | sentence-transformers (all-MiniLM-L6-v2) |
| Database | SQLite |
| PDF Parsing | pdfplumber |
| Charts | Plotly |
| Auth | bcrypt |

## 🤖 AI/ML Components

- **Semantic Similarity** — Compares student answer with ideal answer using cosine similarity
- **LLM Evaluation** — Groq LLM scores answers on correctness, depth, and clarity
- **Question Generation** — Dynamic question generation per role and difficulty level
- **Skill Gap Detection** — Identifies weak topics from scores and targets them next session
- **Resume Parsing** — Extracts skills and projects from PDF to generate personalized questions

## 🚀 How to Run

1. Clone the repository
2. Install dependencies:
```bash
   pip install -r requirements.txt
```
3. Add your Groq API key in `modules/feedback.py` and `modules/resume_parser.py`
4. Run the app:
```bash
   streamlit run app.py
```

## 📁 Project Structure

## 👩‍💻 Author

**Oishi Bhattacharya**
- GitHub: [@oishi503](https://github.com/oishi503)
- Institute of Engineering and Management, Kolkata
