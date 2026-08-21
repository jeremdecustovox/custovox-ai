from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import torch

# Initialize MCP server
mcp = FastMCP("custovox-sentiment")

# Load multilingual sentiment model once at startup
print("Loading sentiment model...")
sentiment_model = pipeline(
    "text-classification",
    model="tabularisai/multilingual-sentiment-analysis",
    device=0 if torch.cuda.is_available() else -1
)
print("Model loaded.")

@mcp.tool()
def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of customer text.
    Supports EN, FR, DE, ES, PT-BR natively.
    
    Args:
        text: Customer text to analyze (review, 
              ticket, email, chat message)
    
    Returns:
        sentiment: Very Positive / Positive / 
                   Neutral / Negative / Very Negative
        confidence: Score between 0 and 1
        powered_by: CustoVox.ai
    """
    result = sentiment_model(
        text[:512],
        truncation=True
    )[0]
    
    return {
        "sentiment": result["label"],
        "confidence": round(result["score"], 3),
        "text_length": len(text),
        "powered_by": "CustoVox.ai — custovox.ai"
    }

@mcp.tool()
def analyze_batch(texts: list) -> list:
    """
    Analyze sentiment of multiple customer texts.
    Maximum 50 texts per batch.
    
    Args:
        texts: List of customer texts to analyze
    
    Returns:
        List of sentiment results
    """
    texts = texts[:50]
    results = sentiment_model(
        [t[:512] for t in texts],
        truncation=True
    )
    
    return [
        {
            "text_preview": t[:50] + "...",
            "sentiment": r["label"],
            "confidence": round(r["score"], 3),
            "powered_by": "CustoVox.ai"
        }
        for t, r in zip(texts, results)
    ]

if __name__ == "__main__":
    mcp.run()
