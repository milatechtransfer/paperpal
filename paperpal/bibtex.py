import httpx
import asyncio
from typing import List, Dict, Optional, Any
from constants import USER_AGENT


async def fetch_bibtex(
    arxiv_id: str, client: Optional[httpx.AsyncClient] = None
) -> str:
    """Fetch the BibTeX for a given Arxiv ID.

    Args:
        arxiv_id (str): The ID of the paper to get the BibTeX for, e.g. "2503.01469"
        client (httpx.AsyncClient, optional): An existing client to use. If None, a new one will be created.

    Returns:
        str: The BibTeX for the given Arxiv ID
    """
    # Construct the BibTeX URL
    bibtex_url = f"https://arxiv.org/bibtex/{arxiv_id}"

    # Set up the headers
    headers = {"User-Agent": USER_AGENT}

    # Make the request
    try:
        # If a client is provided, use it. Otherwise, create a new one.
        if client is not None:
            response = await client.get(bibtex_url, headers=headers)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(bibtex_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            bibtex_content = response.text
            return bibtex_content
        else:
            print(
                f"Failed to fetch BibTeX: {response.status_code} {response.reason_phrase}"
            )
            return ""
    except Exception as e:
        print(f"Error fetching BibTeX: {str(e)}")
        return ""


async def fetch_bibtex_batch(
    arxiv_ids: List[str], batch_size: int = 5
) -> Dict[str, str]:
    """Fetch the BibTeX for a list of Arxiv IDs concurrently.

    Args:
        arxiv_ids (List[str]): The IDs of the papers to get the BibTeX for
        batch_size (int, optional): Number of requests to make concurrently. Defaults to 5.

    Returns:
        Dict[str, str]: Dictionary of BibTeX for all papers, with paper IDs as keys
    """
    results = {}

    # Process papers in batches
    for i in range(0, len(arxiv_ids), batch_size):
        batch_arxiv_ids = arxiv_ids[i : i + batch_size]
        async with httpx.AsyncClient() as client:
            tasks = [fetch_bibtex(arxiv_id, client) for arxiv_id in batch_arxiv_ids]
            batch_results = await asyncio.gather(*tasks)
            results.update(dict(zip(batch_arxiv_ids, batch_results)))

    return results


async def add_bibtex_to_papers(papers: List[Any], batch_size: int = 5) -> List[Any]:
    # TODO: Don't pass Any, pass arxivpaper or huggingface paper but import them to avoid circular imports
    """
    Add BibTeX data to a list of ArxivPaper objects.

    Parameters:
    -----------
    papers : List[ArxivPaper]
        The list of papers to add BibTeX data to
    batch_size : int, optional
        Number of BibTeX requests to make concurrently (default: 5)

    Returns:
    --------
    List[ArxivPaper]
        The same list of papers with BibTeX data added
    """
    # Get all arxiv_ids
    arxiv_ids = [
        paper.arxiv_id for paper in papers if paper.arxiv_id and not paper.bibtex
    ]

    if not arxiv_ids:
        return papers  # No papers need BibTeX data

    # Fetch BibTeX data
    bibtex_dict = await fetch_bibtex_batch(arxiv_ids, batch_size)

    # Add BibTeX data to each paper
    for paper in papers:
        if paper.arxiv_id in bibtex_dict and not paper.bibtex:
            paper.bibtex = bibtex_dict[paper.arxiv_id]

    return papers
