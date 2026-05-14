import os
from pymongo import MongoClient
import vertexai
from vertexai.generative_models import GenerativeModel

# 1. Configuration
# Ensure this matches the project you set in gcloud config set project
PROJECT_ID = "gcp-wow-wwnz-edr-reactpoc-test" 
LOCATION = "us-central1"
MONGO_URI = "mongodb+srv://db_user_team_4:Welcome1@clusterteam4.ngblzn.mongodb.net/"

# 2. Initialize Vertex AI 
# (It will automatically use the credentials from your 'gcloud auth' login)
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-1.5-flash")

def test_workflow(article_id):
    try:
        # A. Fetch from MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['PromoGen']
        collection = db['ArticleInfo']
        
        # Search for the promotion
        print(f"Searching MongoDB for Article ID: {article_id}...")
        promo = collection.find_one({"article_id": article_id})
        
        if not promo:
            return f"Error: Article ID '{article_id}' not found in database."
        
        # B. Send to Vertex AI
        print("Data found! Sending to Vertex AI...")
        prompt = f"Summarize this promotion for a store manager: {promo}"
        
        response = model.generate_content(prompt)
        
        return {
            "mongo_data": promo,
            "vertex_ai_response": response.text
        }
    except Exception as e:
        return f"An error occurred: {e}"

# --- TEST IT ---
if __name__ == "__main__":
    # Use a real ID from your MongoDB
    result = test_workflow('12345') 
    print("\n--- RESULTS ---")
    print(result)