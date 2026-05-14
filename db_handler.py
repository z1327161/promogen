from pymongo import MongoClient

# Use the URI from your original test script
MONGO_URI = "mongodb+srv://db_user_team_4:Welcome1@clusterteam4.ngblzn.mongodb.net/"

def save_and_fetch_promo(article_id, ui_promo_data):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['PromoGen']
        
        # FIX: Point to 'PromotionData' instead of 'ArticleInfo'
        collection = db['PromotionData']
        article_collection = db['ArticleInfo']
        
        
        # Ensure the article_id is part of the data being saved
        ui_promo_data["article_id"] = article_id
        
        # Update if it exists (by article_id), otherwise insert (upsert=True)
        # This handles the "manual workload" reduction mentioned in your brief [cite: 7]
        collection.update_one(
            {"article_id": article_id},
            {"$set": ui_promo_data},
            upsert=True
        )
        
        # Retrieve the updated record to pass to Vertex AI [cite: 29]
        full_promo = collection.find_one({"article_id": article_id})
        # 3. Fetch the corresponding Article Info
        # Note: Ensure the field name in ArticleInfo is also "article_id" 
        article_info = article_collection.find_one({"article_id": article_id})
        
        if full_promo and article_info:
            # Remove the MongoDB internal _id if you don't want duplicates in the merge
            article_info.pop('_id', None)
            
            # Merge Article Info into the Promotion Data object
            full_promo["article_details"] = article_info
            
        return full_promo
        
    except Exception as e:
        print(f"Database Error: {e}")
        return None

def get_articles_by_category(category_id):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['PromoGen']
        # Querying ArticleInfo as requested
        collection = db['ArticleInfo']
        
        # find() returns a cursor for all matching documents
        cursor = collection.find({"CategoryId": category_id})
        
        articles = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"]) # Convert ObjectId for JSON compatibility
            articles.append(doc)
            
        return articles
    except Exception as e:
        print(f"Database Error: {e}")
        return []
        
def get_all_categories():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['PromoGen']
        collection = db['CategoryInfo']
        
        # find({}) with an empty object retrieves all documents
        cursor = collection.find({})
        
        categories = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId for JSON
            categories.append(doc)
            
        return categories
    except Exception as e:
        print(f"Database Error: {e}")
        return []
        
def get_all_articles():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['PromoGen']
        collection = db['ArticleInfo']
        
        # find({}) with an empty object retrieves all documents
        cursor = collection.find({})
        
        categories = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId for JSON
            categories.append(doc)
            
        return categories
    except Exception as e:
        print(f"Database Error: {e}")
        return []
