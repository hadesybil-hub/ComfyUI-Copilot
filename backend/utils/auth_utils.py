# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

"""
Authentication utilities for ComfyUI Copilot
"""

from typing import Any, Dict, Optional
from .globals import set_comfyui_copilot_api_key, get_comfyui_copilot_api_key
from .logger import log


def redact_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a log-safe copy without API keys, tokens, or authorization data."""
    redacted: Dict[str, Any] = {}
    for key, value in config.items():
        lowered = key.lower()
        if any(marker in lowered for marker in ("api_key", "token", "authorization")):
            redacted[key] = "***" if value else value
        else:
            redacted[key] = value
    return redacted

def extract_and_store_api_key(request) -> Optional[str]:
    """
    Extract Bearer token from Authorization header and store it in globals
    
    Args:
        request: The aiohttp request object
        
    Returns:
        The extracted API key if successful, None otherwise
    """
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            set_comfyui_copilot_api_key(api_key)
            log.info("ComfyUI Copilot API key extracted and stored")
            
            # Verify it's stored correctly
            stored_key = get_comfyui_copilot_api_key()
            if stored_key == api_key:
                log.info("API key verification: Successfully stored in globals")
            else:
                log.error("API key verification: Storage failed")
                
            return api_key
        else:
            log.error("No valid Authorization header found")
            return None
    except Exception as e:
        log.error(f"Error extracting API key: {str(e)}")
        return None
