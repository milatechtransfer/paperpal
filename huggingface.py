from pydantic import BaseModel
import httpx

class HuggingFacePaper(BaseModel):
    title: str
    summary: str
    arxiv_id: str
    upvotes: int

    def __str__(self) -> str:
        return f"Title: {self.title}\nSummary: {self.summary}\nID: {self.arxiv_id}\nUpvotes: {self.upvotes}"

def parse_paper(paper: dict) -> HuggingFacePaper:
    """Parse a paper from the HuggingFace API response."""
    return HuggingFacePaper(
        title=paper['paper']["title"],
        summary=paper['paper']["summary"],
        arxiv_id=paper['paper']["id"],
        upvotes=paper['paper']["upvotes"],
    )





def semantic_search_huggingface_papers(query: str, top_n: int) -> list[HuggingFacePaper]:
    """Search for papers on HuggingFace."""

    url = f"https://huggingface.co/api/papers/search?q={query}"

    try:
        response = httpx.get(url)
        response.raise_for_status()
        papers_json = response.json()
        papers: list[HuggingFacePaper] = [parse_paper(paper) for paper in papers_json[:top_n]]

        return papers

    except Exception as e:
        return [f"Error fetching papers from HuggingFace. Try again later. {e}"]