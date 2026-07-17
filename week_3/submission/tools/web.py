import json
import os
import requests
import trafilatura

def web_search(query: str, serper_api_key: str) -> str:
    """
    Search the web using Serper API.
    Returns a JSON string of results.
    """
    if not serper_api_key:
        return "Error: SERPER_API_KEY is not set."
        
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract organic results
        results = []
        if "organic" in data:
            for item in data["organic"][:5]:  # Return top 5 results
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                })
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error performing web search: {e}"

def web_fetch(url: str) -> str:
    """
    Fetch the content of a URL and extract the main article text using trafilatura.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return f"Error: Could not download {url}"
            
        result = trafilatura.extract(downloaded)
        if result is None:
            return f"Error: Could not extract text from {url}"
            
        return result[:4000]  # Truncate strictly to avoid context limit issues with multiple fetches
    except Exception as e:
        return f"Error fetching url: {e}"

WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for a given query to find recent information or URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and extract the main text content from a web page URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL of the page to read."}
                },
                "required": ["url"]
            }
        }
    }
]
