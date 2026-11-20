# custovox-review-analyzer

[![jeremdecustovox/custovox-ai MCP server](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai/badges/score.svg)](https://glama.ai/mcp/servers/jeremdecustovox/custovox-ai)

<!-- mcp-name: io.github.jeremdecustovox/custovox-review-analyzer -->

MCP server that analyzes a batch of customer reviews: overall sentiment, breakdown, and short summaries of what positive and negative reviews say.

## Quick start
```bash
pip install custovox-review-analyzer
claude mcp add custovox-review-analyzer -- uvx custovox-review-analyzer
# Then ask Claude: "Analyze these 40 reviews of our app: ..."
# Returns: overall_sentiment, average_score, sentiment_breakdown, top_positive_themes, top_negative_themes, recommendation
```
Models are downloaded from Hugging Face on first start, then everything runs locally.

## Tools
- `analyze_reviews(reviews, product_name)`: up to 100 reviews per call

## Limits
- Sentiment (5 levels) uses a multilingual model (English, French, German, Spanish, Portuguese among others).
- The summaries use an English model (`facebook/bart-large-cnn`): most accurate on English reviews, and based on the first 10 positive and 10 negative reviews only.
- The recommendation is a simple rule on the share of negative reviews (above 20%).
- About 2 GB of models are downloaded on first start.

## About
Built by [CustoVox.ai](https://custovox.ai). This free server runs on your machine with open models.
The hosted platform at [custovox.ai](https://custovox.ai) covers 5 languages, voice, text and images, with reports and integrations. From $89/month.
