import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
import openai
from pydantic import ValidationError
from .schemas import NarrativePlan

# Load env and set API key for the new OpenAI SDK
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def generate_narrative(structured_plan_json: str, system_prompt: str, user_prompt_template: str) -> NarrativePlan:
    """
    Uses OpenAI Chat Completions (new SDK style) and returns a validated NarrativePlan.
    Falls back to a safe default if JSON parsing/validation fails.
    """
    user_prompt = user_prompt_template.format(structured_json=structured_plan_json)

    resp = openai.chat.completions.create(
        model=DEFAULT_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
        narrative = NarrativePlan(**data)
        return narrative
    except (json.JSONDecodeError, ValidationError):
        # Fail closed with a minimal safe narrative
        fallback = NarrativePlan(
            overview="This week focuses on consistent practice of social greetings, expanding functional communication, and structured play routines. Activities are aligned to the provided targets with prompting and reinforcement faded appropriately.",
            daily_schedule={
                "Mon": ["Greeting practice", "Requesting during snack", "Functional play rotations"],
                "Tue": ["Turn-taking game", "Labeling scavenger", "Pretend play 2-step"],
                "Wed": ["Peer greeting walk", "Phrase mands practice", "Board game rules"],
                "Thu": ["Cooperative play station", "WH-question bingo", "Shared craft"],
                "Fri": ["Generalization across settings", "Story retell", "Choice play with token cash-out"],
            },
            parent_tips=[
                "Use a consistent hello/goodbye routine at home.",
                "Offer choices to encourage requesting.",
                "Narrate play actions and wait for responses.",
                "Practice turn-taking during simple games.",
            ],
            cautions=[
                "Fade prompts to avoid over-prompting.",
                "Generalize targets across rooms and people.",
            ],
        )
        return fallback
