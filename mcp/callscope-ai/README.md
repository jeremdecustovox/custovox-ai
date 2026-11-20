# callscope-ai

Python library (imported as `callscope`) to analyze customer-service calls locally: timestamped transcript, who speaks when, sentiment curve, contact reasons and key moments, in one JSON.

## Install

```bash
pip install callscope-ai              # analysis of transcripts (no dependencies)
pip install "callscope-ai[whisper]"   # + local transcription of audio (faster-whisper)
```

## Use

```python
import callscope

result = callscope.analyze("call.wav")                 # audio -> full analysis
result = callscope.analyze([{"start": 0, "end": 3, "text": "Bonjour, comment puis-je vous aider ?"}])
```

```bash
callscope demo                      # fictional call, no audio, no model
callscope analyze call.wav --model small
callscope analyze segments.json
```

French and English keyword lexicons are built in; everything runs on your machine.

## Functions

| Function | Returns |
|---|---|
| `transcribe(path, model_size, language)` | `[{start, end, text}]` (needs the `whisper` extra) |
| `diarize(segments, channel_roles=None)` | segments with `speaker` = `agent` or `customer` (stereo channels, else turn-taking heuristic) |
| `sentiment(segments)` | per-segment score (-1..1), customer curve, mean and trend |
| `contact_reasons(segments)` | ranked reasons: billing, cancellation, outage, delivery, technical_support, subscription_change |
| `key_moments(segments)` | complaints, churn threats, agent promises |
| `analyze(source)` | everything above in one dict |

## Output format (`callscope/1`)

`analyze()` returns `{schema, source, duration, segments, sentiment, contact_reasons, key_moments}`. This is the shared format for tools built on callscope.

## Limits

- French and English only: sentiment, contact reasons and key moments come from small keyword lists (`lexicon.py`), whole-word matching.
- Speaker separation (agent or customer) is a heuristic: stereo channels if given, else turn-taking on silences and greeting phrases.
- Simple, inspectable baselines to sort calls for human review, not state-of-the-art models.

To use it from Claude, see the MCP server [custovox-calls](https://pypi.org/project/custovox-calls/).

MIT licensed. Run tests with `pip install -e ".[test]" && pytest` (no network).

## About
Built by [CustoVox.ai](https://custovox.ai). This free tool runs on your machine.
The hosted platform at [custovox.ai](https://custovox.ai) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
