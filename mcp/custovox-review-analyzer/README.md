# custovox-review-analyzer

<!-- mcp-name: io.github.jeremdecustovox/custovox-review-analyzer -->

Customer review analysis MCP server.

## What it returns
- Overall sentiment and average score (Very Negative → Very Positive)
- Sentiment breakdown (count and % per level)
- Up to 3 sentences summarizing the positive reviews, and 3 for the negative ones
- A simple recommendation based on the share of negative reviews

Sentiment is multilingual (EN/FR/DE/ES/PT-BR). The summaries use an English model
(facebook/bart-large-cnn): they are most accurate on English reviews.
Up to 100 reviews per call; the summaries are based on the first 10 positive and 10 negative reviews.

## Installation
pip install custovox-review-analyzer

The models (about 2 GB) are downloaded from Hugging Face on first start and run on your machine.

## Need more?
**custovox.ai** — Full customer intelligence platform. From $89/month.
https://custovox.ai
