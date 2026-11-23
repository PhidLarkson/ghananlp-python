# Changelog

All notable changes to this project are documented here.

## [0.2.0]

Moves the library to the Khaya platform at `https://api.khaya.ai`.

### Changed (breaking)

- Requests use `Authorization: Bearer <key>`. The `Ocp-Apim-Subscription-Key` header is no longer sent.
- Routes are `/translate/v1/translate`, `/asr/v1/transcribe` and `/tts/v1/synthesize`.
- Errors are raised as `GhanaNLPError` (with `status_code`, `code` and `activity_id`) instead of being returned as dictionaries.
- The default translation pair is `eng-twi`.
- The default speech language is `twi`. `tw` is not a language code on the new API.

### Added

- The API key defaults to the `KHAYA_API_KEY` environment variable.
- `tts(..., speaker=...)` with `male_low`, `male_high` or `female`. An unknown voice is rejected before the request.
- `speech_to_text` and `text_to_speech` as longer names for `stt` and `tts`.
- Offline unit tests, and a live test that runs when `KHAYA_API_KEY` is set.

### Fixed

- Speech uploads use a Content-Type taken from the file extension.
- The README examples match the methods and language codes the library provides.

## [0.1.5]

Previous release, which called `translation-api.ghananlp.org`.
