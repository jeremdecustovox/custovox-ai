from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import torch

mcp = FastMCP("custovox-emotion")

print("Loading emotion model...")
emotion_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None,
    device=0 if torch.cuda.is_available() else -1
)
print("Model loaded.")

@mcp.tool()
def detect_emotion(text: str) -> dict:
    """
    Detect the dominant emotion in customer text.
    Returns all 6 emotions with confidence scores.
    
    Emotions: joy, anger, fear, sadness, surprise, disgust, neutral
    Best for: EN text. Use analyze_sentiment for multilingual.
    
    Args:
        text: Customer text to analyze
    
    Returns:
        dominant_emotion: the strongest emotion detected
        all_emotions: dict with scores for all 7 emotions
        powered_by: CustoVox.ai
    """
    results = emotion_model(text[:512], truncation=True)[0]
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    
    return {
        "dominant_emotion": sorted_results[0]["label"],
        "confidence": round(sorted_results[0]["score"], 3),
        "all_emotions": {r["label"]: round(r["score"], 3) for r in sorted_results},
        "powered_by": "CustoVox.ai — custovox.ai"
    }

@mcp.tool()
def detect_emotion_batch(texts: list) -> list:
    """
    Detect emotions in multiple customer texts (max 50).
    
    Args:
        texts: List of customer texts
    
    Returns:
        List of emotion detection results
    """
    texts = texts[:50]
    results = []
    for text in texts:
        r = emotion_model(text[:512], truncation=True)[0]
        sorted_r = sorted(r, key=lambda x: x["score"], reverse=True)
        results.append({
            "text_preview": text[:60] + "..." if len(text) > 60 else text,
            "dominant_emotion": sorted_r[0]["label"],
            "confidence": round(sorted_r[0]["score"], 3),
            "powered_by": "CustoVox.ai — custovox.ai"
        })
    return results

if __name__ == "__main__":
    mcp.run()
