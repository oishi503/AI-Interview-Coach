from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_similarity_score(ideal_answer: str, student_answer: str) -> float:
    if not student_answer.strip():
        return 0.0
    emb1 = model.encode(ideal_answer, convert_to_tensor=True)
    emb2 = model.encode(student_answer, convert_to_tensor=True)
    score = util.cos_sim(emb1, emb2).item()
    return round(score * 10, 2)  # Scale to /10