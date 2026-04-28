"""Image Search Router for Main API.

This router provides endpoints for image-based product search
by integrating with the ML Search Service.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from src.config.database import get_db
from src.dependency.auth import get_optional_user
from src.service.ml_client import ml_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Image Search"])


@router.post("/by-image")
async def search_by_image(
    file: UploadFile = File(..., description="Image file to search"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Search products by image using ML.
    
    This endpoint:
    1. Sends the image to the ML service
    2. Receives matching product IDs with scores
    3. Enriches results with full product details
    
    Returns:
        Search results with product details
    """
    # Call ML service
    result = await ml_client.search_by_image(file, top_k)
    
    if result is None:
        raise HTTPException(503, "ML service unavailable. Please try again later.")
    
    # Get product IDs from results
    product_ids = [r["product_id"] for r in result.get("results", [])]
    
    # Enrich with product details from database
    products = _get_products_by_ids(db, product_ids)
    
    # Build enriched results
    enriched_results = []
    for r in result.get("results", []):
        product_id = r["product_id"]
        if product_id in products:
            enriched_results.append({
                "product_id": product_id,
                "score": r["score"],
                "match_type": r["match_type"],
                "product": products[product_id]
            })
    
    return {
        "query": result.get("query", {}),
        "results": enriched_results,
        "total": len(enriched_results)
    }


@router.get("/ml/status")
async def get_ml_service_status():
    """Get ML service status and index statistics.
    
    Returns:
        ML service health and index information
    """
    is_healthy = await ml_client.health_check()
    stats = await ml_client.get_index_stats() if is_healthy else None
    
    return {
        "ml_service_healthy": is_healthy,
        "ml_service_url": ml_client.base_url,
        "index_stats": stats
    }


@router.get("/ml/brands")
async def get_known_brands():
    """Get list of brands recognized by ML service.
    
    Returns:
        List of brand names
    """
    brands = await ml_client.get_known_brands()
    return {"brands": brands}


@router.get("/ml/categories")
async def get_supported_categories():
    """Get list of categories supported by ML detection.
    
    Returns:
        List of category names
    """
    categories = await ml_client.get_supported_categories()
    return {"categories": categories}


@router.post("/ml/index-product")
async def index_product(
    product_id: int = Query(..., description="Product ID to index"),
    image_url: str = Query(..., description="Product image URL")
):
    """Add a product to the ML search index.
    
    This endpoint triggers the ML service to download and index
    a product image for similarity search.
    
    Returns:
        Indexing status
    """
    success = await ml_client.index_product(product_id, image_url)
    
    if not success:
        raise HTTPException(500, "Failed to index product")
    
    return {
        "status": "success",
        "product_id": product_id,
        "message": "Product indexed successfully"
    }


@router.post("/ml/rebuild-index")
async def rebuild_ml_index():
    """Trigger rebuild of ML search index.
    
    This rebuilds the FAISS index from all products with images.
    This is a background operation.
    
    Returns:
        Rebuild status
    """
    success = await ml_client.rebuild_index()
    
    if not success:
        raise HTTPException(500, "Failed to trigger index rebuild")
    
    return {
        "status": "started",
        "message": "Index rebuild started in background"
    }


def _get_products_by_ids(db: Session, product_ids: List[int]) -> dict:
    """Get products by IDs from database.
    
    Args:
        db: Database session
        product_ids: List of product IDs
        
    Returns:
        Dictionary mapping product_id to product data
    """
    from src.schemas.product import Product
    from sqlalchemy.orm import joinedload
    
    if not product_ids:
        return {}
    
    products = {}
    
    try:
        # Query products with relationships
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.inventory)
        ).filter(Product.product_id.in_(product_ids))
        
        for product in query.all():
            products[product.product_id] = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "selling_price": float(product.selling_price) if product.selling_price else None,
                "unit_cost": float(product.unit_cost) if product.unit_cost else None,
                "image_url": product.image_url,
                "status": product.status.value if hasattr(product.status, 'value') else product.status,
                "category": {
                    "categoryID": product.category.categoryID,
                    "name": product.category.name
                } if product.category else None,
                "inventory": {
                    "current_stock": float(product.inventory.current_stock) if product.inventory and product.inventory.current_stock else 0,
                    "min_stock_level": float(product.inventory.min_stock_level) if product.inventory and product.inventory.min_stock_level else 0
                } if product.inventory else None
            }
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
    
    return products
