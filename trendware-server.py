import os
import json
import logging
from typing import List, Dict, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

# MCP server label can be anything; keep consistent with clients that call it.
mcp = FastMCP("SearchServer")

# Config (REPO_SERVER_URL must be set in the environment)
REPO_SERVER_URL = os.environ.get("REPO_SERVER_URL", "https://qsc-dev.quasiris.de/api/v1/search/demo/trendware").strip()
REQUEST_TIMEOUT = float(os.environ.get("REPO_REQUEST_TIMEOUT", "10"))


def fetch_documents(query: str, limit: int = 20):
    """
    Call the fetch endpoint and return its full payload, but ensure each document
    (either in result->...->documents or payload['documents'] or top-level list)
    has a 'text' field.
    """
    logger.info("fetch_documents called q=%r limit=%s", query, limit)

    try:
        r = requests.get(REPO_SERVER_URL, params={"q": query, "limit": limit}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        logger.exception("Error fetching docs from repo search: %s", e)
        return {}

    return payload

# Search MCP tool
@mcp.tool(name="search_products_tool")
async def search_products_tool(query: str, limit: int = 20):
    """
    Tool signature: search_products_tool(query: str, limit: int = 20)
    Returns a JSON-serializable list of documents.
    """
    logger.info("search_products_tool called q=%r limit=%s", query, limit)
    try:
        docs = fetch_documents(query, limit=limit)
        return json.loads(json.dumps(docs))
    except Exception as e:
        logger.exception("search_products_tool failed: %s", e)
        return []


if __name__ == "__main__":
    logger.info("Starting MCP Search server on http://0.0.0.0:8080/mcp")
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
    except Exception:
        logger.exception("MCP server terminated.")
