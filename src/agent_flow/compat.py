"""
Compatibility layer for OpenAI Agents SDK.
All SDK imports go through here to isolate against API changes.
"""

from typing import Any, Dict
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()




from agents import Agent
from agents.items import MessageOutputItem as Message

from openai import AsyncOpenAI
from agents import set_default_openai_client, set_tracing_disabled, set_default_openai_api


_api_key = os.getenv("OPENAI_API_KEY")
_base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
_response_type = os.getenv("OPENAI_RESPONSE_TYPE", "responses").lower() or "responses"

if not _api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not _base_url:
    raise ValueError("OPENAI_BASE_URL environment variable is not set")


if _response_type not in ["chat_completions", "responses"]:
    raise ValueError("OPENAI_RESPONSE_TYPE must be either 'chat_completions' or 'responses'")

_shared_client = AsyncOpenAI(
    api_key=_api_key,
    base_url=_base_url
)




set_default_openai_client(_shared_client)

# Configure API type based on environment variable
# Default is "completions" (chat_completions) since most LLM providers don't support the Responses API
# Set OPENAI_RESPONSE_TYPE=responses to use the Responses API (requires OpenAI or compatible provider)
api_type = "chat_completions" if _response_type == "chat_completions" else "responses"
set_default_openai_api(api_type)

# disable if base api is not openai
if not "openai.com" in _base_url:
    set_tracing_disabled(True)
else:
    set_tracing_disabled(False)




# Re-export SDK types for internal use
__all__ = [

    "get_shared_client",
]


def get_shared_client() -> AsyncOpenAI:
    """Get the shared OpenAI client configured with environment variables."""
    return _shared_client