import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview.vision_models import ImageGenerationModel

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
        model = GenerativeModel("gemini-2.5-flash")

        prompt = f"""Role: You are a specialized Retail Graphic Design Agent.
        Generate a high-fidelity A6 promotional image by cross-referencing Article Data and Promotion Data.
        1. Visual Foundation (Fixed Brand Identity)Canvas: Vertical A6 Sign.Split Background: Top 25% is Vibrant Lime-Green. Bottom 75% is Vibrant Cyan-Blue.
        Header Logo: Top-left of the green section. "freshchoice" logo.
        Feature Graphic: A large, horizontal speech bubble with a thick yellow border and dark green interior, centered on the intersection of the green and blue backgrounds.

        2. Dynamic Text & Pricing LogicRead the promotion_type and apply these specific rules:IF promotion_type IS "Multi buy":Bubble Text: "MULTIBUY DEALS"Main Yellow Box: Display "ANY 2 FOR $[Price]".
        Calculation: $[Price] = (Standard\_Price \times 2) \times (1 - percentage/100)$.IF promotion_type IS "Discount" or "Single":Bubble Text: "SPECIAL OFFER"Main Yellow Box: Display "NOW $[Price]".Calculation: $[Price] = Standard\_Price \times (1 - percentage/100)$.

        3. Central Product CardInside the blue section, place a White Rectangular Card containing:Product Name: Article_Name in bold, black, all-caps.Product Image: Render the product from the provided Image URL realistically in the center.Badge: Bright Red pill-shaped badge with "GREAT VALUE" in white bold text.The Deal Box: A bright yellow rectangle containing the Calculated Price in massive, heavy, black numerals.

        4. Footer (Small Print)Bottom Left: "Unit Price: $[Standard_Price]" | "Valid until end_date".Bottom Right: "AUCKLAND" in tiny black capital letters.

Promotion data: {mongo_data}

Respond in JSON with keys: "image_prompt", "shelf_talker_copy", "template_suggestion"."""

        response = model.generate_content(prompt)

        return {
            "ai_output": response.text,
            "status": "success"
        }

    except Exception as e:
        return {"error": f"Gemini call failed: {str(e)}"}

def generate_promotional_image(image_prompt: str) -> bytes | None:
    """
    Generates a promotional image from a text prompt using Imagen 3 on Vertex AI.
    Returns raw image bytes (JPEG), or None on failure.
    """
    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        images = model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
        )
        return images[0]._image_bytes
    except Exception as e:
        print(f"Imagen generation failed: {e}")
        return None

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
