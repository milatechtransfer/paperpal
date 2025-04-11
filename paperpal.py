from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import asyncio

# Initialize FastMCP server
mcp = FastMCP("paperpal")

# Constants
USER_AGENT = "paperpal-app/1.0"

class Paper(BaseModel):
    title: str
    summary: str
    id: str
    upvotes: int

    def __str__(self) -> str:
        return f"Title: {self.title}\nSummary: {self.summary}\nID: {self.id}\nUpvotes: {self.upvotes}"

def parse_paper(paper: dict) -> Paper:
    """Parse a paper from the HuggingFace API response."""
    return Paper(
        title=paper['paper']["title"],
        summary=paper['paper']["summary"],
        id=paper['paper']["id"],
        upvotes=paper['paper']["upvotes"],
    )

async def get_arxiv_info_async(paper_id: str, client: httpx.AsyncClient) -> str:
    """Get the Arxiv info for a paper asynchronously."""
    try:
        url = f"https://www.arxiv-txt.org/raw/abs/{paper_id}"
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching Arxiv info for paper {paper_id}. Try again later. {e}"

async def get_arxiv_info_for_papers_async(paper_ids: list[str], batch_size: int = 5) -> list[str]:
    """Get the Arxiv info for a list of papers concurrently, processing in batches.

    Args:
        paper_ids (list[str]): The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
        batch_size (int): Number of papers to process concurrently in each batch. Defaults to 5.

    Returns:
        list[str]: List of Arxiv info for all papers, in the same order as input paper_ids
    """
    results = []

    # Process papers in batches
    for i in range(0, len(paper_ids), batch_size):
        batch = paper_ids[i:i + batch_size]
        async with httpx.AsyncClient() as client:
            tasks = [get_arxiv_info_async(paper_id, client) for paper_id in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

    return results


def stringify_papers(papers: list[Paper]) -> str:
    """Format a list of papers into a string."""

    papers_str = "\n---\n".join([str(paper) for paper in papers])
    return f"List of papers:\n---\n{papers_str}\n---\n"


def semantic_search_huggingface_papers(query: str, top_n: int) -> list[Paper]:
    """Search for papers on HuggingFace."""

    url = f"https://huggingface.co/api/papers/search?q={query}"

    try:
        response = httpx.get(url)
        response.raise_for_status()
        papers_json = response.json()
        papers: list[Paper] = [parse_paper(paper) for paper in papers_json[:top_n]]

        return papers

    except Exception as e:
        return [f"Error fetching papers from HuggingFace. Try again later. {e}"]


@mcp.tool()
async def semantic_search_papers(query: str, top_n: int = 10) -> str:
    """Search for papers on HuggingFace using semantic search.

    Args:
        query (str): The query term to search for. It will automatically determine if it should use keywords or a natural language query, so format your queries accordingly.
        top_n (int): The number of papers to return. Default is 10, but you can set it to any number.

    Returns:
        str: A list of papers with the title, summary, ID, and upvotes.
    """
    papers: list[Paper] = semantic_search_huggingface_papers(query, top_n)

    return stringify_papers(papers)


@mcp.tool()
async def fetch_paper_details_from_arxiv(paper_ids: list[str]) -> str:
    """Get the Arxiv info for a list of papers.

    Args:
        paper_ids (list[str]): The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
    """
    arxiv_info = await get_arxiv_info_for_papers_async(paper_ids)
    return "\n---\n".join(arxiv_info)


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


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
