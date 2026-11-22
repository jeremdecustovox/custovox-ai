# custovox-calls

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

<!-- mcp-name: io.github.jeremdecustovox/custovox-calls -->

An MCP server that lets Claude analyze customer-service calls: sentiment, contact reasons, complaints, churn threats and agent promises, then suggest follow-up actions. Everything runs on your machine.

Built on [callscope-ai](https://pypi.org/project/callscope-ai/).

![Demo mode: custovox-calls lists the fictional calls with a churn threat and suggests a manager alert, a customer callback and a CRM ticket](https://custovox.ai/images/demo/custovox-calls-demo-en.gif)

*Demo mode, fictional calls. The analysis uses simple French/English keyword rules.*

## Install

```bash
pip install custovox-calls              # transcripts (JSON segments) and demo mode
pip install "custovox-calls[whisper]"   # + local transcription of audio files (faster-whisper)
```

## Quick start

```bash
# try it with 6 fictional calls, no audio needed
claude mcp add custovox-calls-demo --env CUSTOVOX_CALLS_DEMO=1 -- uvx custovox-calls

# your own calls
claude mcp add custovox-calls -- uvx --from "custovox-calls[whisper]" custovox-calls
```

Then ask: *"Analyze ~/calls/2026-11-18-0912.wav"*, *"What did customers complain about this month?"*, *"Which calls had a churn threat?"*, *"What should we do after call demo-1?"*

## Use in Claude Desktop

```json
{
  "mcpServers": {
    "custovox-calls": {
      "command": "uvx",
      "args": ["--from", "custovox-calls[whisper]", "custovox-calls"]
    }
  }
}
```

## Tools

| Tool | What it does |
|---|---|
| `analyze_call(source, call_id, started_at, language)` | Analyze one call and save it. `source`: local audio file, http(s) URL to an audio file, local JSON file of segments `[{start, end, text}]`, or a demo call (`demo-1` … `demo-6`) |
| `get_call_insights(since, until)` | Summary over a period: calls, minutes, mean customer sentiment, contact reasons, churn threats, most negative calls |
| `search_feedback(query, speaker, since, until)` | Find what customers (or agents) said; case and accents ignored |
| `suggest_actions(call_id)` | Manager alert, customer callback, CRM ticket, each with its reason and the sentence that triggered it. Sends nothing |
| `send_action(action_id)` | Only when `CUSTOVOX_CALLS_WEBHOOK_URL` is set: posts one suggested action to your webhook (Slack, Zapier, Make, a CRM…) |

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CUSTOVOX_CALLS_DB` | `~/.custovox-calls/calls.db` | SQLite file holding the analyzed calls |
| `CUSTOVOX_CALLS_DEMO` | off | `1`: in-memory database preloaded with 6 fictional calls |
| `CUSTOVOX_CALLS_WEBHOOK_URL` | none | Enables `send_action`. The JSON payload has a `text` field, so Slack incoming webhooks display it as is |
| `CUSTOVOX_CALLS_WHISPER_MODEL` | `small` | faster-whisper model size |

## Privacy and limits

- Call recordings and transcripts contain personal data. Audio is transcribed locally and the analysis is stored in a local SQLite file; nothing is sent anywhere, except by `send_action` to the webhook you configured.
- Speaker detection (agent or customer), sentiment and contact reasons come from simple, inspectable rules in callscope-ai, in French and English. Use them to sort and prioritize calls, and check important cases by listening to them.

## Development

```bash
pip install -e ".[test]" && pytest   # no network, no audio, no model
```

MIT licensed.

## About
Built by [CustoVox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11). This free tool runs on your machine.
The hosted platform at [custovox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
