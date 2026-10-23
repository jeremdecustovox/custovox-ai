# custovox-ticket-scorer

<!-- mcp-name: io.github.jeremdecustovox/custovox-ticket-scorer -->

Support ticket scoring MCP server.

## What it returns
- **Priority**: urgent / normal / low priority
- **Category**: billing issue, technical problem, delivery issue, product defect, account access, refund request, general inquiry, feature request
- **Sentiment**: Very Negative → Very Positive, multilingual (EN/FR/DE/ES/PT-BR)
- **Escalation risk**: low / medium / high (negative sentiment + urgent priority)

Priority and category use an English zero-shot model (facebook/bart-large-mnli): they are most
accurate on English tickets. Sentiment uses a multilingual model.
Batch mode: up to 20 tickets per call, sorted by escalation risk.

## Installation
pip install custovox-ticket-scorer

The models (about 2 GB) are downloaded from Hugging Face on first start and run on your machine.

## Need more?
**custovox.ai** — Full customer intelligence platform. From €49/month.
https://custovox.ai
