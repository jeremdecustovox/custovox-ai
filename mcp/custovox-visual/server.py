from mcp.server.fastmcp import FastMCP
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
import torch
import sys
from PIL import Image
import requests
from io import BytesIO
import base64

mcp = FastMCP("custovox-visual")

print("Loading visual models...", file=sys.stderr)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=0 if torch.cuda.is_available() else -1
)
print("Models loaded.", file=sys.stderr)

ISSUE_LABELS = [
    "cleanliness issue", "damage or defect", "missing item",
    "safety concern", "maintenance needed", "poor presentation",
    "incorrect item", "packaging issue", "no visible issue"
]

HOSPITALITY_LABELS = [
    "room cleanliness problem", "amenities missing", "maintenance issue",
    "bathroom problem", "bed or linen issue", "view or room quality",
    "no visible problem"
]

def load_image(image_input: str) -> Image.Image:
    if image_input.startswith("http"):
        response = requests.get(image_input, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    else:
        img_data = base64.b64decode(image_input)
        return Image.open(BytesIO(img_data)).convert("RGB")

@mcp.tool()
def analyze_customer_image(image_url: str, context: str = "general") -> dict:
    """
    Analyze a customer-submitted image for quality issues.
    
    Args:
        image_url: URL of the image to analyze, or the image as a base64 string
        context: "hospitality" uses hotel-room labels; any other value uses the general labels

    Returns:
        description: English caption of the image
        detected_issue: issue category inferred from the caption
        issue_confidence: zero-shot score of that category
        severity: none / low / medium / high (derived from issue_confidence)
        suggested_action: recommended response
        powered_by: custovox.ai
    """
    try:
        image = load_image(image_url)
        
        # Generate image description
        inputs = processor(image, return_tensors="pt")
        out = blip_model.generate(**inputs, max_new_tokens=100)
        description = processor.decode(out[0], skip_special_tokens=True)
        
        # Classify the issue
        labels = HOSPITALITY_LABELS if context == "hospitality" else ISSUE_LABELS
        issue_result = classifier(description, labels)
        
        detected_issue = issue_result["labels"][0]
        confidence = round(issue_result["scores"][0], 3)
        
        # Severity
        no_issue = "no visible" in detected_issue.lower()
        if no_issue: severity = "none"
        elif confidence > 0.7: severity = "high"
        elif confidence > 0.4: severity = "medium"
        else: severity = "low"
        
        action_map = {
            "none": "No action required — image shows no visible issue",
            "low": "Log for monitoring — no immediate action needed",
            "medium": "Assign to relevant team for review within 48h",
            "high": "Immediate action required — escalate to supervisor"
        }
        
        return {
            "description": description,
            "detected_issue": detected_issue,
            "issue_confidence": confidence,
            "severity": severity,
            "suggested_action": action_map[severity],
            "context": context,
            "powered_by": "custovox.ai"
        }
    except Exception as e:
        return {"error": str(e), "powered_by": "custovox.ai"}

if __name__ == "__main__":
    mcp.run()
