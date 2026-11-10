# Contracts: 003-ask-your-money

## POST /chat  (rate limit RATE_LIMIT_CHAT = 10 / 60 s per IP)

Request:
```json
{"question": "How much FX loss last quarter?",
 "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```
- `question`: 1–500 chars after trim (else 422). `history`: ≤ 6 items, each content ≤ 2000 chars.

Response 200:
```json
{
  "answer": "Your FX loss in last quarter (Jul–Sep 2026) was ₹38,000.00 (INR, Simulated (sandbox) rate).",
  "outcome": "answered" | "no_data" | "fallback",
  "periods": ["Last quarter (1 Jul 2026 – 30 Sep 2026)"],
  "figures": [
    {"label": "FX loss", "kind": "money", "value": "38000.00", "currency": "INR",
     "period": "Last quarter (1 Jul 2026 – 30 Sep 2026)"},
    {"label": "Payments", "kind": "count", "value": "18", "currency": null, "period": "..."},
    {"label": "Leakage %", "kind": "percent", "value": "7.30", "currency": null, "period": "..."}
  ],
  "disclaimer": "Prepared from user data — not tax advice. Confirm with a CA." | null,
  "tools_used": ["fee_summary"]
}
```
429 `RATE_LIMITED`, 422 `VALIDATION_ERROR` use the standard error shape. LLM failures are 200 with
`outcome: "fallback"`.

## Internal Python interfaces (owned by the files named; others import only these)

`app/ai/types.py`
```python
class Figure(BaseModel): label: str; kind: Literal["money","count","percent"]; value: str;
    currency: str | None; period: str
class ToolResult(BaseModel): name: str; content: dict[str, Any]  # JSON-safe, money as strings
    has_data: bool; figures: list[Figure]; period_label: str
```
`app/ai/tools/__init__.py`
```python
TOOL_DEFINITIONS: list[dict[str, Any]]   # Anthropic tool JSON: name, description, input_schema
def run_tool(session: Session, name: str, arguments: dict[str, Any], now: datetime) -> ToolResult
# unknown tool or invalid arguments -> raises ToolInputError (app/ai/types.py)
```
`app/ai/llm.py`
```python
class LlmRequest(BaseModel): system: str; messages: list[dict[str, Any]]; tools: list[dict[str, Any]]
class LlmResponse(BaseModel): content: list[dict[str, Any]]; stop_reason: str
class LlmClient(Protocol): def create(self, request: LlmRequest) -> LlmResponse: ...
def get_llm() -> LlmClient   # settings: llm_mode http|fake, llm_api_url, llm_api_key, llm_model
```
