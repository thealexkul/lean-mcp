"""
Simple REST API Tool Example
Example tool that makes REST API calls and returns string responses for LM Studio
"""
import os
import logging
import httpx
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://mymachine.cec.net:80")
TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Create reusable HTTP client
http_client = httpx.Client(timeout=TIMEOUT)


def register_tools(mcp_instance):
    """Register simple REST API tools with the MCP instance"""
    
    @mcp_instance.tool()
    def call_api_endpoint(endpoint: str, method: str = "GET") -> str:
        """
        Call a REST API endpoint and return the response as a string.
        
        This tool makes an HTTP request to your API and returns the response
        as a formatted string that LM Studio can easily consume and display.
        
        Args:
            endpoint: The API endpoint path (e.g., "/api/users" or "/v1/data")
            method: HTTP method to use - GET, POST, PUT, DELETE (default: GET)
        
        Returns:
            String containing the API response or error message
        
        Example:
            call_api_endpoint("/api/status") -> "Status: OK"
            call_api_endpoint("/api/users", "POST") -> "User created successfully"
        """
        # Normalize endpoint (ensure it starts with /)
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        
        full_url = f"{API_BASE_URL}{endpoint}"
        method = method.upper()
        
        logger.info("Calling API: %s %s", method, full_url)
        
        try:
            # Make the request based on method
            if method == "GET":
                response = http_client.get(full_url)
            elif method == "POST":
                response = http_client.post(full_url)
            elif method == "PUT":
                response = http_client.put(full_url)
            elif method == "DELETE":
                response = http_client.delete(full_url)
            else:
                return f"Error: Unsupported HTTP method '{method}'. Use GET, POST, PUT, or DELETE."
            
            response.raise_for_status()
            
            # Try to parse as JSON first, fall back to text
            try:
                data = response.json()
                # Format JSON nicely for display
                formatted = json.dumps(data, indent=2)
                logger.info("API call successful - returned JSON")
                return f"API Response:\n{formatted}"
            except (ValueError, TypeError):
                # Not JSON, return as text
                text_response = response.text.strip()
                logger.info("API call successful - returned text")
                if text_response:
                    return f"API Response:\n{text_response}"
                else:
                    return f"API Response: (empty) HTTP {response.status_code}"
        
        except httpx.TimeoutException:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("API timeout: %s", error_msg)
            return f"Error: {error_msg}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.error("API HTTP error: %s", error_msg)
            return f"Error: {error_msg}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("API connection error: %s", error_msg)
            return f"Error: {error_msg}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("API unexpected error: %s", error_msg)
            return f"Error: {error_msg}"
   
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
        full_url = f"{API_BASE_URL}{endpoint}"
        
        logger.info("=" * 60)
        logger.info("get_chassis() called")
        logger.info("  API_BASE_URL: %s", API_BASE_URL)
        logger.info("  Endpoint: %s", endpoint)
        logger.info("  Full URL: %s", full_url)
        logger.info("  Timeout: %s seconds", TIMEOUT)
        
        try:
            logger.info("Making GET request to %s", full_url)
            response = http_client.get(full_url, timeout=TIMEOUT)
            
            logger.info("Response received - Status: %s", response.status_code)
            logger.info("Response headers: %s", dict(response.headers))
            
            response.raise_for_status()
            
            logger.info("Parsing response as JSON...")
            data = response.json()
            logger.info("JSON parsed successfully, keys: %s", list(data.keys()) if isinstance(data, dict) else "Not a dict")
            
            logger.info("Formatting JSON with indent=2...")
            formatted = json.dumps(data, indent=2)
            logger.info("JSON formatted, length: %d characters", len(formatted))
            
            logger.info("Successfully retrieved chassis information")
            logger.info("=" * 60)
            return f"Chassis Information:\n{formatted}"
        
        except httpx.TimeoutException as e:
            error_msg = f"Request timed out after {TIMEOUT} seconds"
            logger.error("=" * 60)
            logger.error("Chassis API timeout")
            logger.error("  URL: %s", full_url)
            logger.error("  Error: %s", str(e))
            logger.error("=" * 60)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            error_detail = e.response.text[:500] if e.response.text else "No details"
            logger.error("=" * 60)
            logger.error("Chassis API HTTP error")
            logger.error("  URL: %s", full_url)
            logger.error("  Status: %s", e.response.status_code)
            logger.error("  Response text (first 500 chars): %s", error_detail)
            logger.error("=" * 60)
            return f"Error: {error_msg}\nEndpoint: {full_url}\nDetails: {error_detail}"
        
        except httpx.RequestError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("=" * 60)
            logger.error("Chassis API connection error")
            logger.error("  URL: %s", full_url)
            logger.error("  Error type: %s", type(e).__name__)
            logger.error("  Error: %s", str(e))
            logger.error("=" * 60)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error("=" * 60)
            logger.error("Chassis API JSON decode error")
            logger.error("  URL: %s", full_url)
            logger.error("  Response text (first 500 chars): %s", response.text[:500] if 'response' in locals() else "No response")
            logger.error("  JSON Error: %s", str(e))
            logger.error("=" * 60)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("=" * 60)
            logger.error("Chassis API unexpected error")
            logger.error("  URL: %s", full_url)
            logger.error("  Error type: %s", type(e).__name__)
            logger.error("  Error: %s", str(e))
            logger.error("  Traceback:", exc_info=True)
            logger.error("=" * 60)
            return f"Error: {error_msg}\nEndpoint: {full_url}"
