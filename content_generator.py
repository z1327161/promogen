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

        prompt = f"""You are a retail promotion specialist. Given the following promotion data, generate:
A multibuy deal A6 size image

1. Layout & Color Palette:
Split Background: The sign is divided into two distinct horizontal sections.
Header (Top 25%): Vibrant Lime-Green background.
Body (Bottom 75%): Vibrant Cyan-Blue background.
The Speech Bubble: A large, horizontal "speech bubble" graphic is centered, overlapping both colors. It has a thick yellow border and a dark green interior. Inside this bubble, the text "MULTIBUY DEALS" is written in a heavy, bold, white sans-serif font with a subtle drop shadow.

2. Branding:
Logo: In the top green header, place a logo consisting of three curved "leaf" strokes (Red, Yellow, Green) forming a circle, followed by the word "freshchoice" in a clean, white, lowercase sans-serif font.
Location: In the bottom right corner of the blue section, the word "Auckland" is written in small, clean white text.
3. Dynamic Product Block (Central White Card): In the center of the blue section, there is a large, clean White Rectangular Card. Populate it with these details from the JSON:

Product Title: [Article_Name] in bold, black, all-caps, centered at the top.
Value Badge: Directly below the title, a bright Red pill-shaped badge with the text "GREAT VALUE" in bold white letters.
Yellow Deal Box: A large, bright Yellow rectangle fills the middle of the white card. Inside, display: "ANY 2 FOR $[Calculated Price]". The numerals for the price must be very large, black, and heavy.
Footer Info:
Bottom Left: "Unit Price: $[Standard_Price]" and "Valid until 31/12/2026" in tiny black font.
Bottom Right: The word "AUCKLAND" in tiny black capital letters.

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
