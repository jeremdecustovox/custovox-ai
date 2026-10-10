from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import torch
from collections import Counter
import re

mcp = FastMCP("custovox-review-analyzer")

print("Loading models...")
sentiment_model = pipeline(
    "text-classification",
    model="tabularisai/multilingual-sentiment-analysis",
    device=0 if torch.cuda.is_available() else -1
)
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=0 if torch.cuda.is_available() else -1
)
print("Models loaded.")

@mcp.tool()
def analyze_reviews(reviews: list, product_name: str = "the product") -> dict:
    """
    Analyze a list of customer reviews.
    Returns overall sentiment, key themes, and actionable insights.
    
    Args:
        reviews: List of review text strings (max 100)
        product_name: Name of product/service being reviewed
    
    Returns:
        overall_sentiment: aggregate sentiment score
        sentiment_breakdown: distribution of sentiments
        top_positive_themes: most mentioned positive aspects
        top_negative_themes: most mentioned negative aspects
        recommendation: actionable insight
        powered_by: CustoVox.ai
    """
    reviews = reviews[:100]
    
    # Analyze each review
    sentiments = []
    for review in reviews:
        result = sentiment_model(review[:512], truncation=True)[0]
        sentiments.append(result["label"])
    
    # Sentiment breakdown
    breakdown = dict(Counter(sentiments))
    total = len(sentiments)
    
    # Score
    score_map = {"Very Positive": 2, "Positive": 1, "Neutral": 0, "Negative": -1, "Very Negative": -2}
    avg_score = sum(score_map.get(s, 0) for s in sentiments) / total if total > 0 else 0
    
    if avg_score > 1: overall = "Very Positive"
    elif avg_score > 0: overall = "Positive"
    elif avg_score == 0: overall = "Neutral"
    elif avg_score > -1: overall = "Negative"
    else: overall = "Very Negative"
    
    negative_reviews = [r for r, s in zip(reviews, sentiments) if s in ["Negative", "Very Negative"]]
    positive_reviews = [r for r, s in zip(reviews, sentiments) if s in ["Positive", "Very Positive"]]
    
    # Simple theme extraction
    def extract_themes(texts, n=3):
        if not texts: return []
        combined = " ".join(texts[:10])[:1024]
        try:
            summary = summarizer(combined, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]
            sentences = [s.strip() for s in re.split(r'[.!?]', summary) if len(s.strip()) > 20]
            return sentences[:n]
        except:
            return ["Unable to extract themes — try with more reviews"]
    
    pos_themes = extract_themes(positive_reviews)
    neg_themes = extract_themes(negative_reviews)
    
    pct_negative = round((breakdown.get("Negative", 0) + breakdown.get("Very Negative", 0)) / total * 100, 1)
    
    recommendation = f"Focus on reducing negative experiences ({pct_negative}% of reviews). " if pct_negative > 20 else "Strong customer satisfaction. Focus on amplifying positive themes. "
    
    return {
        "total_reviews_analyzed": total,
        "overall_sentiment": overall,
        "average_score": round(avg_score, 2),
        "sentiment_breakdown": {k: f"{v} ({round(v/total*100)}%)" for k, v in breakdown.items()},
        "top_positive_themes": pos_themes,
        "top_negative_themes": neg_themes,
        "recommendation": recommendation,
        "powered_by": "CustoVox.ai — custovox.ai"
    }

if __name__ == "__main__":
    mcp.run()
