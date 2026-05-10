"""ML Client Service for Main API.

This module provides a client for communicating with the ML Search Service.
"""
import httpx
from fastapi import UploadFile
from typing import Optional, List, Dict
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class MLSearchClient:
    """HTTP client for ML Search Service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = (base_url or settings.ML_SERVICE_URL).rstrip('/')
        self.timeout = timeout
        self._headers = {"X-API-Key": settings.ML_API_KEY}
        logger.info(f"MLSearchClient initialized with base URL: {self.base_url}")
    
    async def search_by_image(
        self,
        file: UploadFile,
        top_k: int = 10
    ) -> Optional[Dict]:
        """Call ML service for image search.
        
        Args:
            file: Uploaded image file
            top_k: Number of results to return
            
        Returns:
            Search results dictionary or None if failed
        """
        url = f"{self.base_url}/api/v1/search-by-image"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                content = await file.read()
                response = await client.post(
                    url,
                    headers=self._headers,
                    files={"file": (file.filename, content, file.content_type or "image/jpeg")},
                    params={"top_k": top_k}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"ML service returned {response.status_code}: {response.text}")
                    
            except httpx.ConnectError:
                logger.error(f"Could not connect to ML service at {self.base_url}")
            except httpx.TimeoutException:
                logger.error("ML service request timed out")
            except Exception as e:
                logger.error(f"ML service error: {e}")
        
        return None
    
    async def index_product(self, product_id: int, image_url: str) -> bool:
        """Add product to ML index.
        
        Args:
            product_id: Product ID to index
            image_url: URL of product image
            
        Returns:
            True if indexed successfully, False otherwise
        """
        url = f"{self.base_url}/api/v1/index-product"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    headers=self._headers,
                    params={"product_id": product_id, "image_url": image_url}
                )
                
                return response.status_code == 200
                
            except Exception as e:
                logger.error(f"Error indexing product: {e}")
                return False
    
    async def rebuild_index(self) -> bool:
        """Trigger index rebuild.
        
        Returns:
            True if rebuild started successfully, False otherwise
        """
        url = f"{self.base_url}/api/v1/rebuild-index"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._headers)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Error rebuilding index: {e}")
                return False
    
    async def get_index_stats(self) -> Optional[Dict]:
        """Get index statistics.
        
        Returns:
            Stats dictionary or None if failed
        """
        url = f"{self.base_url}/api/v1/index/stats"

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Error getting index stats: {e}")
        
        return None
    
    async def health_check(self) -> bool:
        """Check if ML service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/health"
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except Exception:
                return False
    
    async def get_known_brands(self) -> List[str]:
        """Get list of known brands from ML service.
        
        Returns:
            List of brand names
        """
        url = f"{self.base_url}/api/v1/brands"

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("brands", [])
            except Exception as e:
                logger.error(f"Error getting brands: {e}")
        
        return []
    
    async def get_supported_categories(self) -> List[str]:
        """Get list of supported categories from ML service.
        
        Returns:
            List of category names
        """
        url = f"{self.base_url}/api/v1/categories"

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("categories", [])
            except Exception as e:
                logger.error(f"Error getting categories: {e}")
        
        return []


# Global client instance
ml_client = MLSearchClient()
