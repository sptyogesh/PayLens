"""The single LLM wrapper (Principle IX): Anthropic Messages API over httpx (research R1).

Provider URL, model and key come from settings. The key is sent only in the request header and
is never logged. No retry loop: the chat must answer within the timeout (FR-009).
"""

import logging
from http import HTTPStatus
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.common.constants import LLM_API_VERSION, LLM_EFFORT, LLM_MAX_TOKENS
from app.common.errors import LlmConfigError, LlmUnavailableError

logger = logging.getLogger(__name__)

MESSAGES_PATH = "/v1/messages"
UNAVAILABLE_MESSAGE = "The AI service is not available right now."
CONFIG_MESSAGE = "The AI service rejected the request. Check the LLM settings."
UNAVAILABLE_STATUSES = frozenset({HTTPStatus.TOO_MANY_REQUESTS})


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
        response = self._post(self._body(request), request.timeout_s)
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

    def _post(self, body: dict[str, Any], timeout_s: float | None) -> httpx.Response:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": LLM_API_VERSION,
            "content-type": "application/json",
        }
        try:
            if timeout_s is None:
                return self._client.post(MESSAGES_PATH, json=body, headers=headers)
            return self._client.post(MESSAGES_PATH, json=body, headers=headers, timeout=timeout_s)
        except httpx.HTTPError as error:
            logger.warning("AI service unreachable: %s", type(error).__name__)
            raise LlmUnavailableError(UNAVAILABLE_MESSAGE) from error


def check_status(status: int) -> None:
    """429 and 5xx (incl. 529 overloaded) are temporary; other non-200 codes are config errors."""
    if status == HTTPStatus.OK:
        return
    logger.warning("AI service returned HTTP %d", status)
    if status in UNAVAILABLE_STATUSES or status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise LlmUnavailableError(UNAVAILABLE_MESSAGE)
    raise LlmConfigError(CONFIG_MESSAGE)
