"""Client for the Khaya AI API: translation, speech-to-text and text-to-speech.

Version 0.2 targets the Khaya platform at https://api.khaya.ai. Keys from the
Khaya developer portal are sent as ``Authorization: Bearer <key>``. Errors are
raised as ``GhanaNLPError`` instead of being returned as dictionaries.
"""

import mimetypes
import os
from typing import Any, Optional

import requests

DEFAULT_BASE_URL = "https://api.khaya.ai"
DEFAULT_TIMEOUT = 30
SUPPORTED_SPEAKERS = frozenset({"male_low", "male_high", "female"})


class GhanaNLPError(Exception):
    """Raised when a request fails or the API returns an error.

    Attributes:
        message: Human-readable message.
        status_code: HTTP status, or None when the request never got a response.
        code: Platform error code such as ``INVALID_API_KEY``, when provided.
        activity_id: Request ID to quote when contacting support, when provided.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        activity_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.activity_id = activity_id


class GhanaNLP:
    """Client for translation, speech-to-text and text-to-speech.

    Args:
        api_key: Your Khaya API key. Defaults to the ``KHAYA_API_KEY`` environment variable.
        base_url: API root. Must be HTTPS.
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        key = api_key or os.environ.get("KHAYA_API_KEY")
        if not key:
            raise GhanaNLPError("API key is required: pass api_key or set KHAYA_API_KEY", 401)
        if not base_url.startswith("https://"):
            raise ValueError("base_url must use HTTPS")
        self.api_key = key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {key}"
        self.session.headers["Cache-Control"] = "no-cache"

    # Translation -----------------------------------------------------------

    def translate(self, text: str, language_pair: str = "eng-twi") -> str:
        """Translate text, for example ``eng-twi`` (English to Twi).

        Returns:
            The translated text.
        """
        if not text or not text.strip():
            raise GhanaNLPError("text is required", 400)
        body = self._post_json("/translate/v1/translate", {"in": text, "lang": language_pair})
        if isinstance(body, dict):
            return str(body.get("text", ""))
        return str(body)

    # Speech to text ---------------------------------------------------------

    def stt(self, audio_file_path: str, language: str = "twi") -> str:
        """Transcribe a WAV or other audio file to text."""
        with open(audio_file_path, "rb") as handle:
            data = handle.read()
        content_type = _content_type(audio_file_path)
        response = self._request(
            "POST",
            "/asr/v1/transcribe",
            params={"language": language},
            data=data,
            headers={"Content-Type": content_type},
        )
        body = response.json()
        if isinstance(body, dict):
            return str(body.get("text", ""))
        return str(body)

    speech_to_text = stt

    # Text to speech ---------------------------------------------------------

    def tts(self, text: str, lang: str = "twi", speaker: Optional[str] = None) -> bytes:
        """Synthesize speech. Returns the audio bytes (WAV).

        Args:
            text: Text to speak.
            lang: Language code, for example ``twi``, ``ewe`` or ``ga``.
            speaker: Optional voice: ``male_low``, ``male_high`` or ``female``.
        """
        if speaker is not None and speaker not in SUPPORTED_SPEAKERS:
            raise GhanaNLPError(
                f"Unknown speaker {speaker!r}. Supported speakers: {', '.join(sorted(SUPPORTED_SPEAKERS))}",
                400,
            )
        payload: dict[str, Any] = {"text": text, "language": lang}
        if speaker is not None:
            # The wire field is speaker_id; "speaker" is silently ignored by the API.
            payload["speaker_id"] = speaker
        response = self._request("POST", "/tts/v1/synthesize", json=payload)
        return response.content

    text_to_speech = tts

    # Internals --------------------------------------------------------------

    def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("POST", path, json=payload).json()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise GhanaNLPError(f"Request failed, check your connection: {exc}") from exc
        if response.status_code >= 400:
            raise _error_from(response)
        return response


def _content_type(audio_file_path: str) -> str:
    guessed, _ = mimetypes.guess_type(audio_file_path)
    if guessed is not None and guessed.startswith(("audio/", "video/")):
        return guessed
    return "application/octet-stream"


def _error_from(response: requests.Response) -> GhanaNLPError:
    """Build a GhanaNLPError from the platform's error body, which may not be JSON."""
    message = f"HTTP {response.status_code}"
    code = None
    activity_id = response.headers.get("X-Khaya-Request-Id") or response.headers.get("X-Correlation-ID")
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        detail = body.get("detail", body)
        if isinstance(detail, dict):
            message = str(detail.get("message") or detail.get("error") or message)
            code = detail.get("code") or detail.get("error")
            activity_id = detail.get("request_id") or activity_id
        elif detail:
            message = str(detail)
    return GhanaNLPError(message, response.status_code, code, activity_id)
