import httpx
from constants import USER_AGENT


async def search_semantic_scholar(query: str, num_papers: int = 20) -> dict:
    """Search for papers on Semantic Scholar.

    Args:
        query (str): The search query
        num_papers (int): Number of papers to return. Defaults to 20.

    Returns:
        dict: The JSON response from Semantic Scholar API containing paper details

    Raises:
        httpx.HTTPError: If the API request fails
    """
    fields = "title,authors,url,abstract,tldr,citationStyles"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": num_papers,
                    "fields": fields
                },
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Failed to fetch papers from Semantic Scholar: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error while searching Semantic Scholar: {str(e)}")