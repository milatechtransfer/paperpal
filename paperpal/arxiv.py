import httpx
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Optional, Dict
from pydantic import BaseModel, model_validator
from constants import USER_AGENT
import asyncio

from utils import create_author_short
from bibtex import add_bibtex_to_papers


class ArxivPaper(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    authors: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    bibtex: Optional[str] = None
    arxiv_url: Optional[str] = None
    author_short: Optional[str] = None

    @model_validator(mode="after")
    def create_url(self):
        self.arxiv_url = f"https://arxiv.org/abs/{self.arxiv_id}"
        return self

    @model_validator(mode="after")
    def set_author_short(self):
        self.author_short = create_author_short(self.authors)
        return self

    def __str__(self) -> str:
        if self.error_message:
            return f"Error: {self.error_message}"
        else:
            return f"Title: {self.title}\nAuthors: {self.author_short}\nPaper ID: {self.arxiv_id}\nURL: {self.arxiv_url}\nCitation: {self.bibtex}"


async def search_arxiv(
    search_query: str, fetch_bibtex_data: bool = True
) -> List[ArxivPaper]:
    """
    Search arXiv for papers matching the query.

    Parameters:
    -----------
    search_query : str
        The search query string. Can include field-specific searches.
        This will be directly inserted into the URL as:
        "http://export.arxiv.org/api/query?search_query={search_query}"

        Examples:
        - 'all:electron' (search for 'electron' in all fields)
        - 'ti:neural networks' (search for 'neural networks' in title)
        - 'au:goodfellow' (search for author 'goodfellow')
        - 'all:electron+AND+all:proton' (search for both terms)
        - 'cat:cs.AI' (search in specific category)

        Complex ML literature review example:
        - 'ti:"attention mechanism"+AND+abs:"transformer"+AND+cat:cs.CL+AND+cat:cs.LG+ANDNOT+ti:survey&max_results=100&sortBy=submittedDate&sortOrder=descending'
          (Find papers with "attention mechanism" in title AND "transformer" in abstract,
           in both computational linguistics AND machine learning categories,
           excluding survey papers, limited to 100 results, sorted by newest first)

        Search operators:
        - AND: both terms must be present
        - OR: either term must be present
        - ANDNOT: first term without second term

        Search fields:
        - ti: title
        - au: author
        - abs: abstract
        - co: comment
        - jr: journal reference
        - cat: category
        - all: all fields

    fetch_bibtex_data : bool, optional
        Whether to fetch BibTeX data for each paper (default: True)

    Additional parameters (pass as part of search_query):
    ---------------------------------------------------
    max_results : int
        Maximum number of results to return (default: 10, max allowed: 2000)
        Example: 'all:electron&max_results=100'

    start : int
        Index of first result to return (default: 0)
        Example: 'all:electron&start=50'

    sortBy : str
        Sort order for results (default: 'relevance')
        Options: 'relevance', 'lastUpdatedDate', 'submittedDate'
        Example: 'all:electron&sortBy=lastUpdatedDate'

    sortOrder : str
        Direction of sort (default: 'descending')
        Options: 'ascending', 'descending'
        Example: 'all:electron&sortBy=submittedDate&sortOrder=ascending'

    Returns:
    --------
    List[ArxivPaper]
        A list of ArxivPaper objects containing paper information

    Notes:
    ------
    The URL is constructed as:
    "http://export.arxiv.org/api/query?search_query={search_query}"

    For more complex queries, you can see the arXiv API documentation at:
    https://arxiv.org/help/api/user-manual

    Examples of API URLs:
    http://export.arxiv.org/api/query?search_query=all:electron
    http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton&max_results=50
    """

    base_url = "http://export.arxiv.org/api/query"
    url = f"{base_url}?search_query={search_query}"

    # Set up headers
    headers = {"User-Agent": USER_AGENT}

    try:
        # Send the request using httpx
        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.text

        # Parse the XML response
        root = ET.fromstring(data)

        # Define namespaces
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        }

        papers: list[ArxivPaper] = []

        # Extract information for each entry
        for entry in root.findall(".//atom:entry", namespaces):
            # Extract the arXiv ID from the URL
            id_url = entry.find("./atom:id", namespaces).text
            arxiv_id = id_url.split("/")[-1]

            # Get PDF URL
            pdf_link = entry.find('./atom:link[@title="pdf"]', namespaces)
            pdf_url = pdf_link.get("href") if pdf_link is not None else None

            # Get authors
            authors = [
                author.find("./atom:name", namespaces).text
                for author in entry.findall("./atom:author", namespaces)
            ]

            # Get categories
            categories = [
                category.get("term")
                for category in entry.findall("./atom:category", namespaces)
            ]

            # Create ArxivPaper object
            paper = ArxivPaper(
                title=entry.find("./atom:title", namespaces).text.strip(),
                summary=entry.find("./atom:summary", namespaces).text.strip(),
                authors=authors,
                categories=categories,
                arxiv_id=arxiv_id,
                pdf_url=pdf_url,
                bibtex=None,  # Will be populated later if fetch_bibtex_data is True
            )

            papers.append(paper)

        # If fetch_bibtex_data is True, fetch BibTeX data for all papers
        if fetch_bibtex_data and papers:
            papers = await add_bibtex_to_papers(papers)

        return papers

    except httpx.HTTPError as e:
        # Return a single ArxivPaper with an error message
        return [ArxivPaper(error_message=f"HTTP error occurred: {str(e)}")]
    except ET.ParseError as e:
        return [ArxivPaper(error_message=f"XML parsing error: {str(e)}")]
    except Exception as e:
        return [ArxivPaper(error_message=f"An unexpected error occurred: {str(e)}")]


# Example usage:
if __name__ == "__main__":
    # Option 1: Search with BibTeX fetching

    search_query = 'ti:"attention mechanism"+AND+abs:"transformer"+AND+cat:cs.CL+AND+cat:cs.LG+ANDNOT+ti:survey&max_results=10&sortBy=submittedDate&sortOrder=descending'
    papers = asyncio.run(
        search_arxiv(
            search_query,
            fetch_bibtex_data=True,
        )
    )

    print(f"Found {len(papers)} papers")

    # Print results
    for i, paper in enumerate(papers, 1):
        if paper.error_message:
            print(f"Error: {paper.error_message}")
            continue

        print(f"\n--- Paper {i} ---")
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors or [])}")
        print(f"Categories: {', '.join(paper.categories or [])}")
        print(f"arXiv ID: {paper.arxiv_id}")
        print(f"PDF URL: {paper.pdf_url}")
        print(
            f"Summary: {paper.summary[:200]}..."
            if paper.summary
            else "No summary available"
        )
        print(
            f"BibTeX: {paper.bibtex[:150]}..."
            if paper.bibtex
            else "No BibTeX available"
        )
