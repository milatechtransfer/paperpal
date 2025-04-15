from fastmcp import FastMCP
from fastmcp.prompts.prompt import UserMessage, AssistantMessage, Message

from arxiv import get_arxiv_info_from_arxiv_ids, ArxivPaper
from huggingface import semantic_search_huggingface_papers, HuggingFacePaper
from s2 import search_semantic_scholar, SemanticScholarPaper


# Initialize FastMCP server
mcp = FastMCP(
    name="paperpal",
)


def stringify_papers(
    papers: list[ArxivPaper | HuggingFacePaper | SemanticScholarPaper],
) -> str:
    """Format a list of papers into a string."""

    papers_str = "\n---\n".join([str(paper) for paper in papers])
    return f"List of papers:\n---\n{papers_str}\n---\n"


@mcp.tool()
async def search_papers_on_huggingface(query: str, top_n: int = 10) -> str:
    """Semantic and keyword search for papers on HuggingFace using semantic search.

    It is a good idea to use this tool iteratively to find papers on a given topic, trying different queries until you find the most relevant papers.

    Args:
        query (str): The query term to search for. It will automatically determine if it should use keywords or a natural language query, so format your queries accordingly.
        top_n (int): The number of papers to return. Default is 10, but you can set it to any number.

    Returns:
        str: A list of papers with the title, summary, ID, and upvotes.
    """
    papers: list[HuggingFacePaper] = semantic_search_huggingface_papers(query, top_n)

    return stringify_papers(papers)


@mcp.tool()
async def fetch_paper_details_from_arxiv(arxiv_ids: list[str] | str) -> str:
    """Get the Arxiv info for a list of papers.

    Args:
        arxiv_ids (list[str] | str): The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
    """
    arxiv_papers: list[ArxivPaper] = await get_arxiv_info_from_arxiv_ids(arxiv_ids)
    return stringify_papers(arxiv_papers)


@mcp.tool()
async def search_papers_on_semantic_scholar(query: str, top_n: int = 10) -> str:
    """Search for papers on Semantic Scholar using semantic search.

    Args:
        query (str): The query term to search for. It will automatically determine if it should use keywords or a natural language query, so format your queries accordingly.
        top_n (int): The number of papers to return. Default is 10, but you can set it to any number.

    Returns:
        str: A list of papers with the title, summary, ID, and upvotes.

    If you get a 429 error, it means you've hit the rate limit. You can try again in a few moments.

    """
    papers: list[SemanticScholarPaper] = search_semantic_scholar(query, top_n)
    return stringify_papers(papers)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
