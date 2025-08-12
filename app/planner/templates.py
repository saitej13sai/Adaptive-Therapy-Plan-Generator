SYSTEM_NARRATIVE = """You are an ABA plan narrator. 
- You MUST NOT invent therapy targets. 
- Convert provided structured plan into a warm, parent-friendly narrative.
- Do NOT make medical claims or guarantees.
- Keep tone supportive and clear.
OUTPUT MUST BE VALID JSON ONLY and match the provided JSON schema keys exactly.
"""

NARRATIVE_USER_PROMPT = """Create a one-week narrative plan for the child based on this structured data:

STRUCTURED_PLAN_JSON:
{structured_json}

Constraints:
- overview: short paragraph (5–7 sentences) summarizing goals across domains.
- daily_schedule: 5 keys (Mon..Fri). For each day, list 3–5 concise activities referencing provided targets/activities.
- parent_tips: 4–6 bullet points with simple at-home practice ideas.
- cautions: 2–4 items about prompting fade, generalization, and avoiding over-prompting.

Return **JSON ONLY** for keys: overview, daily_schedule, parent_tips, cautions.
"""
