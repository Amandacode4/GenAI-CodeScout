import json
import requests
import os
import re

def normalize_arxiv_id(paper_id: str) -> str:
    """Extract just the ID part, e.g., from 'https://arxiv.org/abs/2205.14135' or '2205.14135v2' -> '2205.14135'"""
    # Remove URL parts
    if "arxiv.org" in paper_id:
        paper_id = paper_id.split("/")[-1]
    # Remove version suffix if any, though HF often handles it, it's safer to strip for exact matching or leave it?
    # Actually, HF handles standard arxiv ids well. We'll strip the URL prefix and leave the rest.
    return paper_id.strip()

def paper_search(query: str) -> str:
    """
    Search Hugging Face Papers API for a given query.
    """
    url = "https://huggingface.co/api/papers/search"
    params = {"q": query}
    headers = {}
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract papers
        results = []
        # Sometimes HF wraps it in a 'papers' key or returns a list directly
        papers = data.get("papers", data) if isinstance(data, dict) else data
        for item in papers[:5]:  # Top 5
            # Depending on schema, it might be nested
            paper_info = item.get("paper", item)
            results.append({
                "id": paper_info.get("id"),
                "title": paper_info.get("title"),
                "summary": paper_info.get("summary", "")[:200] + "..."
            })
        if not results:
            return "No papers found for this query on Hugging Face Papers."
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching papers: {e}"

def read_paper(paper_id: str) -> str:
    """
    Read the metadata and markdown content of a paper using HF API.
    """
    clean_id = normalize_arxiv_id(paper_id)
    base_url = f"https://huggingface.co/api/papers/{clean_id}"
    headers = {}
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    try:
        # Fetch metadata
        meta_resp = requests.get(base_url, headers=headers, timeout=10)
        if meta_resp.status_code == 404:
            return f"Error: Paper {clean_id} not found on Hugging Face Papers. Try using web_search with arxiv.org instead."
        meta_resp.raise_for_status()
        meta = meta_resp.json()
        
        title = meta.get("title", "Unknown Title")
        authors = [a.get("name") for a in meta.get("authors", [])]
        
        # Fetch markdown content
        md_url = f"https://huggingface.co/papers/{clean_id}.md"
        md_resp = requests.get(md_url, headers=headers, timeout=10)
        content = ""
        if md_resp.status_code == 200:
            content = md_resp.text
        else:
            content = meta.get("summary", "No abstract or markdown content available.")
            
        result = f"# {title}\nAuthors: {', '.join(authors)}\n\n{content}"
        return result[:8000] # Cap output to save context window
    except Exception as e:
        return f"Error reading paper: {e}"

PAPER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "paper_search",
            "description": "Search Hugging Face Papers index for academic papers by keyword.",
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
            "name": "read_paper",
            "description": "Read the metadata and markdown content of an academic paper using its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string", "description": "The ArXiv ID of the paper (e.g., '2205.14135')."}
                },
                "required": ["paper_id"]
            }
        }
    }
]