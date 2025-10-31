"""
Model Service Tools
Tools for interacting with the model service (localhost:8000)
"""
import os
import logging
import httpx
from typing import Dict

logger = logging.getLogger(__name__)

# Configuration
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:8000")
TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Create reusable HTTP client
http_client = httpx.Client(timeout=TIMEOUT)


def register_tools(mcp_instance):
    """Register all model service tools with the MCP instance"""
    
    @mcp_instance.tool()
    def get_available_models() -> Dict:
        """
        Retrieve the list of available AI models from the model service.
        
        This tool queries the local model service API at /v1/models endpoint
        to fetch all currently available models, including their IDs, names,
        and metadata.
        
        Returns:
            Dictionary containing:
            - success: Boolean indicating if the request succeeded
            - models: List of model objects with id, name, and metadata
            - count: Total number of available models
            - error: Error message if request failed (only present on failure)
        
        Example:
            {
                "success": true,
                "models": [
                    {"id": "gpt-3.5-turbo", "object": "model", ...},
                    {"id": "gpt-4", "object": "model", ...}
                ],
                "count": 2
            }
        """
        logger.info("Fetching models from %s/v1/models", MODEL_SERVICE_URL)
        
        try:
            response = http_client.get(
                f"{MODEL_SERVICE_URL}/v1/models",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            models_list = data.get("data", [])
            
            logger.info("✓ Successfully retrieved %d models", len(models_list))
            
            return {
                "success": True,
                "models": models_list,
                "count": len(models_list)
            }
        
        except httpx.TimeoutException as e:
            error_msg = f"Request timed out after {TIMEOUT}s"
            logger.error("✗ %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "models": [],
                "count": 0
            }
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error("✗ HTTP error: %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "models": [],
                "count": 0
            }
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("✗ %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "models": [],
                "count": 0
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("✗ %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "models": [],
                "count": 0
            }

    @mcp_instance.tool()
    def get_model_details(model_id: str) -> Dict:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: The unique identifier of the model (e.g., "gpt-3.5-turbo")
        
        Returns:
            Dictionary with model details including capabilities and limits,
            or error information if the request failed
        
        Example:
            {
                "success": true,
                "model": {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai"
                }
            }
        """
        logger.info("Fetching details for model: %s", model_id)
        
        try:
            response = http_client.get(
                f"{MODEL_SERVICE_URL}/v1/models/{model_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            
            model_data = response.json()
            logger.info("✓ Successfully retrieved details for %s", model_id)
            
            return {
                "success": True,
                "model": model_data
            }
        
        except httpx.HTTPStatusError as e:
            error_msg = f"Model not found or API error: HTTP {e.response.status_code}"
            logger.error("✗ %s for model %s", error_msg, model_id)
            return {
                "success": False,
                "error": error_msg,
                "model_id": model_id
            }
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("✗ %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "model_id": model_id
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("✗ %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "model_id": model_id
            }

    @mcp_instance.tool()
    def check_model_service_health() -> Dict:
        """
        Check if the model service is available and responding.
        
        This is a lightweight health check that verifies the model service
        is accessible and operational.
        
        Returns:
            Dictionary with health status information
        
        Example:
            {
                "success": true,
                "service": "model-service",
                "status": "healthy",
                "url": "http://localhost:8000"
            }
        """
        logger.info("Checking health of model service at %s", MODEL_SERVICE_URL)
        
        try:
            # Try to fetch models list with short timeout
            response = http_client.get(
                f"{MODEL_SERVICE_URL}/v1/models",
                timeout=5
            )
            
            is_healthy = response.status_code == 200
            status = "healthy" if is_healthy else f"unhealthy (HTTP {response.status_code})"
            
            logger.info("✓ Model service is %s", status)
            
            return {
                "success": True,
                "service": "model-service",
                "status": status,
                "url": MODEL_SERVICE_URL,
                "response_code": response.status_code
            }
        
        except Exception as e:
            logger.error("✗ Model service health check failed: %s", str(e))
            return {
                "success": False,
                "service": "model-service",
                "status": "unavailable",
                "url": MODEL_SERVICE_URL,
                "error": str(e)
            }
