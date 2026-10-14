"""
Groq LLM Client & Provider Configuration for Market Orbit.

Phase 5.2: Secure, production-ready Groq API client with connection reuse,
configurable model/timeout settings, error sanitization, and compatibility wrappers.
"""

import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional
import groq
from groq import Groq


# Default model and connection settings
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_TIMEOUT = 15.0
DEFAULT_GROQ_MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Exception Hierarchy
# ---------------------------------------------------------------------------

class GroqClientError(Exception):
    """Base exception for all Groq client and provider communication errors."""
    pass


class GroqConfigurationError(GroqClientError):
    """Raised when Groq API key or required client configuration is missing or invalid."""
    pass


class GroqAuthenticationError(GroqClientError):
    """Raised when Groq API authentication fails (401/403)."""
    pass


class GroqRateLimitError(GroqClientError):
    """Raised when Groq API rate limits or quota are exceeded (429)."""
    pass


class GroqTimeoutError(GroqClientError):
    """Raised when request to Groq API times out."""
    pass


class GroqConnectionError(GroqClientError):
    """Raised when network connectivity or DNS resolution fails."""
    pass


class GroqEmptyResponseError(GroqClientError):
    """Raised when Groq returns an empty choices array or empty text content."""
    pass


class GroqAPIError(GroqClientError):
    """Raised for server-side or unhandled Groq API response errors."""
    pass


# ---------------------------------------------------------------------------
# Configuration Resolver
# ---------------------------------------------------------------------------

def load_groq_config() -> Dict[str, Any]:
    """
    Safely resolves Groq settings across environment, backend config, and dotenv files.

    Order of resolution:
    1. Direct environment variables (GROQ_API_KEY, GROQ_MODEL, GROQ_TIMEOUT, GROQ_MAX_RETRIES)
    2. Backend app.core.config.settings (if importable)
    3. Ignored .env files (.env or backend/.env) via python-dotenv
    """
    config: Dict[str, Any] = {
        "api_key": os.getenv("GROQ_API_KEY", "").strip(),
        "model": os.getenv("GROQ_MODEL", "").strip(),
        "timeout": None,
        "max_retries": None,
    }

    # Parse timeout from env if present
    env_timeout = os.getenv("GROQ_TIMEOUT")
    if env_timeout:
        try:
            config["timeout"] = float(env_timeout)
        except ValueError:
            pass

    # Parse max_retries from env if present
    env_retries = os.getenv("GROQ_MAX_RETRIES")
    if env_retries:
        try:
            config["max_retries"] = int(env_retries)
        except ValueError:
            pass

    # Try backend settings if api_key or model not found
    if not config["api_key"] or not config["model"] or config["timeout"] is None:
        try:
            backend_dir = str(Path(__file__).resolve().parents[2] / "backend")
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            # pyrefly: ignore [missing-import]
            from app.core.config import settings

            if not config["api_key"] and getattr(settings, "GROQ_API_KEY", None):
                config["api_key"] = settings.GROQ_API_KEY.strip()
            if not config["model"] and getattr(settings, "GROQ_MODEL", None):
                config["model"] = settings.GROQ_MODEL.strip()
            if config["timeout"] is None and getattr(settings, "GROQ_TIMEOUT", None) is not None:
                config["timeout"] = float(settings.GROQ_TIMEOUT)
            if config["max_retries"] is None and getattr(settings, "GROQ_MAX_RETRIES", None) is not None:
                config["max_retries"] = int(settings.GROQ_MAX_RETRIES)
        except Exception:
            pass

    # Try reading .env / backend/.env directly if api_key still empty
    if not config["api_key"]:
        try:
            from dotenv import dotenv_values
            root_dir = Path(__file__).resolve().parents[2]
            for env_path in [root_dir / "backend" / ".env", root_dir / ".env"]:
                if env_path.is_file():
                    vals = dotenv_values(env_path)
                    if vals.get("GROQ_API_KEY"):
                        config["api_key"] = str(vals["GROQ_API_KEY"]).strip()
                    if not config["model"] and vals.get("GROQ_MODEL"):
                        config["model"] = str(vals["GROQ_MODEL"]).strip()
                    if config["timeout"] is None and vals.get("GROQ_TIMEOUT"):
                        try:
                            config["timeout"] = float(vals["GROQ_TIMEOUT"])
                        except ValueError:
                            pass
                    break
        except Exception:
            pass

    # Apply defaults for unset configuration
    if not config["model"]:
        config["model"] = DEFAULT_GROQ_MODEL
    if config["timeout"] is None:
        config["timeout"] = DEFAULT_GROQ_TIMEOUT
    if config["max_retries"] is None:
        config["max_retries"] = DEFAULT_GROQ_MAX_RETRIES

    return config


# ---------------------------------------------------------------------------
# GroqClient Implementation
# ---------------------------------------------------------------------------

