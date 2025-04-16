import asyncio
from typing import Optional
from bibtex import add_bibtex_to_papers
from pydantic import BaseModel, model_validator
import httpx
from utils import create_author_short


class HuggingFacePaper(BaseModel):
    title: str
    summary: str
    authors: list[str]
    arxiv_id: str
    upvotes: int
    arxiv_url: str = (
        None  # This will be populated after the class is created from the arxiv_id
    )
    bibtex: Optional[str] = None
    error_message: Optional[str] = None
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
        return f"Title: {self.title}\nSummary: {self.summary}\nID: {self.arxiv_id}\nUpvotes: {self.upvotes}\nURL: {self.arxiv_url}"


def parse_authors(authors_data: dict) -> list[str]:
    """
    Parse authors from the provided data string.

    Args:
        authors_data (dict): Dictionary containing paper data from HuggingFace API

    Returns:
        list: List of author names
    """
    authors = []
    for author in authors_data:
        if "name" in author:
            authors.append(author["name"])

    return authors


def parse_paper(paper: dict) -> HuggingFacePaper:
    """Parse a paper from the HuggingFace API response."""
    return HuggingFacePaper(
        title=paper["paper"]["title"],
        summary=paper["paper"]["summary"],
        arxiv_id=paper["paper"]["id"],
        upvotes=paper["paper"]["upvotes"],
        authors=parse_authors(paper["paper"]["authors"]),
    )


async def semantic_search_huggingface_papers(
    query: str, top_n: int, fetch_bibtex_data: bool = True
) -> list[HuggingFacePaper]:
    """Search for papers on HuggingFace."""

    url = f"https://huggingface.co/api/papers/search?q={query}"

    try:
        response = httpx.get(url)
        response.raise_for_status()
        papers_json = response.json()
        papers: list[HuggingFacePaper] = [
            parse_paper(paper) for paper in papers_json[:top_n]
        ]

        if fetch_bibtex_data and papers:
            papers = await add_bibtex_to_papers(papers)

        return papers

    except Exception as e:
        return [
            HuggingFacePaper(
                error_message=f"Error fetching papers from HuggingFace. Try again later. {e}"
            )
        ]


if __name__ == "__main__":
    query = "trasformers SOTA TTS models"
    papers = asyncio.run(
        semantic_search_huggingface_papers(query, top_n=10, fetch_bibtex_data=True)
    )

    # Print results
    for i, paper in enumerate(papers, 1):
        if paper.error_message:
            print(f"Error: {paper.error_message}")
            continue

        print(f"\n--- Paper {i} ---")
        print(f"Title: {paper.title}")
        print(f"Upvotes: {paper.upvotes}")
        print(f"Authors: {paper.authors}")
        print(f"arXiv ID: {paper.arxiv_id}")
        print(f"Arxiv URL: {paper.arxiv_url}")
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
