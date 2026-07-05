import json

import httpx
from google import genai
from google.genai import types
from google.genai.errors import APIError

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
- Never use em dashes. Use commas, full stops or parentheses instead.
"""


class InsightGenerationError(Exception):
    """Raised when the AI insight proxy fails to produce usable content, so the router can turn
    it into a clean 503 rather than a bare 500."""


def generate_insight(section_key: str, metrics: list[PeriodMetrics]) -> str:
    settings = get_settings()

    section_title = SECTION_TITLES.get(section_key, section_key)
    payload = json.dumps([m.model_dump() for m in metrics], indent=2)
    user_prompt = f"Section: {section_title}\n\nComputed metrics (JSON):\n{payload}"

    if settings.insight_proxy_url:
        return _generate_via_proxy(settings, user_prompt)
    return _generate_direct(settings, user_prompt)


def _generate_direct(settings, user_prompt: str) -> str:
    """Calls Gemini directly. Works fine from a residential IP (local development); this is the
    only path used there, since INSIGHT_PROXY_URL is unset locally."""
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[user_prompt],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
    except APIError as exc:
        raise InsightGenerationError(str(exc)) from exc
    return response.text


def _generate_via_proxy(settings, user_prompt: str) -> str:
    """Google blocks direct Gemini calls from most cloud-hosting datacenter IP ranges (confirmed
    against Render specifically, and reported against other providers too, as of mid-2026), even
    with a correctly restricted API key. So the deployed environment (INSIGHT_PROXY_URL set)
    routes the call through a small serverless function on Vercel instead
    (apps/web/api/generate-insight.ts), which isn't blocked. The key stays server-side there too,
    it's never sent to the browser; a shared secret stops anyone else who finds the proxy's URL
    from spending our Gemini quota."""
    try:
        response = httpx.post(
            settings.insight_proxy_url,
            json={"model": MODEL, "system_instruction": SYSTEM_PROMPT, "prompt": user_prompt},
            headers={"x-proxy-secret": settings.insight_proxy_secret},
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise InsightGenerationError(f"insight proxy request failed: {exc}") from exc

    text = response.json().get("text")
    if not text:
        raise InsightGenerationError(f"insight proxy returned no text: {response.text}")
    return text
