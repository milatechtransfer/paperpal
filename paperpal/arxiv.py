import httpx
import asyncio
from pydantic import BaseModel

class ArxivPaper(BaseModel):
    title: str | None = None
    summary: str | None = None
    authors: list[str] | None = None
    categories: list[str] | None = None
    arxiv_id: str | None = None
    url: str | None = None
    raw_arxiv_info: str | None = None
    error_message: str | None = None

    def __str__(self) -> str:
        if self.error_message:
            return f"Error: {self.error_message}"
        else:
            return self.raw_arxiv_info

def parse_arxiv_info(raw_arxiv_info: str) -> ArxivPaper:
    """Parse the raw txt Arxiv info for a paper from arxiv-txt.org into a ArxivPaper object.
    The input should be in the following markdown format:

    # Title
    [title]

    # Authors
    [comma-separated authors]

    # Abstract
    [abstract text]

    # Categories
    [comma-separated categories]

    # Publication Details
    - Published: [date]
    - arXiv ID: [id]

    # BibTeX
    [bibtex entry]
    """
    lines = raw_arxiv_info.strip().split('\n')
    current_section = None
    data = {
        'title': '',
        'summary': '',
        'authors': [],
        'categories': [],
        'arxiv_id': '',
        'url': ''
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('# '):
            current_section = line[2:].lower()
            continue

        if current_section == 'title':
            data['title'] = line
        elif current_section == 'authors':
            authors = [a.strip() for a in line.split(',')]
            data['authors'].extend(authors)
        elif current_section == 'abstract':
            data['summary'] += line + ' '
        elif current_section == 'categories':
            categories = [c.strip() for c in line.split(',')]
            data['categories'].extend(categories)
        elif current_section == 'publication details':
            if 'arXiv ID:' in line:
                data['arxiv_id'] = line.split('arXiv ID:')[1].strip()
                data['url'] = f"https://arxiv.org/abs/{data['arxiv_id']}"

    # Clean up the summary by removing extra spaces
    data['summary'] = data['summary'].strip()
    data['raw_arxiv_info'] = raw_arxiv_info

    return ArxivPaper(**data)

async def get_arxiv_info_single(arxiv_id: str, client: httpx.AsyncClient) -> ArxivPaper | None:
    """Get the Arxiv info for a paper asynchronously.

    Args:
        arxiv_id (str): The ID of the paper to get the Arxiv info for, e.g. "2503.01469"

    Returns:
        ArxivPaper | None: The parsed Arxiv paper info, or None if there was an error
    """
    try:
        url = f"https://www.arxiv-txt.org/raw/abs/{arxiv_id}"
        response = await client.get(url)
        response.raise_for_status()
        raw_arxiv_info = response.text
        return parse_arxiv_info(raw_arxiv_info)
    except Exception as e:
        print(f"Error fetching Arxiv info for paper {arxiv_id}: {e}")
        return ArxivPaper(arxiv_id=arxiv_id, error_message=str(e))

async def get_arxiv_info_batch(arxiv_ids: list[str], batch_size: int) -> list[ArxivPaper | None]:
    """Get the Arxiv info for a list of papers concurrently, processing in batches.

    Args:
        arxiv_ids (list[str]): The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
        batch_size (int): Number of papers to process concurrently in each batch. Defaults to 5.

    Returns:
        dict[str, ArxivPaper | None]: Dictionary of Arxiv info for all papers, with paper IDs as keys
    """
    results = []

    # Process papers in batches
    for i in range(0, len(arxiv_ids), batch_size):
        batch_arxiv_ids = arxiv_ids[i:i + batch_size]
        async with httpx.AsyncClient() as client:
            tasks = [get_arxiv_info_single(arxiv_id, client) for arxiv_id in batch_arxiv_ids]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

    return results


async def get_arxiv_info_from_arxiv_ids(arxiv_ids: list[str], batch_size: int = 5) -> list[str]:
    """Get the Arxiv info for a list of papers concurrently, processing in batches.

    Args:
        arxiv_ids list[str]: The IDs of the papers to get the Arxiv info for, e.g. ["2503.01469", "2503.01470"]
        batch_size (int): Number of papers to process concurrently in each batch. Defaults to 5.

    Returns:
        list[str]: List of Arxiv info for all papers, in the same order as input paper_ids
    """
    if isinstance(arxiv_ids, list):
        return await get_arxiv_info_batch(arxiv_ids, batch_size)
    else:
        raise ValueError("arxiv_ids must be a list of strings")

