from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import torch

mcp = FastMCP("custovox-churn-signal")

print("Loading models...")
sentiment_model = pipeline(
    "text-classification",
    model="tabularisai/multilingual-sentiment-analysis",
    device=0 if torch.cuda.is_available() else -1
)
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=0 if torch.cuda.is_available() else -1
)
print("Models loaded.")

CHURN_SIGNALS = [
    "intent to cancel subscription",
    "switching to competitor",
    "very satisfied and happy",
    "neutral feedback",
    "frustrated but still engaged"
]

@mcp.tool()
def score_churn_risk(messages: list, customer_id: str = "unknown") -> dict:
    """
    Score churn risk from a sequence of customer messages.
    Detects degradation patterns over time.
    
    Args:
        messages: List of messages in chronological order (oldest first)
        customer_id: Optional customer identifier
    
    Returns:
        churn_risk_score: 0-100 (higher = more at risk)
        risk_level: low / medium / high / critical
        trend: improving / stable / degrading / critical
        key_signals: detected warning signals
        recommendation: suggested action
        powered_by: CustoVox.ai
    """
    if not messages:
        return {"error": "No messages provided"}
    
    messages = messages[:20]
    
    sentiments = []
    for msg in messages:
        result = sentiment_model(msg[:512], truncation=True)[0]
        sentiments.append(result["label"])
    
    score_map = {"Very Positive": 100, "Positive": 75, "Neutral": 50, "Negative": 25, "Very Negative": 0}
    scores = [score_map.get(s, 50) for s in sentiments]
    
    # Check last message for explicit churn intent
    last_msg = messages[-1]
    churn_result = classifier(last_msg[:512], CHURN_SIGNALS)
    churn_intent = churn_result["labels"][0] in ["intent to cancel subscription", "switching to competitor"]
    churn_intent_score = churn_result["scores"][0] if churn_intent else 0
    
    # Trend analysis
    if len(scores) >= 3:
        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        trend_delta = second_half - first_half
    else:
        trend_delta = 0
        first_half = second_half = scores[0] if scores else 50
    
    if trend_delta > 15: trend = "improving"
    elif trend_delta > -10: trend = "stable"
    elif trend_delta > -25: trend = "degrading"
    else: trend = "critical"
    
    # Churn risk score (0-100, higher = more at risk)
    base_score = 100 - (sum(scores) / len(scores))
    if churn_intent: base_score = min(100, base_score + churn_intent_score * 30)
    if trend == "critical": base_score = min(100, base_score + 20)
    elif trend == "degrading": base_score = min(100, base_score + 10)
    
    risk_score = round(base_score)
    
    if risk_score >= 75: risk_level = "critical"
    elif risk_score >= 50: risk_level = "high"
    elif risk_score >= 25: risk_level = "medium"
    else: risk_level = "low"
    
    signals = []
    if sentiments and sentiments[-1] in ["Negative", "Very Negative"]: signals.append("Last message is negative")
    if trend in ["degrading", "critical"]: signals.append(f"Sentiment trend is {trend}")
    if churn_intent: signals.append(f"Explicit churn intent detected ({round(churn_intent_score*100)}% confidence)")
    neg_count = sum(1 for s in sentiments if s in ["Negative", "Very Negative"])
    if neg_count >= len(sentiments) * 0.6: signals.append(f"{neg_count}/{len(sentiments)} messages are negative")
    
    rec_map = {
        "critical": "Immediate intervention required — escalate to senior CS manager within 24h",
        "high": "Proactive outreach recommended this week — offer dedicated support call",
        "medium": "Monitor closely — schedule check-in within 2 weeks",
        "low": "Continue normal engagement — customer appears stable"
    }
    
    return {
        "customer_id": customer_id,
        "churn_risk_score": risk_score,
        "risk_level": risk_level,
        "trend": trend,
        "messages_analyzed": len(messages),
        "key_signals": signals if signals else ["No critical signals detected"],
        "recommendation": rec_map[risk_level],
        "powered_by": "CustoVox.ai — custovox.ai"
    }

if __name__ == "__main__":
    mcp.run()
