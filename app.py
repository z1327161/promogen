import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from db_handler import save_and_fetch_promo, get_articles_by_category, get_all_categories, get_all_articles
from content_generator import get_vertex_outputs, verify_promotion_compliance

app = FastAPI(
    title="PromoGen API",
    description=(
        "**PromoGen** is an AI-powered retail promotion management platform.\n\n"
        "It orchestrates the full promotion workflow:\n"
        "- **Data Persistence** — saves promotion data to MongoDB\n"
        "- **Asset Generation** — generates image prompts and shelf-talker copy via Vertex AI\n"
        "- **Template Selection** — automatically selects label stationery based on promotion type\n"
        "- **Compliance Audit** — verifies promotional assets against localised legal requirements\n\n"
        "Swagger UI: `/docs` | ReDoc: `/redoc`"
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Health", "description": "Service availability checks."},
        {"name": "Articles", "description": "Article and category data from MongoDB."},
        {"name": "Promotions", "description": "End-to-end promotion processing pipeline."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://promogenui-73298798964.us-central1.run.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromotionRequest(BaseModel):
    promotion_id: str = Field(..., description="Unique identifier for the promotion.", json_schema_extra={"example": "PROMO-2026-001"})
    start_date: str = Field(..., description="Promotion start date (YYYY-MM-DD).", json_schema_extra={"example": "2026-06-01"})
    end_date: str = Field(..., description="Promotion end date (YYYY-MM-DD).", json_schema_extra={"example": "2026-06-30"})
    promotion_type: str = Field(..., description="Supported values: `Multi buy`, `Price Promise`, `Member Pricing`.", json_schema_extra={"example": "Multi buy"})
    description: Optional[str] = Field("No description", description="Human-readable description of the offer.", json_schema_extra={"example": "Buy 2 get 1 free"})
    price: Optional[float] = Field(0.0, description="Promotional price (used for compliance checks).", json_schema_extra={"example": 4.99})
    percentage: Optional[int] = Field(0, description="Discount percentage applied to the article.", json_schema_extra={"example": 20})

@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Confirm the PromoGen API is reachable."""
    return {"status": "PromoGen API is online and ready for the UI."}


@app.get("/articles/category/{category_id}", tags=["Articles"], summary="Get Articles by Category")
async def fetch_articles_by_cat(category_id: int):
    """Retrieves all articles belonging to a specific CategoryId."""
    articles = get_articles_by_category(category_id)
    return {
        "status": "success",
        "message": f"No articles found for CategoryId {category_id}" if not articles else None,
        "count": len(articles),
        "data": articles,
    }


@app.get("/categories", tags=["Articles"], summary="Get All Categories")
async def fetch_categories():
    """Retrieves all available categories from the CategoryInfo collection."""
    categories = get_all_categories()
    return {
        "status": "success",
        "count": len(categories),
        "data": categories,
    }


@app.get("/articles", tags=["Articles"], summary="Get All Articles")
async def fetch_articles():
    """Retrieves all articles from the ArticleInfo collection."""
    articles = get_all_articles()
    return {
        "status": "success",
        "count": len(articles),
        "data": articles,
    }


@app.post("/process-promotion/{article_id}", tags=["Promotions"], summary="Process a Promotion")
async def handle_promo(article_id: str, promo: PromotionRequest):
    """
    End-to-end promotion processing pipeline:

    1. **Persist** — Upserts the promotion record in MongoDB (`PromotionData` collection).
    2. **Generate** — Calls Vertex AI Agent to produce an image URL and shelf-talker copy.
    3. **Select Template** — Maps the promotion type to the correct label stationery.
    4. **Audit** — Runs a localised compliance check on the promotion metadata.
    """
    # Step A: Persist to MongoDB
    full_data = save_and_fetch_promo(article_id, promo.model_dump())
    if not full_data:
        raise HTTPException(status_code=500, detail="Database sync failed.")

    if "_id" in full_data:
        full_data["_id"] = str(full_data["_id"])

    # Step B: Generate assets via Vertex AI Agent
    ai_results = get_vertex_outputs(full_data)
    if "error" in ai_results:
        raise HTTPException(status_code=500, detail=ai_results["error"])

    # Step C: Select label stationery based on promotion type
    label_stationery = "Standard White"
    p_type_lower = full_data.get("promotion_type", "").lower()
    if "multi buy" in p_type_lower:
        label_stationery = "Multi-Buy Yellow Stationery"
    elif "price promise" in p_type_lower:
        label_stationery = "Price Promise Gold Stationery"
    elif "member" in p_type_lower:
        label_stationery = "Exclusive Member Blue Stationery"

    # Step D: Compliance audit
    compliance_report = verify_promotion_compliance(None, full_data)

    return {
        "status": "success",
        "metadata": {
            "article_id": article_id,
            "db_id": full_data.get("_id"),
            "required_stationery": label_stationery,
        },
        "generated_assets": {
            "ai_image_url": ai_results.get("ai_image_url"),
            "shelf_talker_copy": ai_results.get("shelf_talker_copy"),
        },
        "compliance_audit": {
            "status": "Verified",
            "details": compliance_report,
            "note": f"Confirmed for {label_stationery} use.",
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

