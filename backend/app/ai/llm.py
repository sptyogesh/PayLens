"""The single LLM wrapper (Principle IX): one request/response shape for every provider.

Requests and responses use the Anthropic Messages block format (research R1). AnthropicLlm sends
them as they are; GeminiLlm (`gemini.py`) translates them (research R5). Provider, URL, model and
key come from settings. The key is sent only in a request header and is never logged. No retry
loop: the chat must answer within the timeout (FR-009). HTTP 429 is "busy" (LLM_BUSY).
"""

import logging
from http import HTTPStatus
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.common.constants import LLM_API_VERSION, LLM_BUSY_CODE, LLM_EFFORT, LLM_MAX_TOKENS
from app.common.errors import LlmConfigError, LlmUnavailableError

logger = logging.getLogger(__name__)

MESSAGES_PATH = "/v1/messages"
UNAVAILABLE_MESSAGE = "The AI service is not available right now."
CONFIG_MESSAGE = "The AI service rejected the request. Check the LLM settings."
BUSY_MESSAGE = "The AI is busy. Try again shortly."


class LlmRequest(BaseModel):
    system: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = Field(default_factory=list)
    timeout_s: float | None = None  # caps this call (the chat has one overall deadline)
    # Strict JSON output (004 research R1): the answer is one text block matching this schema.
    output_schema: dict[str, Any] | None = None


class LlmResponse(BaseModel):
    content: list[dict[str, Any]]
    stop_reason: str


class LlmClient(Protocol):
    def create(self, request: LlmRequest) -> LlmResponse: ...


class AnthropicLlm:
    """Calls POST /v1/messages. Only status codes and error types are logged."""

    def __init__(self, client: httpx.Client, api_key: str, model: str) -> None:
        self._client = client
        self._api_key = api_key
        self._model = model

    def create(self, request: LlmRequest) -> LlmResponse:
        headers = {"x-api-key": self._api_key, "anthropic-version": LLM_API_VERSION}
        response = post_json(self._client, MESSAGES_PATH, self._body(request), headers, request)
        check_status(response.status_code)
        try:
            return LlmResponse.model_validate_json(response.content)
        except ValidationError as error:
            logger.warning("AI service returned an unreadable response")
            raise LlmUnavailableError(UNAVAILABLE_MESSAGE) from error

    def _body(self, request: LlmRequest) -> dict[str, Any]:
        # No temperature/top_p/thinking/tool_choice: the default model rejects them (research R1).
        output_config: dict[str, Any] = {"effort": LLM_EFFORT}
        if request.output_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": request.output_schema}
        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": LLM_MAX_TOKENS,
            "system": request.system,
            "messages": request.messages,
        }
        if request.tools:
            body["tools"] = request.tools
        body["output_config"] = output_config
        return body


def post_json(
    client: httpx.Client,
    path: str,
    body: dict[str, Any],
    headers: dict[str, str],
    request: LlmRequest,
) -> httpx.Response:
    """POST `body` as JSON; network errors and timeouts become LlmUnavailableError."""
    all_headers = {**headers, "content-type": "application/json"}
    try:
        if request.timeout_s is None:
            return client.post(path, json=body, headers=all_headers)
        return client.post(path, json=body, headers=all_headers, timeout=request.timeout_s)
    except httpx.HTTPError as error:
        logger.warning("AI service unreachable: %s", type(error).__name__)
        raise LlmUnavailableError(UNAVAILABLE_MESSAGE) from error


def check_status(status: int) -> None:
    """429 is busy (rate limit or quota); 5xx (incl. 529 overloaded) is temporary; any other
    non-200 code means the request or settings are wrong (bad key, model, body, no credit)."""
    if status == HTTPStatus.OK:
        return
    logger.warning("AI service returned HTTP %d", status)
    if status == HTTPStatus.TOO_MANY_REQUESTS:
        raise LlmUnavailableError(BUSY_MESSAGE, code=LLM_BUSY_CODE)
    if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise LlmUnavailableError(UNAVAILABLE_MESSAGE)
    raise LlmConfigError(CONFIG_MESSAGE)
