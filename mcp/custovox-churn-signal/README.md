# custovox-churn-signal

<!-- mcp-name: io.github.jeremdecustovox/custovox-churn-signal -->

MCP server that scores the churn risk of a customer from the sequence of their messages (tickets, emails, chats), oldest first.

## Quick start
```bash
pip install custovox-churn-signal
claude mcp add custovox-churn-signal -- uvx custovox-churn-signal
# Then ask Claude: "Score the churn risk of this customer from their last 5 messages: ..."
# Returns: churn_risk_score (0-100), risk_level, trend, key_signals, recommendation
```
Models are downloaded from Hugging Face on first start, then everything runs locally.

## What it returns
One tool, `score_churn_risk(messages, customer_id="unknown")`:
- `churn_risk_score`: 0-100 (higher = more at risk)
- `risk_level`: low / medium / high / critical
- `trend`: improving / stable / degrading / critical (sentiment of the second half of the messages vs the first half, from 3 messages)
- `key_signals`: the warning signals found (negative last message, degrading trend, explicit intent to cancel or switch to a competitor, share of negative messages)
- `recommendation`: a suggested follow-up action
- `messages_analyzed`

## How it works
- Each message gets a 5-level sentiment (Very Negative → Very Positive) from one multilingual model (`tabularisai/multilingual-sentiment-analysis`; English, French, German, Spanish and Portuguese among the languages its model card lists).
- The last message is checked for an explicit intent to cancel or to switch to a competitor with English zero-shot classification (`facebook/bart-large-mnli`), so this signal is most reliable in English.
- The score is a transparent rule-based combination of these signals (average sentiment, trend, intent). It is a ranking to prioritize follow-up, not a trained or validated churn prediction.
- Up to 20 messages per call; each message is read up to its first 512 characters. Runs locally: messages are not sent anywhere. Models are downloaded on first run.

## About
Built by [CustoVox.ai](https://custovox.ai). This free server runs on your machine with open models.
The hosted platform at [custovox.ai](https://custovox.ai) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
