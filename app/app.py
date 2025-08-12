import json
import os
from datetime import date
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
import openai  # <-- NEW: use the new SDK import

from planner.schemas import ChildProfile, SkillLevels, PlanPackage
from planner.engine import RuleBook, build_weekly_plan, plan_to_minified_dict
from planner.templates import SYSTEM_NARRATIVE, NARRATIVE_USER_PROMPT
from planner.llm import generate_narrative

# -----------------------
# Load environment variables from .env
# -----------------------
load_dotenv()

# Allow Streamlit Cloud "Secrets" to set the env vars automatically if running online
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "OPENAI_MODEL" in st.secrets:
    os.environ["OPENAI_MODEL"] = st.secrets["OPENAI_MODEL"]

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------
# Streamlit page config
# -----------------------
st.set_page_config(page_title="Adaptive Therapy Plan Generator", page_icon="🧩", layout="wide")

# ---- Sidebar: API and Model Health
with st.sidebar:
    st.header("Settings")
    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    st.write("OpenAI API Key:", "✅ Found" if api_key_present else "❌ Missing")
    st.caption("Set OPENAI_API_KEY in your environment, .env, or Streamlit Secrets")

    st.divider()
    st.markdown("**Model:**")
    st.code(os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    st.divider()
    st.markdown("**How it works**")
    st.caption(
        "- Rules determine goals & criteria (deterministic)\n"
        "- LLM writes the parent-friendly narrative only\n"
        "- You review and export"
    )

st.title("🧩 Adaptive Therapy Plan Generator — Educator/Tutor Prototype")

# ---- Tabs
tab1, tab2 = st.tabs(["Generate Weekly Plan", "Tutor/Parent Chat"])

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), "planner", "rules.yaml")
rulebook = RuleBook.from_file(RULES_PATH)

# ---- Inputs shared
colA, colB = st.columns(2)
with colA:
    st.subheader("Child Profile")
    default_json_path = os.path.join(os.path.dirname(__file__), "data", "sample_child.json")
    if st.toggle("Load sample child", value=True):
        with open(default_json_path, "r", encoding="utf-8") as f:
            sample = json.load(f)
    else:
        sample = {
            "name": "",
            "age_years": 6,
            "diagnosis": "Autism Spectrum Disorder",
            "strengths": [],
            "preferences": [],
            "notes": "",
        }

    name = st.text_input("Name (first initial OK)", value=sample["name"])
    age = st.number_input("Age (years)", min_value=2, max_value=16, value=sample["age_years"])
    diagnosis = st.text_input("Diagnosis", value=sample["diagnosis"])
    strengths = st.text_input("Strengths (comma-separated)", value=", ".join(sample["strengths"]))
    preferences = st.text_input("Preferences (comma-separated)", value=", ".join(sample["preferences"]))
    notes = st.text_area("Notes (optional)", value=sample.get("notes", ""))

with colB:
    st.subheader("Skill Levels (select)")
    social = st.selectbox("Social", ["beginner", "intermediate", "advanced"], index=0)
    verbal = st.selectbox("Verbal", ["beginner", "intermediate", "advanced"], index=0)
    play = st.selectbox("Play", ["beginner", "intermediate", "advanced"], index=0)
    week_of = st.date_input("Week Of", value=date.today())

child = ChildProfile(
    name=name or "Child",
    age_years=int(age),
    diagnosis=diagnosis or "Autism Spectrum Disorder",
    strengths=[s.strip() for s in strengths.split(",") if s.strip()],
    preferences=[p.strip() for p in preferences.split(",") if p.strip()],
    notes=notes or None,
)
levels = SkillLevels(social=social, verbal=verbal, play=play)

# ---- Tab 1: Plan generation
with tab1:
    st.subheader("1) Generate Deterministic Weekly Plan")
    if st.button("Build Plan (Rules)"):
        plan = build_weekly_plan(child=child, levels=levels, rulebook=rulebook, week_of=week_of)
        st.session_state["plan"] = plan
        st.success("Plan built from rules.")

    if "plan" in st.session_state:
        plan = st.session_state["plan"]
        st.write("### Deterministic Plan (JSON)")
        st.json(plan.model_dump(), expanded=False)

        if plan.safety_flags:
            st.warning("Safety flags detected:")
            for f in plan.safety_flags:
                st.write("-", f)

        st.subheader("2) Create Parent-Friendly Narrative (LLM)")
        if st.button("Generate Narrative (OpenAI)"):
            structured = json.dumps(plan_to_minified_dict(plan), ensure_ascii=False)
            narrative = generate_narrative(structured, SYSTEM_NARRATIVE, NARRATIVE_USER_PROMPT)
            pkg = PlanPackage(plan=plan, narrative=narrative)
            st.session_state["package"] = pkg
            st.success("Narrative generated.")

    if "package" in st.session_state:
        pkg: PlanPackage = st.session_state["package"]
        st.write("### Narrative (LLM JSON)")
        st.json(pkg.narrative.model_dump(), expanded=False)

        # Render friendly view
        st.write("## Weekly Overview")
        st.write(pkg.narrative.overview)

        st.write("## Daily Schedule")
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            acts = pkg.narrative.daily_schedule.get(day, [])
            st.markdown(f"**{day}**")
            for a in acts:
                st.write("-", a)

        st.write("## Parent Tips")
        for tip in pkg.narrative.parent_tips:
            st.write("-", tip)

        st.write("## Cautions")
        for c in pkg.narrative.cautions:
            st.write("-", c)

# ---- Tab 2: Tutor/Parent Chat
with tab2:
    st.subheader("Ask the Tutor Assistant")
    st.caption("The assistant will stay within the child’s selected levels and rules.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": "You are a concise ABA tutor assistant. Avoid medical claims and guarantees."},
            {"role": "assistant", "content": "Hi! Ask me about greeting practice, requesting, or play ideas based on today's levels."},
        ]

    # Display chat
    for m in st.session_state["messages"]:
        if m["role"] == "assistant":
            st.chat_message("assistant").write(m["content"])
        elif m["role"] == "user":
            st.chat_message("user").write(m["content"])

    query = st.chat_input("Type your question...")
    if query:
        st.session_state["messages"].append({"role": "user", "content": query})

        # Deterministic context for guardrails
        plan = build_weekly_plan(child, levels, rulebook, week_of)
        snippet = json.dumps(plan_to_minified_dict(plan), ensure_ascii=False)

        sys_prompt = (
            "You are an ABA tutor. ONLY use the provided structured plan content. "
            "No medical claims, no guarantees. Keep answers actionable and short."
        )
        tool_context = f"STRUCTURED_PLAN:{snippet}"

        resp = openai.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"{tool_context}\n\nQuestion: {query}"},
            ],
        )
        answer = resp.choices[0].message.content.strip()
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)

st.divider()
st.caption("Prototype: rules-first planner + LLM narrative wrapper. © Your Center")
