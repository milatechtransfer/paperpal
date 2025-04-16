from fastmcp import FastMCP
from fastmcp.prompts.prompt import UserMessage, AssistantMessage, Message

from arxiv import ArxivPaper, search_arxiv
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
        str: A list of papers with the title, summary, ID, upvotes, authors and bibtex.
    """
    papers: list[HuggingFacePaper] = await semantic_search_huggingface_papers(query, top_n)

    return stringify_papers(papers)


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


@mcp.tool()
async def search_papers_on_arxiv(search_query: str, fetch_bibtex_data: bool = True) -> str:
    """
    Search arXiv for papers matching your query.

    Parameters:
    -----------
    search_query : str
        The properly formatted search query for arXiv.

        The query must begin with "ti:" or "abs:" or "au:" or "cat:" or "all:"
            - "all:neural networks" (search in all fields)
            - "ti:transformer" (search in title)
            - "au:goodfellow" (search for author)
            - "cat:cs.AI" (search in category)

        The query will be formatted as:
            base_url = "http://export.arxiv.org/api/query"
            url = f"{base_url}?search_query={search_query}"

        So be sure to format your query correctly.

    fetch_bibtex_data : bool, optional
        Whether to fetch BibTeX data for each paper (default: True)

    Returns:
    --------
    str: A list of papers with their titles, summaries, authors, and other metadata.

    Notes:
    ------
    Keep your queries simple and focused. If you don't get the results you want,
    try refining your search term rather than using complex query syntax.

    A very complex query might look like this:
    search_query = 'ti:"attention mechanism"+AND+abs:"transformer"+AND+cat:cs.CL+AND+cat:cs.LG+ANDNOT+ti:survey&max_results=10&sortBy=submittedDate&sortOrder=descending'

    Only use the query syntax if you know what you're doing and once you've searched for other papers with simpler queries.
    """

    papers: list[ArxivPaper] = await search_arxiv(search_query, fetch_bibtex_data=fetch_bibtex_data)
    return stringify_papers(papers)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
