import json

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.metrics import PeriodMetrics

MODEL = "gemini-2.5-flash"
PROMPT_VERSION = "v1"

SECTION_TITLES = {
    "growth": "Growth & Revenue",
    "profitability": "Profitability",
    "cash-liquidity": "Cash & Liquidity",
    "solvency": "Solvency & Leverage",
    "returns": "Returns",
}

SYSTEM_PROMPT = """You are a financial analyst writing a short board commentary for Senus PLC, an
Irish Natural Capital management software company, for a non-financial audience (assume the reader
does not have an accounting background).

You are given computed metrics for one section of the board report, already calculated from the
company's financial disclosures and labelled with whether each period's figures are REPORTED (from
an official filing) or MODELLED (estimated by splitting a reported total, e.g. individual months).

Rules:
- Only discuss numbers present in the data given to you. Never invent a figure, a date or a trend
  that isn't directly supported by the input.
- Write 3 to 5 short sentences of plain prose, no headings, no bullet points, no markdown.
- Explain any financial term you use in the same sentence, briefly, as if to someone without a
  finance background (e.g. "EBITDA, roughly how much the core business earns before financing and
  accounting costs").
- When you reference a MODELLED period or figure, say so explicitly (e.g. "an estimated..."),
  rather than presenting it with the same certainty as a REPORTED one.
- Focus on the clearest trend across periods (improving, worsening, or stable) and the single most
  useful thing a board member should take away, rather than restating every number.
"""


def generate_insight(section_key: str, metrics: list[PeriodMetrics]) -> str:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)

    section_title = SECTION_TITLES.get(section_key, section_key)
    payload = json.dumps([m.model_dump() for m in metrics], indent=2)
    user_prompt = f"Section: {section_title}\n\nComputed metrics (JSON):\n{payload}"

    response = client.models.generate_content(
        model=MODEL,
        contents=[user_prompt],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return response.text
