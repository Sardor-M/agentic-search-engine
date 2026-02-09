"""
3View Product Knowledge Base
Scoped to: Machine365.Ai + MV900 only

Loads structured product data from JSON files in data/.
Agents use these to map customer problems to 3View solutions.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> dict | list:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# ── Load product data from JSON ──
_company = _load_json("company.json")
MV900_KNOWLEDGE = _load_json("mv900.json")
MACHINE365_KNOWLEDGE = _load_json("machine365.json")
COMBINED_SOLUTION = _load_json("combined_solution.json")
CASE_STUDIES = _load_json("case_studies.json")

# Build COMPANY_PROFILE string from structured data
COMPANY_PROFILE = (
    f"{_company['name']} is a South Korean smart manufacturing company "
    f"based in {_company['location']}.\n"
    + "\n".join(f"- {v}" for v in _company["stats"].values())
    + f"\n- Contact: {_company['contact']['email']} | {_company['contact']['phone']}"
)


def get_full_product_context() -> str:
    """Returns formatted product knowledge for agent context."""
    mv = MV900_KNOWLEDGE
    m365 = MACHINE365_KNOWLEDGE
    combo = COMBINED_SOLUTION

    sections = [
        "=== 3VIEW COMPANY OVERVIEW ===",
        COMPANY_PROFILE,
        "",
        f"=== PRODUCT 1: {mv['name']} (Hardware) ===",
        f"{mv['name']} — {mv['tagline']}",
        mv["description"],
        "",
        "Key Features:",
        *[f"- {f}" for f in mv["key_features"]],
        "",
        "Key Functions:",
        *[f"- {f}" for f in mv["key_functions"]],
        "",
        "Expected Benefits:",
        *[f"- {b}" for b in mv["expected_benefits"]],
        "",
        f"Best For: {', '.join(mv['best_for'])}",
        "",
        f"Hardware Specs: {mv['specs']}",
        "",
        f"=== PRODUCT 2: {m365['name']} (Software Platform) ===",
        f"{m365['name']} — {m365['tagline']}",
        m365["description"],
        "",
        "Key Features:",
        *[f"- {f}" for f in m365["key_features"]],
        "",
        "Key Functions:",
        *[f"- {k}: {v}" for k, v in m365["key_functions"].items()],
        "",
        "Implementation Benefits:",
        *[f"- {k}: {v}" for k, v in m365["implementation_benefits"].items()],
        "",
        f"Best For: {', '.join(m365['best_for'])}",
        "",
        f"=== COMBINED SOLUTION: {combo['name']} ===",
        combo["description"],
        "",
        "Synergies:",
        *[f"- {s}" for s in combo["synergies"]],
        "",
        "Ideal Customer Pain Points:",
        *[f"- {p}" for p in combo["ideal_customer_profile"]["pain_points"]],
        "",
        "Typical ROI:",
        *[f"- {k}: {v}" for k, v in combo["ideal_customer_profile"]["typical_roi"].items()],
        "",
        "=== CASE STUDIES ===",
        *[f"- {cs['title']}: {cs['solution']} -> {cs['result']}" for cs in CASE_STUDIES],
    ]

    return "\n".join(sections)
