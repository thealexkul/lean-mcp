"""
Simple REST API Tool Example
Example tool that makes REST API calls and returns string responses for LM Studio
"""
import os
import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:80")
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
                import json
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
    def call_api_with_body(endpoint: str, body: str, method: str = "POST") -> str:
        """
        Call a REST API endpoint with a request body and return the response.
        
        This tool sends JSON data to your API endpoint and returns the response
        as a formatted string.
        
        Args:
            endpoint: The API endpoint path (e.g., "/api/users")
            body: JSON string to send in the request body
            method: HTTP method - POST or PUT (default: POST)
        
        Returns:
            String containing the API response or error message
        
        Example:
            call_api_with_body("/api/users", '{"name": "John"}') -> "User created"
        """
        # Normalize endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        
        full_url = f"{API_BASE_URL}{endpoint}"
        method = method.upper()
        
        if method not in ["POST", "PUT", "PATCH"]:
            return f"Error: Method '{method}' not supported with body. Use POST, PUT, or PATCH."
        
        logger.info("Calling API with body: %s %s", method, full_url)
        
        try:
            # Parse body as JSON
            import json
            try:
                body_data = json.loads(body)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in body: {str(e)}"
            
            # Make request
            if method == "POST":
                response = http_client.post(full_url, json=body_data)
            elif method == "PUT":
                response = http_client.put(full_url, json=body_data)
            elif method == "PATCH":
                response = http_client.patch(full_url, json=body_data)
            
            response.raise_for_status()
            
            # Format response
            try:
                data = response.json()
                formatted = json.dumps(data, indent=2)
                logger.info("API call with body successful")
                return f"API Response:\n{formatted}"
            except (ValueError, TypeError):
                text_response = response.text.strip()
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
    def check_api_health() -> str:
        """
        Check if the API service is available and responding.
        
        This is a simple health check that tries to reach your API service
        and returns a status message.
        
        Returns:
            String with health status
        
        Example:
            check_api_health() -> "API is healthy and responding"
        """
        logger.info("Checking API health at %s", API_BASE_URL)
        
        try:
            # Try a simple GET request (you might want to use a specific health endpoint)
            response = http_client.get(API_BASE_URL, timeout=5)
            
            if response.status_code == 200:
                status = "healthy and responding"
            else:
                status = f"responding with HTTP {response.status_code}"
            
            logger.info("API health check: %s", status)
            return f"API at {API_BASE_URL} is {status}"
        
        except httpx.TimeoutException:
            logger.error("API health check timed out")
            return f"Error: API at {API_BASE_URL} is not responding (timeout)"
        
        except httpx.RequestError as e:
            logger.error("API health check failed: %s", str(e))
            return f"Error: Cannot reach API at {API_BASE_URL} - {str(e)}"
        
        except Exception as e:
            logger.error("API health check error: %s", str(e))
            return f"Error: {str(e)}"

