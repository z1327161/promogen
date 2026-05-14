import vertexai
# CHANGED: Use the stable import path
from google.cloud import discoveryengine 
from vertexai.generative_models import GenerativeModel, Part

# --- CONFIGURATION ---
PROJECT_ID = "gcp-wow-wwnz-edr-reactpoc-test"
LOCATION = "us-central1" 

# However, Agent Builder (Discovery Engine) usually lives in 'global'
AGENT_LOCATION = "global"
AGENT_ID = "1778658051045" # Get this from Agent Settings or URL

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

def get_vertex_outputs(mongo_data):
    """
    Calls the Vertex AI Agent (Studio/Agent Builder) using the 
    Conversational Search Service.
    """
    try:
        # 1. Setup the client
        client = discoveryengine.ConversationalSearchServiceClient()
        
        # 2. Build the resource name for the default data store/session
        # For Agent Builder, the path usually points to the 'servingConfig'
        serving_config = f"projects/{PROJECT_ID}/locations/{AGENT_LOCATION}/collections/default_collection/engines/{AGENT_ID}/servingConfigs/default_serving_config"
        
        # 3. Create the query based on your MongoDB data
        user_query = f"Analyze this promotion data and generate content: {mongo_data}"
        
        query = discoveryengine.Query(text=user_query)
        
        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config,
            query=query,
        )

        # 4. Execute the request
        response = client.answer_query(request)
        
        # Extract the text from the agent's answer
        answer_text = response.answer.answer_text

        # Note: Since Studio Agents return text, you may need to parse 
        # the response if the agent returns JSON-like strings.
        return {
            "ai_output": answer_text,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"Agent Builder call failed: {str(e)}"}

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