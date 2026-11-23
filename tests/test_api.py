"""Unit tests run offline. The live test runs only when KHAYA_API_KEY is set."""

import os
import tempfile
import unittest
from unittest import mock

import requests

from ghana_nlp import GhanaNLP, GhanaNLPError


def _response(status=200, json_body=None, content=b"", headers=None):
    response = requests.Response()
    response.status_code = status
    response._content = content if json_body is None else __import__("json").dumps(json_body).encode()
    response.headers.update(headers or {})
    return response


class TestClientSetup(unittest.TestCase):
    def test_uses_bearer_auth_and_new_base_url(self) -> None:
        client = GhanaNLP(api_key="k")
        self.assertEqual(client.base_url, "https://api.khaya.ai")
        self.assertEqual(client.session.headers["Authorization"], "Bearer k")
        self.assertNotIn("Ocp-Apim-Subscription-Key", client.session.headers)

    def test_reads_key_from_environment(self) -> None:
        with mock.patch.dict(os.environ, {"KHAYA_API_KEY": "from-env"}):
            self.assertEqual(GhanaNLP().api_key, "from-env")

    def test_missing_key_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(GhanaNLPError) as ctx:
                GhanaNLP()
        self.assertEqual(ctx.exception.status_code, 401)

    def test_rejects_http_base_url(self) -> None:
        with self.assertRaises(ValueError):
            GhanaNLP(api_key="k", base_url="http://example.com")


class TestTranslate(unittest.TestCase):
    def setUp(self) -> None:
        self.client = GhanaNLP(api_key="k")

    def test_posts_to_v1_route_and_returns_text(self) -> None:
        with mock.patch.object(self.client.session, "request", return_value=_response(json_body={"text": "Mema wo akwaaba"})) as req:
            result = self.client.translate("Welcome", "eng-twi")
        self.assertEqual(result, "Mema wo akwaaba")
        args, kwargs = req.call_args
        self.assertEqual(args[1], "https://api.khaya.ai/translate/v1/translate")
        self.assertEqual(kwargs["json"], {"in": "Welcome", "lang": "eng-twi"})

    def test_accepts_bare_string_response(self) -> None:
        with mock.patch.object(self.client.session, "request", return_value=_response(json_body="Akpe")):
            self.assertEqual(self.client.translate("Thanks", "eng-twi"), "Akpe")

    def test_empty_text_raises_before_request(self) -> None:
        with mock.patch.object(self.client.session, "request") as req:
            with self.assertRaises(GhanaNLPError):
                self.client.translate("  ", "eng-twi")
        req.assert_not_called()


class TestTextToSpeech(unittest.TestCase):
    def test_unknown_speaker_raises_before_request(self) -> None:
        client = GhanaNLP(api_key="k")
        with mock.patch.object(client.session, "request") as req:
            with self.assertRaises(GhanaNLPError) as ctx:
                client.tts("Hello", "twi", speaker="nobody")
        req.assert_not_called()
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("female", str(ctx.exception))

    def test_sends_speaker_as_speaker_id(self) -> None:
        client = GhanaNLP(api_key="k")
        with mock.patch.object(client.session, "request", return_value=_response(content=b"RIFF")) as req:
            audio = client.tts("Hello", "twi", speaker="female")
        self.assertEqual(audio, b"RIFF")
        args, kwargs = req.call_args
        self.assertEqual(args[1], "https://api.khaya.ai/tts/v1/synthesize")
        self.assertEqual(kwargs["json"], {"text": "Hello", "language": "twi", "speaker_id": "female"})

    def test_default_language_is_twi(self) -> None:
        client = GhanaNLP(api_key="k")
        with mock.patch.object(client.session, "request", return_value=_response(content=b"RIFF")) as req:
            client.text_to_speech("Hello")
        self.assertEqual(req.call_args.kwargs["json"]["language"], "twi")


class TestSpeechToText(unittest.TestCase):
    def test_uploads_wav_with_audio_content_type(self) -> None:
        client = GhanaNLP(api_key="k")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"RIFFfake")
        try:
            with mock.patch.object(client.session, "request", return_value=_response(json_body={"text": "na akye"})) as req:
                text = client.stt(tmp.name, "twi")
        finally:
            os.unlink(tmp.name)
        self.assertEqual(text, "na akye")
        args, kwargs = req.call_args
        self.assertEqual(args[1], "https://api.khaya.ai/asr/v1/transcribe")
        self.assertEqual(kwargs["params"], {"language": "twi"})
        self.assertEqual(kwargs["headers"]["Content-Type"], "audio/x-wav")


class TestErrors(unittest.TestCase):
    def test_platform_error_body_is_raised_with_code_and_request_id(self) -> None:
        client = GhanaNLP(api_key="bad")
        body = {"detail": {"error": "INVALID_API_KEY", "message": "API key not found or revoked", "request_id": "abc-123"}}
        with mock.patch.object(client.session, "request", return_value=_response(status=401, json_body=body)):
            with self.assertRaises(GhanaNLPError) as ctx:
                client.translate("Hello", "eng-twi")
        err = ctx.exception
        self.assertEqual(err.status_code, 401)
        self.assertEqual(err.code, "INVALID_API_KEY")
        self.assertEqual(err.activity_id, "abc-123")
        self.assertIn("revoked", err.message)

    def test_non_json_error_body_still_raises(self) -> None:
        client = GhanaNLP(api_key="k")
        with mock.patch.object(client.session, "request", return_value=_response(status=502, content=b"<html>bad gateway</html>")):
            with self.assertRaises(GhanaNLPError) as ctx:
                client.tts("Hello")
        self.assertEqual(ctx.exception.status_code, 502)

    def test_connection_failure_is_wrapped(self) -> None:
        client = GhanaNLP(api_key="k")
        with mock.patch.object(client.session, "request", side_effect=requests.ConnectionError("down")):
            with self.assertRaises(GhanaNLPError) as ctx:
                client.translate("Hello", "eng-twi")
        self.assertIsNone(ctx.exception.status_code)


@unittest.skipUnless(os.environ.get("KHAYA_API_KEY"), "set KHAYA_API_KEY to run live tests")
class TestLive(unittest.TestCase):
    def test_translate_live(self) -> None:
        self.assertTrue(GhanaNLP().translate("Good morning", "eng-twi"))


if __name__ == "__main__":
    unittest.main()
