# custovox-sentiment

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

<!-- mcp-name: io.github.jeremdecustovox/custovox-sentiment -->

MCP server that rates the sentiment of customer text (reviews, tickets, emails, chat messages) on 5 levels: Very Negative, Negative, Neutral, Positive, Very Positive.

## Quick start
```bash
pip install custovox-sentiment
claude mcp add custovox-sentiment -- uvx custovox-sentiment
# Then ask Claude: "Rate the sentiment of: 'I have been waiting three weeks for my refund.'"
# Returns: sentiment (5 levels), confidence (0-1), text_length
```
Models are downloaded from Hugging Face on first start, then everything runs locally.

## Tools
- `analyze_sentiment(text)`: `sentiment`, `confidence`, `text_length`
- `analyze_batch(texts)`: the same for up to 50 texts, with a `text_preview` of each

## Limits
- One multilingual model (`tabularisai/multilingual-sentiment-analysis`); its model card lists 23 languages, including English, French, German, Spanish and Portuguese.
- Each text is read up to its first 512 characters.
- A single label per text: mixed opinions in one text are not split.

## Anonymous usage statistics
To understand how the server is used, each analysis sends an anonymous counter: tool name, sentiment label(s), number of texts, package version and a random ID regenerated at every start.
The analyzed text is never sent.

To disable it, set the environment variable `CUSTOVOX_TELEMETRY=0`.

## About
Built by [CustoVox.ai](https://custovox.ai). This free server runs on your machine with open models.
The hosted platform at [custovox.ai](https://custovox.ai) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
