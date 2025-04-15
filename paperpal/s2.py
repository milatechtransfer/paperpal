import httpx
import asyncio
from pydantic import BaseModel
from constants import USER_AGENT

class SemanticScholarPaper(BaseModel):
    title: str | None = None
    abstract: str | None = None
    authors: list[str] | None = None
    paper_id: str | None = None
    url: str | None = None
    tldr: str | None = None
    citation: str | None = None
    raw_info: dict | None = None
    error_message: str | None = None

    def __str__(self) -> str:
        if self.error_message:
            return f"Error: {self.error_message}"
        else:
            return f"Title: {self.title}\nAbstract: {self.abstract}\nAuthors: {self.authors}\nPaper ID: {self.paper_id}\nURL: {self.url}\nTLDR: {self.tldr}\nCitation: {self.citation}"

def parse_semantic_scholar_paper(data) -> SemanticScholarPaper:
    """
    Parse a Semantic Scholar paper JSON into a simplified dictionary.

    Args:
        data (dict): The paper data from Semantic Scholar API

    Returns:
        SemanticScholarPaper: A simplified representation of the paper
    """
    try:
        # Extract author names
        author_names = [author.get("name", "") for author in data.get("authors", [])]

        # Extract TLDR text if available
        tldr_text = None
        if data.get("tldr") and data["tldr"].get("text"):
            tldr_text = data["tldr"]["text"]

        # Get citation if available
        citation = None
        if data.get("citationStyles") and data["citationStyles"].get("bibtex"):
            citation = data["citationStyles"]["bibtex"]

        data = {
            "title": data.get("title"),
            "abstract": data.get("abstract"),
            "authors": author_names,
            "paper_id": data.get("paperId"),
            "url": data.get("url"),
            "tldr": tldr_text,
            "citation": citation,
            "raw_info": data,
            "error_message": None
        }
        return SemanticScholarPaper(**data)
    except Exception as e:
        return SemanticScholarPaper(error_message=f"Failed to parse paper data: {str(e)}")

def search_semantic_scholar(query: str, num_papers: int = 20) -> list[SemanticScholarPaper]:
    """Search for papers on Semantic Scholar.

    Args:
        query (str): The search query
        num_papers (int): Number of papers to return. Defaults to 20.

    Returns:
        list[SemanticScholarPaper]: A list of Semantic Scholar papers

    Raises:
        httpx.HTTPError: If the API request fails
    """
    fields = "title,authors,url,abstract,tldr,citationStyles"

    try:
        response = httpx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": num_papers,
                "fields": fields
            },
            headers={"User-Agent": USER_AGENT}
        )

        # Check specifically for 429 status code
        if response.status_code == 429:
            return [SemanticScholarPaper(
                error_message=f"Rate limit exceeded. Try again after later."
            )]

        response.raise_for_status()
        data = response.json()['data']
        papers = [parse_semantic_scholar_paper(paper) for paper in data]
        return papers
    except httpx.HTTPError as e:
        return [SemanticScholarPaper(error_message=f"Failed to fetch papers from Semantic Scholar: {str(e)}")]
    except Exception as e:
        return [SemanticScholarPaper(error_message=f"Unexpected error while searching Semantic Scholar: {str(e)}")]