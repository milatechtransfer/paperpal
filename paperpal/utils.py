from typing import List


def create_author_short(authors: List[str]) -> str:
    if len(authors) == 0:
        return ""
    elif len(authors) == 1:
        return authors[0]
    else:
        return authors[0] + " et al."
