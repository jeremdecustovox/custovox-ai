# custovox.ai — open-source customer-intelligence MCP servers

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

Free MCP servers that let Claude (or any MCP client) read what customers say: sentiment, emotions, support tickets, reviews, churn signals, photos and calls. They run on your machine with open models.

Built by [CustoVox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11).

## MCP servers

| Server | What it does | Languages | PyPI |
|---|---|---|---|
| [custovox-sentiment](mcp/custovox-sentiment) | 5-level sentiment of customer text, batch up to 50 | One multilingual model (EN, FR, DE, ES, PT among others) | [custovox-sentiment](https://pypi.org/project/custovox-sentiment/) |
| [custovox-emotion](mcp/custovox-emotion) | 7 emotions (joy, anger, fear, sadness, surprise, disgust, neutral) | English only | [custovox-emotion](https://pypi.org/project/custovox-emotion/) |
| [custovox-ticket-scorer](mcp/custovox-ticket-scorer) | Ticket priority, category, sentiment and escalation risk | Sentiment multilingual; priority and category best in English | [custovox-ticket-scorer](https://pypi.org/project/custovox-ticket-scorer/) |
| [custovox-review-analyzer](mcp/custovox-review-analyzer) | Sentiment breakdown and summaries of up to 100 reviews | Sentiment multilingual; summaries best in English | [custovox-review-analyzer](https://pypi.org/project/custovox-review-analyzer/) |
| [custovox-churn-signal](mcp/custovox-churn-signal) | Rule-based churn-risk score 0–100 from a customer's messages | Sentiment multilingual; intent detection best in English | [custovox-churn-signal](https://pypi.org/project/custovox-churn-signal/) |
| [custovox-visual](mcp/custovox-visual) | First triage of customer photos (rooms, returns, retail) | English captions | [custovox-visual](https://pypi.org/project/custovox-visual/) |
| [custovox-calls](mcp/custovox-calls) | Call analysis: sentiment, contact reasons, churn threats, follow-up actions; demo mode | Simple rules, French and English | [custovox-calls](https://pypi.org/project/custovox-calls/) |

All seven are listed in the [official MCP registry](https://registry.modelcontextprotocol.io) under `io.github.jeremdecustovox/`.

## Library

| Package | What it does | PyPI |
|---|---|---|
| [callscope-ai](mcp/callscope-ai) | Python library behind custovox-calls (not an MCP server): one JSON per call with transcript, agent/customer turns, sentiment curve, contact reasons and key moments | [callscope-ai](https://pypi.org/project/callscope-ai/) |

## Quick start

```bash
claude mcp add custovox-calls-demo --env CUSTOVOX_CALLS_DEMO=1 -- uvx custovox-calls
# Then ask Claude: "Which demo calls had a churn threat, and what should we do?"
```

Each server's README has its own quick start, tools and limits.

## Limits

These servers are meant to sort and prioritize customer feedback for human review. They use open models and simple, readable rules; several parts work best in English (see each README).

## More

The hosted platform at [custovox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11) covers 5 languages, voice, text and images, with reports and integrations.

MIT License.
