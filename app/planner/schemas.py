from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional, Dict, Any
from datetime import date

class ChildProfile(BaseModel):
    name: str = Field(..., min_length=1)
    age_years: int = Field(..., ge=2, le=16)
    diagnosis: str = "Autism Spectrum Disorder"
    strengths: List[str] = []
    preferences: List[str] = []
    notes: Optional[str] = None

class SkillLevels(BaseModel):
    social: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    verbal: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    play: str = Field(..., pattern="^(beginner|intermediate|advanced)$")

class DomainPlan(BaseModel):
    domain: str
    level: str
    targets: List[str]
    prompting: str
    reinforcement: str
    mastery_criteria: str
    activities: List[str]

class WeeklyPlan(BaseModel):
    child: ChildProfile
    week_of: date
    domains: List[DomainPlan]
    safety_flags: List[str] = []
    generator: str = "rules-first-v1"

class NarrativePlan(BaseModel):
    """LLM output schema (strict)."""
    overview: str
    daily_schedule: Dict[str, List[str]]
    parent_tips: List[str]
    cautions: List[str]

class PlanPackage(BaseModel):
    plan: WeeklyPlan
    narrative: NarrativePlan
