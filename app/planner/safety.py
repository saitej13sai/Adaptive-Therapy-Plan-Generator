from typing import List

# Minimal content rules; expand as needed.
BANNED_CLAIMS = [
    "cure autism", "guaranteed results", "100% success", "reverse autism",
    "replace medical advice", "diagnose", "medicate without doctor"
]

def safety_scan(text: str) -> List[str]:
    flags = []
    low = text.lower()
    for phrase in BANNED_CLAIMS:
        if phrase in low:
            flags.append(f"Contains banned claim: '{phrase}'")
    return flags