class GroqClient:
    """
    Secure client for the Groq Cloud API.

    Manages groq.Groq instance lifecycle, connection reuse, chat completions,
    error sanitization, and compatibility fallbacks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        resolved = load_groq_config()

        self._api_key: str = (api_key.strip() if api_key else "") or resolved["api_key"]
        self.model: str = (model.strip() if model else "") or resolved["model"]
        self.timeout: float = float(timeout) if timeout is not None else resolved["timeout"]
        self.max_retries: int = int(max_retries) if max_retries is not None else resolved["max_retries"]

        if self.timeout <= 0:
            raise GroqConfigurationError("Request timeout must be a positive number of seconds.")
        if self.max_retries < 0:
            raise GroqConfigurationError("Max retries must be a non-negative integer.")

        self._client: Optional[Groq] = None

    @property
    def is_configured(self) -> bool:
        """Indicates whether a non-empty API key is available."""
        return bool(self._api_key)

    @property
    def client(self) -> Groq:
        """Returns the lazily initialized, shared Groq SDK client instance."""
        if not self._api_key:
            raise GroqConfigurationError(
                "GROQ_API_KEY is not configured. Provide an API key or configure it in your environment."
            )
        if self._client is None:
            self._client = Groq(
                api_key=self._api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._client

    def _sanitize(self, text: str) -> str:
        """Removes API key or secret token signatures from text."""
        if not text:
            return ""
        if self._api_key and self._api_key in text:
            text = text.replace(self._api_key, "[REDACTED_API_KEY]")
        text = re.sub(r"gsk_[a-zA-Z0-9_-]{10,}", "[REDACTED_API_KEY]", text)
        return text

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Submits a chat completion request to the Groq API and extracts the response string.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Optional model override; defaults to self.model.
            temperature: Sampling temperature (default 0.2 for deterministic output).
            max_tokens: Maximum tokens in completion.

        Returns:
            The extracted text content string from the top choice.

        Raises:
            GroqConfigurationError: If API key is missing or invalid.
            GroqAuthenticationError: If API key fails authentication (401/403).
            GroqRateLimitError: If rate limit is hit (429).
            GroqTimeoutError: If request times out.
            GroqConnectionError: If network connectivity fails.
            GroqEmptyResponseError: If response payload contains empty content.
            GroqAPIError: For other API status failures.
            GroqClientError: For general client failures.
        """
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be a non-empty list of message dictionaries.")

        target_model = model or self.model
        client = self.client  # Raises GroqConfigurationError if unconfigured

        try:
            kwargs: Dict[str, Any] = {
                "messages": messages,
                "model": target_model,
                "temperature": temperature,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens

            response = client.chat.completions.create(**kwargs)
        except (groq.AuthenticationError, groq.PermissionDeniedError) as exc:
            raise GroqAuthenticationError(self._sanitize(str(exc))) from exc
        except groq.RateLimitError as exc:
            raise GroqRateLimitError(self._sanitize(str(exc))) from exc
        except groq.APITimeoutError as exc:
            raise GroqTimeoutError(self._sanitize(str(exc))) from exc
        except groq.APIConnectionError as exc:
            raise GroqConnectionError(self._sanitize(str(exc))) from exc
        except (groq.BadRequestError, groq.InternalServerError, groq.APIStatusError, groq.APIError) as exc:
            raise GroqAPIError(self._sanitize(str(exc))) from exc
        except groq.GroqError as exc:
            raise GroqClientError(self._sanitize(str(exc))) from exc
        except Exception as exc:
            raise GroqClientError(self._sanitize(str(exc))) from exc

        # Extract and validate response content
        if not response or not getattr(response, "choices", None):
            raise GroqEmptyResponseError("Groq API returned an empty or invalid choices payload.")

        choice = response.choices[0]
        msg = getattr(choice, "message", None)
        if msg is None:
            raise GroqEmptyResponseError("Groq response choice does not contain a message object.")

        content = getattr(msg, "content", None)
        if content is None or not str(content).strip():
            raise GroqEmptyResponseError("Groq response message contains empty text content.")

        return str(content).strip()

    def generate_recommendations(
        self,
        kpi_data: Dict[str, Any],
        rankings: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Compatibility wrapper for existing analytics callers (AnalysisService).

        NOTE: In Phase 5.2, the full prompt-building and output-parsing pipeline
        is under development (scheduled for Phase 5.3-5.5). This method returns
        deterministic fallback recommendations with explicit attribution.
        """
        return [
            {
                "title": "Scale High-ROAS Campaigns",
                "description": "Increase budget for top-performing channels demonstrating ROAS > 3.0x.",
                "action": "Increase Budget by 20%",
                "source": "deterministic_fallback",
            },
            {
                "title": "Pause Underperforming Creatives",
                "description": "Reallocate spend from campaigns with high CPA and low conversion rates.",
                "action": "Pause Low-Performing Ad Sets",
                "source": "deterministic_fallback",
            },
        ]

    def __repr__(self) -> str:
        return f"<GroqClient model='{self.model}' timeout={self.timeout}s configured={self.is_configured}>"

    def __str__(self) -> str:
        return self.__repr__()
