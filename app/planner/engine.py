import yaml
from datetime import date
from typing import Dict, Any, List
from .schemas import *
from .safety import safety_scan
from pydantic import ValidationError

class RuleBook:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules

    @classmethod
    def from_file(cls, path: str) -> "RuleBook":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    def plan_for_level(self, domain: str, level: str) -> DomainPlan:
        try:
            block = self.rules["domains"][domain][level]
        except KeyError:
            raise ValueError(f"Rule not found for {domain} / {level}")
        dp = DomainPlan(
            domain=domain,
            level=level,
            targets=block["targets"],
            prompting=block["prompting"],
            reinforcement=block["reinforcement"],
            mastery_criteria=block["mastery_criteria"],
            activities=block["activities"],
        )
        return dp

def build_weekly_plan(
    child: ChildProfile, levels: SkillLevels, rulebook: RuleBook, week_of: date
) -> WeeklyPlan:
    domains: List[DomainPlan] = []
    domains.append(rulebook.plan_for_level("Social", levels.social))
    domains.append(rulebook.plan_for_level("Verbal", levels.verbal))
    domains.append(rulebook.plan_for_level("Play", levels.play))

    # Aggregate safety scan on concatenated text
    concat_text = " ".join(
        t for d in domains for t in (d.prompting, d.reinforcement, d.mastery_criteria, " ".join(d.targets))
    )
    flags = safety_scan(concat_text)

    plan = WeeklyPlan(
        child=child,
        week_of=week_of,
        domains=domains,
        safety_flags=flags,
        generator="rules-first-v1",
    )
    return plan

def plan_to_minified_dict(plan: WeeklyPlan) -> Dict[str, Any]:
    """Only the fields LLM needs."""
    return {
        "child": {
            "name": plan.child.name,
            "age_years": plan.child.age_years,
            "diagnosis": plan.child.diagnosis,
            "strengths": plan.child.strengths,
            "preferences": plan.child.preferences,
        },
        "week_of": str(plan.week_of),
        "domains": [
            {
                "domain": d.domain,
                "level": d.level,
                "targets": d.targets,
                "prompting": d.prompting,
                "reinforcement": d.reinforcement,
                "mastery_criteria": d.mastery_criteria,
                "activities": d.activities,
            }
            for d in plan.domains
        ],
    }
