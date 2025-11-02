"""
Model Service Tools
Tools for interacting with the model service (localhost:8000) and iDRAC APIs
"""
import os
import logging
import httpx
import json
from typing import Dict

logger = logging.getLogger(__name__)

# Configuration
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:8000")
IDRAC_BASE_URL = os.getenv("IDRAC_BASE_URL", "http://localhost:80")
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
    
    
    # ========================================================================
    # iDRAC/Specific REST API Tools
    # These return formatted JSON strings for better LM Studio readability
    # ========================================================================
    
    @mcp_instance.tool()
    def get_chassis() -> str:
        """
        Get chassis information from iDRAC API.
        
        Retrieves detailed chassis information including hardware status,
        power state, model, serial number, and other chassis-level data
        from the /idrac/v1/Chassis endpoint.
        
        Returns:
            Formatted JSON string with chassis information, or error message
        
        Example response:
            {
              "Id": "System.Embedded.1",
              "Name": "System Chassis",
              "ChassisType": "RackMount",
              "PowerState": "On",
              "Status": {
                "State": "Enabled",
                "Health": "OK"
              }
            }
        """
        endpoint = "/idrac/v1/Chassis"
        full_url = f"{IDRAC_BASE_URL}{endpoint}"
        
        logger.info("Fetching chassis data from %s", full_url)
        
        try:
            response = http_client.get(full_url, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            formatted = json.dumps(data, indent=2)
            
            logger.info("Successfully retrieved chassis information")
            return f"Chassis Information:\n{formatted}"
        
        except httpx.TimeoutException:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("Chassis API timeout: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            error_detail = e.response.text[:500] if e.response.text else "No details"
            logger.error("Chassis API HTTP error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}\nDetails: {error_detail}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("Chassis API connection error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error("Chassis API JSON error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Chassis API unexpected error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
    
    
    @mcp_instance.tool()
    def get_system_info() -> str:
        """
        Get system information from iDRAC API.
        
        Retrieves detailed system information including server model,
        BIOS version, processor details, memory, and system status
        from the /idrac/v1/Systems endpoint.
        
        Returns:
            Formatted JSON string with system information, or error message
        
        Example response:
            {
              "Id": "System.Embedded.1",
              "Name": "System",
              "Model": "PowerEdge R740",
              "ProcessorSummary": {
                "Count": 2,
                "Model": "Intel Xeon"
              },
              "MemorySummary": {
                "TotalSystemMemoryGiB": 256
              }
            }
        """
        endpoint = "/idrac/v1/Systems"
        full_url = f"{IDRAC_BASE_URL}{endpoint}"
        
        logger.info("Fetching system info from %s", full_url)
        
        try:
            response = http_client.get(full_url, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            formatted = json.dumps(data, indent=2)
            
            logger.info("Successfully retrieved system information")
            return f"System Information:\n{formatted}"
        
        except httpx.TimeoutException:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("System API timeout: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            error_detail = e.response.text[:500] if e.response.text else "No details"
            logger.error("System API HTTP error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}\nDetails: {error_detail}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("System API connection error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error("System API JSON error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("System API unexpected error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
    
    
    @mcp_instance.tool()
    def get_thermal_info() -> str:
        """
        Get thermal (temperature/fan) information from iDRAC API.
        
        Retrieves temperature readings, fan speeds, and thermal status
        from the /idrac/v1/Chassis/Thermal endpoint.
        
        Returns:
            Formatted JSON string with thermal information, or error message
        
        Example response:
            {
              "Temperatures": [
                {"Name": "CPU1 Temp", "ReadingCelsius": 45, "Status": "OK"},
                {"Name": "CPU2 Temp", "ReadingCelsius": 47, "Status": "OK"}
              ],
              "Fans": [
                {"Name": "Fan1", "Reading": 3600, "Status": "OK"}
              ]
            }
        """
        endpoint = "/idrac/v1/Chassis/Thermal"
        full_url = f"{IDRAC_BASE_URL}{endpoint}"
        
        logger.info("Fetching thermal info from %s", full_url)
        
        try:
            response = http_client.get(full_url, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            formatted = json.dumps(data, indent=2)
            
            logger.info("Successfully retrieved thermal information")
            return f"Thermal Information:\n{formatted}"
        
        except httpx.TimeoutException:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("Thermal API timeout: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            error_detail = e.response.text[:500] if e.response.text else "No details"
            logger.error("Thermal API HTTP error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}\nDetails: {error_detail}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("Thermal API connection error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error("Thermal API JSON error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Thermal API unexpected error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
    
    
    @mcp_instance.tool()
    def get_power_info() -> str:
        """
        Get power supply and consumption information from iDRAC API.
        
        Retrieves power supply status, power consumption metrics,
        and power-related data from the /idrac/v1/Chassis/Power endpoint.
        
        Returns:
            Formatted JSON string with power information, or error message
        
        Example response:
            {
              "PowerSupplies": [
                {"Name": "PSU1", "PowerCapacityWatts": 750, "Status": "OK"}
              ],
              "PowerControl": [
                {"PowerConsumedWatts": 245, "PowerCapacityWatts": 1500}
              ]
            }
        """
        endpoint = "/idrac/v1/Chassis/Power"
        full_url = f"{IDRAC_BASE_URL}{endpoint}"
        
        logger.info("Fetching power info from %s", full_url)
        
        try:
            response = http_client.get(full_url, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            formatted = json.dumps(data, indent=2)
            
            logger.info("Successfully retrieved power information")
            return f"Power Information:\n{formatted}"
        
        except httpx.TimeoutException:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("Power API timeout: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            error_detail = e.response.text[:500] if e.response.text else "No details"
            logger.error("Power API HTTP error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}\nDetails: {error_detail}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("Power API connection error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error("Power API JSON error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Power API unexpected error: %s", error_msg)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
