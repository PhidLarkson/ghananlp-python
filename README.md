# Ghana NLP Python Library

A Python client for the Khaya AI API: **translation**, **speech-to-text** and **text-to-speech** for Ghanaian and other African languages.

Version 0.2 calls the Khaya platform at `https://api.khaya.ai`. If you're on 0.1.x, see [Upgrading from 0.1](#upgrading-from-01).

## Installation

```bash
pip install -U ghana-nlp
```

Requires Python 3.9 or later.

## Setup

Get an API key from the Khaya developer portal, then either pass it in or set `KHAYA_API_KEY`:

```bash
export KHAYA_API_KEY="your-api-key"
```

```python
from ghana_nlp import GhanaNLP

nlp = GhanaNLP()                      # reads KHAYA_API_KEY
nlp = GhanaNLP(api_key="your-key")    # or pass it in
```

## Translation

Pass a language pair such as `eng-twi` (English to Twi) or `twi-eng`:

```python
text = nlp.translate("Good morning", "eng-twi")
print(text)  # Mema wo akwaaba
```

## Speech to text

Transcribe a WAV or other audio file:

```python
text = nlp.stt("interview.wav", language="twi")
print(text)
```

`speech_to_text` is the same method under a longer name.

## Text to speech

`tts` returns WAV audio as bytes. Pick a language and, optionally, a voice:

```python
audio = nlp.tts("Maakye, akwaaba", lang="twi", speaker="female")
with open("output.wav", "wb") as f:
    f.write(audio)
```

Voices are `male_low`, `male_high` and `female`. `text_to_speech` is the same method under a longer name.

## Errors

Every failure raises `GhanaNLPError`, with these attributes:

| Attribute | Meaning |
| --- | --- |
| `message` | What went wrong |
| `status_code` | HTTP status, or `None` if the request never got a response |
| `code` | Platform code, such as `INVALID_API_KEY` |
| `activity_id` | Request ID to quote when contacting support |

```python
from ghana_nlp import GhanaNLP, GhanaNLPError

try:
    GhanaNLP().translate("Hello", "eng-twi")
except GhanaNLPError as err:
    print(err.status_code, err.code, err.message)
    print("Request ID:", err.activity_id)
```

## Upgrading from 0.1

| 0.1 | 0.2 |
| --- | --- |
| Calls `translation-api.ghananlp.org` | Calls `api.khaya.ai` |
| Sends `Ocp-Apim-Subscription-Key` | Sends `Authorization: Bearer <key>` |
| Returns error dictionaries | Raises `GhanaNLPError` |
| `translate(..., language_pair="en-tw")` | Default is `eng-twi` |
| `tts(text, lang="tw")` | Use `twi`. `tw` is not a language code on the new API |
| `tts` had no voice option | `tts(..., speaker=...)` |

Keys from the legacy GhanaNLP portal don't work with the new API. Create a key in the Khaya developer portal.

## Development

```bash
python -m unittest tests.test_api                     # offline unit tests
KHAYA_API_KEY=... python -m unittest tests.test_api   # also runs the live test
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
