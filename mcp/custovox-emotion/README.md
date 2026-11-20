# custovox-emotion

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

<!-- mcp-name: io.github.jeremdecustovox/custovox-emotion -->

MCP server that detects the emotion in English customer text, among 7 labels: joy, anger, fear, sadness, surprise, disgust, neutral.

## Quick start
```bash
pip install custovox-emotion
claude mcp add custovox-emotion -- uvx custovox-emotion
# Then ask Claude: "What emotion is in: 'Third time my order is late, this is unbelievable.'"
# Returns: dominant_emotion, confidence, scores of all 7 emotions
```
Models are downloaded from Hugging Face on first start, then everything runs locally.

## Tools
- `detect_emotion(text)`: `dominant_emotion`, `confidence`, `all_emotions` (score of each of the 7 labels)
- `detect_emotion_batch(texts)`: dominant emotion and confidence for up to 50 texts

## Limits
- **English only** (`j-hartmann/emotion-english-distilroberta-base`). For other languages, use [custovox-sentiment](https://pypi.org/project/custovox-sentiment/).
- Each text is read up to its first 512 characters.
- Use it to sort and spot patterns in text, not to judge a single customer.

## About
Built by [CustoVox.ai](https://custovox.ai). This free server runs on your machine with open models.
The hosted platform at [custovox.ai](https://custovox.ai) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
