import plotly.graph_objects as go

def compute_topic_averages(session_results: list) -> dict:
    topic_scores = {}
    for result in session_results:
        topic = result["topic"]
        score = result["overall_score"]
        topic_scores.setdefault(topic, []).append(score)
    return {topic: round(sum(scores)/len(scores), 1) for topic, scores in topic_scores.items()}

def get_strengths_and_weaknesses(topic_averages: dict):
    strengths = [t for t, s in topic_averages.items() if s >= 8]
    weaknesses = [t for t, s in topic_averages.items() if s < 8]
    return strengths, weaknesses

def plot_topic_scores(topic_averages: dict):
    topics = list(topic_averages.keys())
    scores = list(topic_averages.values())
    colors = ["#7c3aed" if s >= 8 else "#ef4444" for s in scores]

    fig = go.Figure(go.Bar(
        x=topics,
        y=scores,
        marker_color=colors,
        text=scores,
        textposition="auto",
        textfont=dict(color="#e2e8f0", size=12)
    ))

    fig.update_layout(
        plot_bgcolor="#0a0a0f",
        paper_bgcolor="#0a0a0f",
        margin=dict(t=40, b=40, l=40, r=40),
        xaxis=dict(
            tickfont=dict(color="#94a3b8"),
            gridcolor="#1a1a2e",
            linecolor="#3b3b5c",
            title=dict(text="Topic", font=dict(color="#94a3b8"))
        ),
        yaxis=dict(
            range=[0, 10],
            tickfont=dict(color="#94a3b8"),
            gridcolor="#1a1a2e",
            linecolor="#3b3b5c",
            title=dict(text="Score (out of 10)", font=dict(color="#94a3b8"))
        ),
        title=dict(
            text="Topic-wise Performance",
            font=dict(color="#c4b5fd", size=16)
        )
    )
    return fig