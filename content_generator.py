import vertexai
from vertexai.generative_models import GenerativeModel, Part

# --- CONFIGURATION ---
PROJECT_ID = "gcp-wow-wwnz-edr-reactpoc-test"
LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

def get_vertex_outputs(mongo_data):
    """
    Calls Gemini to generate promotional image prompts and shelf-talker copy.
    """
    try:
        model = GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are a retail promotions specialist. Given the following promotion data, generate:
1. An image prompt suitable for an AI image generator (describe a shelf-talker or promotional display image).
2. Shelf-talker copy (short, punchy promotional text for an in-store label).
3. A suggested label stationery template based on the promotion type.

Promotion data: {mongo_data}

Respond in JSON with keys: "image_prompt", "shelf_talker_copy", "template_suggestion"."""

        response = model.generate_content(prompt)

        return {
            "ai_output": response.text,
            "status": "success"
        }

    except Exception as e:
        return {"error": f"Gemini call failed: {str(e)}"}

def verify_promotion_compliance(image_bytes, promo_data):
    """
    Direct visual analysis using Gemini 1.5 Flash.
    """
    model = GenerativeModel("gemini-1.5-flash-002")

    expected_price = promo_data.get('price', 'N/A')
    p_type = promo_data.get('promotion_type', 'Standard')

    prompt = f"""
    Act as a Retail Compliance Auditor.
    Compare the text in this image against:
    - Promotion Type: {p_type}
    - Expected Price: {expected_price}

    Return a JSON response with 'status' (APPROVED/REJECTED) and 'reason'.
    """

    image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")

    try:
        response = model.generate_content([image_part, prompt])
        return response.text
    except Exception as e:
        return {"error": f"Compliance check failed: {str(e)}"}
