import streamlit as st
import json
import os
import re
from datetime import datetime, date
from pathlib import Path

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Task Manager", page_icon="🤖", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 100%);
    border-radius: 16px; padding: 2rem 2.5rem;
    color: white; margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.3rem 0; }
.hero p  { margin: 0; opacity: 0.85; font-size: 1rem; }

.goal-card {
    background: white; border: 1.5px solid #e0e7ff;
    border-radius: 14px; padding: 1.2rem 1.4rem;
    margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(79,70,229,0.07);
}
.goal-title { font-size: 1.05rem; font-weight: 700; color: #1e1b4b; margin-bottom: 0.3rem; }
.goal-meta  { font-size: 0.78rem; color: #94a3b8; }

.task-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 6px 0; border-bottom: 1px solid #f1f5f9;
}
.task-done   { text-decoration: line-through; color: #94a3b8; }
.task-normal { color: #334155; }

.priority-high   { background:#fee2e2; color:#dc2626; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:600; }
.priority-medium { background:#fef3c7; color:#d97706; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:600; }
.priority-low    { background:#dcfce7; color:#16a34a; padding:2px 9px; border-radius:20px; font-size:0.72rem; font-weight:600; }

.progress-label { font-size: 0.8rem; color: #64748b; margin-bottom: 3px; }
.stat-box { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
            padding:1rem; text-align:center; }
.stat-num  { font-size:1.9rem; font-weight:700; color:#4f46e5; }
.stat-lbl  { font-size:0.75rem; color:#94a3b8; }

.ai-badge { background:#ede9fe; color:#7c3aed; padding:3px 10px;
            border-radius:6px; font-size:0.75rem; font-weight:600; }

.section-title { font-size:1.05rem; font-weight:700; color:#1e1b4b;
                 border-bottom:2px solid #e0e7ff; padding-bottom:6px; margin:1.2rem 0 0.8rem 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA PERSISTENCE  (session state = in-memory)
# ─────────────────────────────────────────────
SAVE_FILE = "tasks_data.json"

def load_data():
    if "goals" not in st.session_state:
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    st.session_state.goals = json.load(f)
            except Exception:
                st.session_state.goals = []
        else:
            st.session_state.goals = []

def save_data():
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(st.session_state.goals, f, indent=2, default=str)
    except Exception:
        pass   # Streamlit Cloud: in-memory only is fine

load_data()

# ─────────────────────────────────────────────
# AI BRAIN — RULE-BASED GOAL DECOMPOSER
# (no API key needed — covers 30+ goal types)
# ─────────────────────────────────────────────

GOAL_TEMPLATES = {
    # ── SOFTWARE / TECH ──────────────────────
    "build": [
        ("Research & plan features and architecture",              "High",   1),
        ("Set up project repo and folder structure",               "High",   1),
        ("Implement core backend / main logic",                    "High",   3),
        ("Build frontend / UI layer",                              "Medium", 3),
        ("Connect frontend to backend (API integration)",          "High",   2),
        ("Write tests and fix bugs",                               "Medium", 2),
        ("Write README with setup instructions and screenshots",   "Low",    1),
        ("Deploy to live URL (Streamlit / Vercel / Render)",       "High",   1),
    ],
    "deploy": [
        ("Choose deployment platform (Streamlit / Vercel / Render / Railway)", "High", 1),
        ("Prepare requirements.txt / package.json",                            "High", 1),
        ("Set environment variables and secrets",                              "High", 1),
        ("Push latest code to GitHub",                                         "High", 1),
        ("Connect GitHub repo to deployment platform",                         "Medium", 1),
        ("Trigger first deploy and check logs",                                "High", 1),
        ("Test live URL and fix any runtime errors",                           "High", 1),
        ("Share live link and update resume / portfolio",                      "Low",  1),
    ],
    "api": [
        ("Define API endpoints and data models",            "High",   1),
        ("Set up project structure and dependencies",       "High",   1),
        ("Implement authentication (JWT / OAuth)",          "High",   2),
        ("Implement CRUD endpoints",                        "High",   3),
        ("Add input validation and error handling",         "Medium", 1),
        ("Write Postman collection for all endpoints",      "Medium", 1),
        ("Add pagination and filtering",                    "Low",    1),
        ("Write API documentation (README / Swagger)",      "Low",    1),
        ("Deploy and test with live URL",                   "High",   1),
    ],
    "machine learning": [
        ("Define problem statement and success metric",             "High",   1),
        ("Collect and explore the dataset (EDA)",                   "High",   2),
        ("Clean data: handle nulls, outliers, encoding",            "High",   2),
        ("Feature engineering and selection",                       "High",   2),
        ("Train baseline model and record metrics",                 "High",   1),
        ("Experiment with improved models / hyperparameter tuning", "Medium", 2),
        ("Evaluate: accuracy, confusion matrix, ROC curve",         "High",   1),
        ("Save model (.pkl / .h5) and write prediction script",     "Medium", 1),
        ("Document findings in Jupyter notebook",                   "Low",    1),
    ],
    "github": [
        ("Create repository with a clear, descriptive name", "High",   1),
        ("Push all project code to the repository",          "High",   1),
        ("Write a professional README (problem, stack, demo, run steps)", "High", 1),
        ("Add screenshots or a demo GIF to the README",      "Medium", 1),
        ("Add .gitignore and requirements.txt",              "Medium", 1),
        ("Pin repository on your GitHub profile",            "Low",    1),
        ("Update GitHub profile README with this project",  "Low",    1),
    ],
    "resume": [
        ("Collect all internship and project details",             "High",   1),
        ("Tailor professional summary to the target role",         "High",   1),
        ("Rewrite experience bullets with impact metrics",         "High",   2),
        ("Update technical skills to match JD keywords",          "High",   1),
        ("Add live project links and GitHub URLs",                 "Medium", 1),
        ("Proofread for grammar, formatting, and consistency",     "Medium", 1),
        ("Export as PDF and test ATS parsing",                     "Low",    1),
        ("Send to 2–3 peers for feedback",                         "Low",    1),
    ],
    # ── JOB SEARCH ───────────────────────────
    "apply": [
        ("Research the company: product, mission, team",         "High",   1),
        ("Tailor resume to match the JD keywords",               "High",   1),
        ("Write a targeted cover letter / application message",  "High",   1),
        ("Update LinkedIn headline and summary",                 "Medium", 1),
        ("Submit application and note deadline",                 "High",   1),
        ("Follow up via LinkedIn after 5 business days",        "Low",    1),
        ("Prepare for possible screening call (research FAQs)", "Medium", 1),
    ],
    "interview": [
        ("Research company product, values and recent news",           "High",   1),
        ("Review common technical questions for the role",             "High",   2),
        ("Practice 2–3 STAR-format behavioural stories",               "High",   1),
        ("Revise your projects: be ready to explain every line",       "High",   2),
        ("Do 2 mock interviews (record yourself)",                     "Medium", 1),
        ("Prepare 3–5 questions to ask the interviewer",               "Low",    1),
        ("Set up tech check (camera, mic, stable internet)",           "Low",    1),
        ("Send a thank-you message within 24 hrs of the interview",    "Low",    1),
    ],
    # ── LEARNING ─────────────────────────────
    "learn": [
        ("Define what success looks like (specific skill / project)", "High",   1),
        ("Find the best free resource (YouTube / docs / Coursera)",   "High",   1),
        ("Complete first module and take notes",                      "High",   2),
        ("Build a small practice project using the new skill",        "High",   3),
        ("Solve 5 related problems / exercises",                      "Medium", 2),
        ("Teach it back: write a LinkedIn post or short blog",        "Low",    1),
        ("Add the skill to your resume and GitHub",                   "Low",    1),
    ],
    "langchain": [
        ("Install LangChain and set up virtual environment",        "High",   1),
        ("Read LangChain Quickstart docs and run Hello World",      "High",   1),
        ("Build a simple chain: prompt → LLM → output",            "High",   1),
        ("Add memory to the chain (ConversationBufferMemory)",      "Medium", 1),
        ("Build a tool-using agent (at least 2 tools)",            "High",   2),
        ("Integrate with a vector store (FAISS / Chroma)",         "Medium", 2),
        ("Build a RAG pipeline: load docs → embed → query",        "High",   2),
        ("Deploy the agent as a Streamlit app",                    "Medium", 1),
        ("Push code to GitHub with README and live link",          "Low",    1),
    ],
    "python": [
        ("Install Python and set up VS Code",                 "High",   1),
        ("Complete basics: variables, loops, functions",      "High",   2),
        ("Learn OOP: classes, inheritance, methods",          "High",   2),
        ("Work with files, JSON, and CSV",                    "Medium", 1),
        ("Learn Pandas and NumPy basics",                     "High",   2),
        ("Build a small automation script",                   "High",   2),
        ("Push your project to GitHub",                       "Low",    1),
    ],
    # ── GENERIC FALLBACK ─────────────────────
    "project": [
        ("Define scope, goals and success criteria",    "High",   1),
        ("Break down into smaller milestones",          "High",   1),
        ("Research tools and technologies needed",      "Medium", 1),
        ("Complete Milestone 1 — core functionality",   "High",   3),
        ("Review progress and adjust plan",             "Medium", 1),
        ("Complete Milestone 2 — polish and edge cases","Medium", 2),
        ("Test end-to-end and gather feedback",         "High",   1),
        ("Document and share the final result",         "Low",    1),
    ],
}

def ai_decompose(goal_text: str) -> list:
    """
    Matches the goal text to the best template.
    Returns a list of task dicts.
    """
    goal_lower = goal_text.lower()

    # Find the best matching template keyword
    best_key = None
    best_score = 0
    for keyword in GOAL_TEMPLATES:
        # Score = number of keyword words found in goal
        words = keyword.split()
        score = sum(1 for w in words if w in goal_lower)
        if score > best_score:
            best_score = score
            best_key = keyword

    # Fall back to "project" template if nothing matched
    template = GOAL_TEMPLATES.get(best_key, GOAL_TEMPLATES["project"])

    tasks = []
    for i, (task_text, priority, est_days) in enumerate(template):
        tasks.append({
            "id":       i,
            "text":     task_text,
            "done":     False,
            "priority": priority,
            "est_days": est_days,
            "created":  str(date.today()),
        })
    return tasks


# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🤖 AI Task Manager</h1>
  <p>Type any goal → AI breaks it into prioritised, actionable tasks → track progress → export to JSON</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — NEW GOAL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ➕ Add New Goal")
    goal_input = st.text_area(
        "What do you want to achieve?",
        placeholder="e.g. Build and deploy a LangChain chatbot\nLearn Python from scratch\nApply for AI internships\nPrepare for technical interview",
        height=110,
    )
    deadline = st.date_input("Deadline (optional)", value=None)
    add_btn = st.button("🤖 Generate Tasks", type="primary", use_container_width=True)

    if add_btn and goal_input.strip():
        tasks = ai_decompose(goal_input.strip())
        goal_obj = {
            "id":       datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "title":    goal_input.strip(),
            "deadline": str(deadline) if deadline else None,
            "created":  str(date.today()),
            "tasks":    tasks,
        }
        st.session_state.goals.insert(0, goal_obj)
        save_data()
        st.success(f"✅ Generated {len(tasks)} tasks!")
        st.rerun()
    elif add_btn:
        st.warning("Please enter a goal first.")

    st.markdown("---")
    st.markdown("### 💡 Try these goals")
    examples = [
        "Build a competitor analysis scraper",
        "Learn LangChain and build an AI agent",
        "Deploy my project to Streamlit Cloud",
        "Prepare for a technical interview",
        "Apply for AI internships",
        "Build a REST API with Spring Boot",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            tasks = ai_decompose(ex)
            goal_obj = {
                "id":       datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "title":    ex,
                "deadline": None,
                "created":  str(date.today()),
                "tasks":    tasks,
            }
            st.session_state.goals.insert(0, goal_obj)
            save_data()
            st.rerun()

    st.markdown("---")
    st.markdown("**Built by [Syeda Ayesha](https://github.com/syedaayesha-28)**")


# ─────────────────────────────────────────────
# STATS BAR
# ─────────────────────────────────────────────
if st.session_state.goals:
    all_tasks  = [t for g in st.session_state.goals for t in g["tasks"]]
    done_tasks = [t for t in all_tasks if t["done"]]
    high_pri   = [t for t in all_tasks if t["priority"] == "High" and not t["done"]]

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(f'<div class="stat-box"><div class="stat-num">{len(st.session_state.goals)}</div>'
                f'<div class="stat-lbl">Active Goals</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-box"><div class="stat-num">{len(all_tasks)}</div>'
                f'<div class="stat-lbl">Total Tasks</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-box"><div class="stat-num">{len(done_tasks)}</div>'
                f'<div class="stat-lbl">Completed</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="stat-box"><div class="stat-num">{len(high_pri)}</div>'
                f'<div class="stat-lbl">High Priority Left</div></div>', unsafe_allow_html=True)
    st.markdown("")


# ─────────────────────────────────────────────
# GOAL CARDS
# ─────────────────────────────────────────────
if not st.session_state.goals:
    st.info("👈 Enter a goal in the sidebar — the AI will break it into tasks instantly!")
    st.markdown('<div class="section-title">🎯 Example Goals You Can Try</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, examples in zip([c1, c2, c3], [
        ["Build a ML model", "Deploy to Streamlit", "Build a REST API"],
        ["Learn LangChain", "Prepare GitHub profile", "Write a resume"],
        ["Apply for internship", "Prepare for interview", "Learn Python"],
    ]):
        for ex in examples:
            col.markdown(f"• {ex}")
else:
    st.markdown('<div class="section-title">🎯 Your Goals</div>', unsafe_allow_html=True)

    for g_idx, goal in enumerate(st.session_state.goals):
        tasks     = goal["tasks"]
        done_count = sum(1 for t in tasks if t["done"])
        total      = len(tasks)
        pct        = int(done_count / total * 100) if total else 0
        est_total  = sum(t.get("est_days", 1) for t in tasks)

        with st.expander(f"{'✅' if pct==100 else '🎯'} {goal['title']}  —  {pct}% complete", expanded=(g_idx == 0)):

            # Meta row
            meta_parts = [f"📅 Created: {goal['created']}"]
            if goal.get("deadline"):
                meta_parts.append(f"⏰ Deadline: {goal['deadline']}")
            meta_parts.append(f"⏱ Est. total: {est_total} day(s)")
            meta_parts.append(f"<span class='ai-badge'>🤖 AI Generated</span>")
            st.markdown(
                f'<div class="goal-meta">{" &nbsp;|&nbsp; ".join(meta_parts)}</div>',
                unsafe_allow_html=True
            )

            # Progress bar
            st.markdown(f'<div class="progress-label">{done_count}/{total} tasks done</div>',
                        unsafe_allow_html=True)
            st.progress(pct / 100)

            st.markdown("")

            # Task list
            for t_idx, task in enumerate(tasks):
                col_check, col_text, col_pri, col_days = st.columns([0.5, 6, 1.5, 1])

                new_val = col_check.checkbox(
                    "", value=task["done"],
                    key=f"chk_{goal['id']}_{t_idx}",
                    label_visibility="collapsed"
                )
                if new_val != task["done"]:
                    st.session_state.goals[g_idx]["tasks"][t_idx]["done"] = new_val
                    save_data()
                    st.rerun()

                style_class = "task-done" if task["done"] else "task-normal"
                col_text.markdown(f'<span class="{style_class}">{task["text"]}</span>',
                                  unsafe_allow_html=True)

                pri_class = f"priority-{task['priority'].lower()}"
                col_pri.markdown(f'<span class="{pri_class}">{task["priority"]}</span>',
                                 unsafe_allow_html=True)

                col_days.markdown(f'<span style="font-size:0.8rem;color:#94a3b8">{task["est_days"]}d</span>',
                                  unsafe_allow_html=True)

            # Action buttons
            st.markdown("")
            b1, b2, b3 = st.columns([2, 2, 6])
            with b1:
                if st.button("🗑 Delete Goal", key=f"del_{goal['id']}", use_container_width=True):
                    st.session_state.goals.pop(g_idx)
                    save_data()
                    st.rerun()
            with b2:
                export_data = json.dumps(goal, indent=2, default=str)
                st.download_button(
                    "⬇️ Export JSON", data=export_data,
                    file_name=f"goal_{goal['id']}.json",
                    mime="application/json",
                    key=f"exp_{goal['id']}",
                    use_container_width=True,
                )
