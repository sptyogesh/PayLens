"""Gemini adapter behind the single LLM wrapper (research R5): generateContent over httpx.

Same LlmClient contract as AnthropicLlm: requests are translated by `gemini_format.py`, and the
reply is turned back into text / tool_use blocks with Anthropic stop reasons, so the chat agent,
FIRA extraction and report summary (and their grounding checks) are unchanged. The key goes only
in the x-goog-api-key header and is never logged.
"""

import logging
from typing import Final

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.alias_generators import to_camel

from app.ai.gemini_format import LOCAL_ID_PREFIX, SIGNATURE_KEY, gemini_body
from app.ai.llm import UNAVAILABLE_MESSAGE, LlmRequest, LlmResponse, check_status, post_json
from app.common.constants import GEMINI_API_PATH, GEMINI_METHOD
from app.common.errors import LlmUnavailableError

logger = logging.getLogger(__name__)

TOOL_USE: Final = "tool_use"
END_TURN: Final = "end_turn"
REFUSAL: Final = "refusal"
STOP_REASONS: Final = {"STOP": END_TURN, "MAX_TOKENS": "max_tokens"}


class GeminiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


class FunctionCall(GeminiModel):
    name: str = Field(min_length=1)
    args: dict[str, object] = Field(default_factory=dict)
    id: str | None = None


class Part(GeminiModel):
    text: str | None = None
    thought: bool = False
    thought_signature: str | None = None
    function_call: FunctionCall | None = None


class Content(GeminiModel):
    parts: list[Part] = Field(default_factory=list)


class Candidate(GeminiModel):
    content: Content = Field(default_factory=Content)
    finish_reason: str | None = None


class PromptFeedback(GeminiModel):
    block_reason: str | None = None


class GenerateContentResponse(GeminiModel):
    candidates: list[Candidate] = Field(default_factory=list)
    prompt_feedback: PromptFeedback | None = None


class GeminiLlm:
    """Calls POST /v1beta/models/{model}:generateContent. Logs status codes and reasons only."""

    def __init__(self, client: httpx.Client, api_key: str, model: str) -> None:
        self._client = client
        self._api_key = api_key
        self._path = f"{GEMINI_API_PATH}/{model}:{GEMINI_METHOD}"

    def create(self, request: LlmRequest) -> LlmResponse:
        headers = {"x-goog-api-key": self._api_key}
        response = post_json(self._client, self._path, gemini_body(request), headers, request)
        check_status(response.status_code)
        try:
            parsed = GenerateContentResponse.model_validate_json(response.content)
        except ValidationError as error:
            logger.warning("Gemini returned an unreadable response")
            raise LlmUnavailableError(UNAVAILABLE_MESSAGE) from error
        return to_llm_response(parsed)


def to_llm_response(parsed: GenerateContentResponse) -> LlmResponse:
    if not parsed.candidates:
        reason = parsed.prompt_feedback.block_reason if parsed.prompt_feedback else None
        if reason is None:
            logger.warning("Gemini returned no candidates and no block reason")
            raise LlmUnavailableError(UNAVAILABLE_MESSAGE)
        logger.info("Gemini blocked the prompt: %s", reason)
        return LlmResponse(content=[], stop_reason=REFUSAL)
    candidate = parsed.candidates[0]
    blocks = [block(part, index) for index, part in enumerate(candidate.content.parts)]
    content = [b for b in blocks if b is not None]
    if any(b["type"] == TOOL_USE for b in content):
        return LlmResponse(content=content, stop_reason=TOOL_USE)
    reason = candidate.finish_reason or ""
    if reason not in STOP_REASONS:
        logger.info("Gemini stopped with %s", reason or "no finish reason")
    return LlmResponse(content=content, stop_reason=STOP_REASONS.get(reason, REFUSAL))


def block(part: Part, index: int) -> dict[str, object] | None:
    """A text or tool_use block; thought summaries and empty unsigned parts are dropped."""
    found: dict[str, object] | None = None
    if part.thought:
        return None
    if part.function_call is not None:
        call = part.function_call
        call_id = call.id or f"{LOCAL_ID_PREFIX}{index}"
        found = {"type": TOOL_USE, "id": call_id, "name": call.name, "input": call.args}
    elif part.text or part.thought_signature:
        found = {"type": "text", "text": part.text or ""}
    if found is not None and part.thought_signature:
        found[SIGNATURE_KEY] = part.thought_signature
    return found
