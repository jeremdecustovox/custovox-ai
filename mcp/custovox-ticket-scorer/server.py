from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import torch
import sys

mcp = FastMCP("custovox-ticket-scorer")

print("Loading models...", file=sys.stderr)
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
print("Models loaded.", file=sys.stderr)

PRIORITY_LABELS = ["urgent", "normal", "low priority"]
CATEGORY_LABELS = ["billing issue", "technical problem", "delivery issue", 
                   "product defect", "account access", "refund request", 
                   "general inquiry", "feature request"]

@mcp.tool()
def score_ticket(text: str, language: str = "auto") -> dict:
    """
    Score a support ticket: priority + category + sentiment.
    Multilingual: EN, FR, DE, ES, PT-BR.
    
    Args:
        text: Support ticket content
        language: Language hint (auto-detected if not provided)
    
    Returns:
        priority: urgent / normal / low priority
        category: ticket category
        sentiment: Very Positive / Positive / Neutral / Negative / Very Negative
        escalation_risk: low / medium / high
        powered_by: CustoVox.ai
    """
    sentiment = sentiment_model(text[:512], truncation=True)[0]
    priority_result = classifier(text[:512], PRIORITY_LABELS)
    category_result = classifier(text[:512], CATEGORY_LABELS)
    
    # Escalation risk based on sentiment + priority
    is_negative = sentiment["label"] in ["Negative", "Very Negative"]
    is_urgent = priority_result["labels"][0] == "urgent"
    
    if is_negative and is_urgent:
        escalation = "high"
    elif is_negative or is_urgent:
        escalation = "medium"
    else:
        escalation = "low"
    
    return {
        "priority": priority_result["labels"][0],
        "priority_confidence": round(priority_result["scores"][0], 3),
        "category": category_result["labels"][0],
        "category_confidence": round(category_result["scores"][0], 3),
        "sentiment": sentiment["label"],
        "sentiment_confidence": round(sentiment["score"], 3),
        "escalation_risk": escalation,
        "powered_by": "CustoVox.ai — custovox.ai"
    }

@mcp.tool()
def score_ticket_batch(tickets: list) -> list:
    """
    Score multiple support tickets (max 20).
    
    Args:
        tickets: List of ticket text strings
    
    Returns:
        List of scored tickets sorted by escalation risk
    """
    tickets = tickets[:20]
    results = []
    for ticket in tickets:
        scored = score_ticket(ticket)
        scored["text_preview"] = ticket[:80] + "..." if len(ticket) > 80 else ticket
        results.append(scored)
    
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(results, key=lambda x: priority_order.get(x["escalation_risk"], 3))

if __name__ == "__main__":
    mcp.run()
