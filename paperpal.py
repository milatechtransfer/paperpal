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
    url = f"https://www.arxiv-txt.org/raw/abs/{paper_id}"
    response = await client.get(url)
    response.raise_for_status()
    return response.text

async def get_arxiv_info_for_papers_async(papers: list[Paper]) -> list[str]:
    """Get the Arxiv info for a list of papers concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [get_arxiv_info_async(paper.id, client) for paper in papers]
        return await asyncio.gather(*tasks)


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
async def search_papers(query: str, top_n: int = 10) -> str:
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
async def get_arxiv_info(paper_ids: list[str]) -> str:
    """Get the Arxiv info for a list of papers.

    Args:
        paper_ids (list[str]): The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
    """
    async with httpx.AsyncClient() as client:
        tasks = [get_arxiv_info_async(paper_id, client) for paper_id in paper_ids]
        arxiv_info = await asyncio.gather(*tasks)
        return "\n---\n".join(arxiv_info)



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
