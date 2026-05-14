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

        prompt = f"""Role: You are a Professional Retail Graphic Designer.
Task: Generate a high-resolution A6 promotional sign by mapping values from the provided JSON input to the layout rules below.

1. Global Visual Identity (Apply to ALL images)
Layout: Vertical A6 composition. Split background: Top 25% is Vibrant Lime-Green; Bottom 75% is Vibrant Cyan-Blue.

Branding: In the green header, place the "freshchoice" logo (three curved leaf strokes in Red, Yellow, and Green forming a circle, followed by "freshchoice" in white lowercase sans-serif).

The Speech Bubble: Centered, overlapping the green/blue divide, is a horizontal speech bubble with a thick yellow border and dark green interior.

2. Conditional Logic (Based on promotion-type)
Identify the promotion-type from the JSON and apply the corresponding text and layout:

IF "multibuy": * Bubble Text: "MULTIBUY DEALS" (Bold, white, heavy sans-serif).

Yellow Deal Box: Display "ANY [Quantity] FOR $[Calculated_Price]".

IF "discount": * Bubble Text: "SPECIAL OFFER" (Bold, white, heavy sans-serif).

Yellow Deal Box: Display "NOW $[Discounted_Price]". Below it, in smaller font: "SAVE $[Savings]".

IF "clearance": * Bubble Text: "CLEARANCE" (Bold, white, heavy sans-serif).

Yellow Deal Box: Display "WAS $[Standard_Price] NOW $[Clearance_Price]".

3. Central Product Card (White Rectangular Insert)
Place a clean white rectangular card in the center of the blue section. Populate it with:

Product Name: [Article_Name] in bold, black, all-caps at the top.

Value Badge: A bright Red pill-shaped badge directly below the title with the text "GREAT VALUE" in white.

The Deal Box: The Bright Yellow Rectangle described in the logic above. The currency and numerals must be the largest, heaviest elements on the card.

4. Mandatory Footer (Tiny Black Text)
Bottom Left: "Unit Price: $[Standard_Price]" | "Valid until [end_Date]"

Bottom Right: "AUCKLAND".

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
