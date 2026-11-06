# custovox-visual

<!-- mcp-name: io.github.jeremdecustovox/custovox-visual -->

MCP server for a first triage of customer-submitted photos (hotel rooms, product returns, retail, support tickets).

## What it returns
One tool, `analyze_customer_image(image_url, context="general")` — `image_url` is an image URL or the image as a base64 string:
- `description`: an English caption of the image
- `detected_issue`: the most likely issue category (cleanliness, damage or defect, missing item, safety, maintenance, presentation, incorrect item, packaging, or no visible issue; with `context="hospitality"`: room cleanliness, missing amenities, maintenance, bathroom, bed or linen, view or room quality, or no visible problem)
- `issue_confidence`: the score of that category
- `severity`: none / low / medium / high, derived from that score
- `suggested_action`

## How it works
- The image is captioned in English by `Salesforce/blip-image-captioning-base`.
- The caption is then classified into the issue categories with English zero-shot classification (`facebook/bart-large-mnli`). The category is inferred from the caption, not from the pixels directly: an issue the caption does not mention is not detected.
- `severity` reflects how confident the classification is, not how serious the issue is. Use it to sort photos for human review, not as a final verdict.
- Runs locally; the only network call is downloading the image when you pass a URL. Models are downloaded on first run.

## Installation
```
pip install custovox-visual
```

## Need more?
**custovox.ai** — Full customer intelligence platform. From $89/month.
https://custovox.ai
