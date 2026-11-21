# custovox-ticket-scorer

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

<!-- mcp-name: io.github.jeremdecustovox/custovox-ticket-scorer -->

MCP server that scores support tickets: priority, category, sentiment and escalation risk, to decide which ticket to handle first.

## Quick start
```bash
pip install custovox-ticket-scorer
claude mcp add custovox-ticket-scorer -- uvx custovox-ticket-scorer
# Then ask Claude: "Score this ticket: 'I was charged twice and nobody answers my emails.'"
# Returns: priority, category, sentiment, escalation_risk (+ confidences)
```
Models are downloaded from Hugging Face on first start, then everything runs locally.

## Tools
- `score_ticket(text)`: `priority` (urgent / normal / low priority), `category` (billing issue, technical problem, delivery issue, product defect, account access, refund request, general inquiry, feature request), `sentiment` (5 levels), `escalation_risk` (low / medium / high), each with a confidence
- `score_ticket_batch(tickets)`: up to 20 tickets, sorted by escalation risk

## Limits
- Priority and category come from an English zero-shot model (`facebook/bart-large-mnli`): most accurate on English tickets.
- Sentiment uses a multilingual model (English, French, German, Spanish, Portuguese among others).
- Escalation risk is a simple rule: negative sentiment and urgent priority gives high; one of the two gives medium.
- Each ticket is read up to its first 512 characters. About 2 GB of models are downloaded on first start.

## About
Built by [CustoVox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11). This free server runs on your machine with open models.
The hosted platform at [custovox.ai](https://custovox.ai/?utm_source=github&utm_medium=readme&utm_campaign=devcampagne-2026-11) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
