from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.extraction import ExtractionResult

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are a financial analyst extracting data from an official Senus PLC financial
disclosure document (e.g. a listing Information Document/prospectus, an annual or half-year results
announcement, or an audited statutory financial statement) for a board reporting system.

Rules:
- Only extract figures you can find explicitly stated in the document. Do not estimate, infer, or
  fill in numbers that are not directly present.
- Focus on the P&L / "Summary Financial Information" table (turnover, gross profit, operating profit,
  profit after tax, balance sheet items, cash flow items) and the KPI / customer sections. That
  table's "Turnover" row is the company's headline sales figure: always record it with metric_key
  "revenue", never "turnover", and never as a separate rounded approximation quoted elsewhere in
  the prose (e.g. "sales of approximately €0.83 million") once you already have the precise figure
  from the table. One fact per period per real-world number, not one per place it's mentioned.
- The company's fiscal year ends 30 June. Use period_type "ANNUAL" for a full fiscal year (e.g. "year
  ended 30 June 2025" -> label "FY2025", fiscal_year 2025, start_date 2024-07-01, end_date
  2025-06-30). Use period_type "HALF_YEAR" for a six-month interim period (e.g. "six months ended 31
  December 2025" -> label "HY2026" (it's the first half of FY2026, the year ending 30 June 2026),
  fiscal_year 2026, start_date 2025-07-01, end_date 2025-12-31). A half-year results announcement
  typically also states a real comparative for the same six months a year earlier: extract that as
  its own separate HALF_YEAR period too (e.g. "six months ended 31 December 2024" -> label "HY2025"),
  not as a MODELLED estimate, it's an equally real reported figure.
- Money values should be plain numbers in EUR, no currency symbols or thousands separators.
- If a figure is a percentage or ratio rather than a currency amount, still record it as a plain
  number (e.g. 17.5) and say so in the "note" field.
- Never compute a derived number yourself (e.g. revenue divided by customer count). Only fill
  "avg_acv" on a customer metric if the document states a single blended average contract value
  for that exact channel.
- customer_metrics.channel must be exactly one of ENTERPRISE, INDEPENDENT or RD: the three channels
  the company itself reports overall customer counts by. Use customer_metrics only for those three
  company-wide totals.
- The document also breaks revenue, customer count and ACV down by product (Soil, Terrain, ERA)
  crossed with channel, often as a table or chart rendered as an image rather than as plain text.
  Read those images too, don't skip a number just because it's in a graphic rather than body text.
  Record each one you find as a fact with metric_key "{metric}_{product}_{channel}" in lowercase.
  There are three metrics to look for per product: revenue, customer count, and ACV, e.g.
  "revenue_soil_enterprise", "customers_soil_enterprise", "acv_soil_enterprise" (do all three for
  every product/channel combination that has a number, not just revenue). Omit a combination
  entirely if the chart shows it as blank/dash rather than a number.
- Every fact must be traceable to a real number somewhere in the document (text, table or chart).
  Never fill a gap with a computed or assumed value, and never back-calculate a prior-year figure
  from a sentence describing a year-over-year change (e.g. "decreased by €X to €Y" only tells you
  Y for the current year; do not add X back to invent last year's number unless that number is also
  stated directly, on its own, somewhere else). Still record the current year's figure in that case,
  just skip the year you can't source directly, e.g. "Administrative expenses decreased by €274,795
  to €1,286,058" gives you FY2025 admin_expenses = 1,286,058 and no FY2024 admin_expenses fact.
- If the document states a bound on a historic, already-reported figure rather than an exact number
  (e.g. "less than 5% outside Ireland" for a past year), do not turn that into a precise
  complementary number (e.g. don't turn it into "95% in Ireland"). Only record a percentage when
  the document states that exact percentage for that exact thing. This does not apply to
  kpi_targets: a forward-looking target is often itself expressed as a threshold (e.g. "less than
  50% of revenue from Ireland by FY2030" is a valid target_value of 50), so record those as given.
- Also capture geography splits if shown per product (metric_key like "revenue_pct_ireland_soil",
  value as a plain percentage number e.g. 81.7) and the company-wide Ireland revenue percentage if
  stated in the text (metric_key "revenue_pct_ireland").
- Balance sheet face lines named simply "Debtors" or "Creditors: amounts falling due within one
  year" are aggregate totals: record them as metric_key "debtors" / "creditors_current". Only use
  "trade_debtors" / "trade_creditors" when the document separately breaks out a "Trade debtors" /
  "Trade creditors" sub-line (usually in the notes) that is a smaller subset of that aggregate.
  Never let both meanings share the same metric_key, they are different real-world numbers.
- Cash flow statements often show a subtotal before financing costs (e.g. "Cash used in
  operations") followed by a final "Net cash used in/generated from operating activities" line
  (after interest paid). Always use metric_key "cash_operating" for that final net line, never the
  earlier subtotal. The same applies to "cash_investing" and "cash_financing": always the final net
  total for that section, never an individual component within it. If a section's components are
  themselves informative (e.g. "Issue of new shares", "Repayment of loans" within financing), record
  those as their own separate, clearly distinct metric_keys (e.g. "cash_financing_share_issue",
  "cash_financing_loans") in addition to, never instead of, the section's final net total.
- If a strategic target you're extracting clearly restates one already given a name in this same
  extraction rulebook or a prior document (e.g. a revenue CAGR target, an EBITDA-positive date), use
  a stable, consistent name for it (e.g. always "Revenue CAGR", always "EBITDA Positive") rather than
  paraphrasing the document's exact wording differently each time. Consistent names are what let two
  documents' extractions be recognised as describing the same target rather than duplicates.
- A kpi_target's description must state the comparison direction in plain words (e.g. "at least 50%
  compound annual growth", "fewer than 50% of revenue from Ireland"), not just the bare number. The
  target_value alone doesn't say whether the goal is to reach at least that number or stay below it,
  and a reader must not have to guess.
- A debt_instrument still outstanding as at the document's reporting date gets repaid_date null. If
  the document states it has been repaid, record repaid_date as the disclosed date. If only a month
  and year are disclosed (not an exact day), use the last day of that month and say so in "note"
  (e.g. "Exact repayment day not disclosed; dated to the last day of the disclosed month.").
- A count of customers gained or contracts closed during a period (a "bookings" figure, e.g. "21
  enterprise customers closed in the period") is different from customer_metrics, which is a
  point-in-time total of accounts held per channel as of the period end date. Record period bookings
  as their own facts (e.g. metric_key "new_customers_period_enterprise", or "new_bookings_value" for
  an associated deal value) rather than as a customer_metrics row, and never treat a "closed in the
  period" count as if it were the channel's total customer count.
"""

USER_PROMPT = """Extract the historic financial data, customer/KPI metrics, strategic targets, and
debt instruments from the attached document into the given JSON schema. Use one period entry per
distinct reporting period (annual or half-year) you find full P&L/balance sheet/cash flow data for."""


def extract_from_pdf(pdf_path: Path) -> ExtractionResult:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type="application/pdf"),
            USER_PROMPT,
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )

    if response.parsed is not None:
        return response.parsed
    return ExtractionResult.model_validate_json(response.text)
