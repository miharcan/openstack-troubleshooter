from typing import List, Optional
from rag.search import search


def search_docs(
    query: str,
    service: Optional[str] = None,
    k: int = 5,
) -> List[dict]:
    """
    Semantic search over OpenStack documentation.
    """
    results = search(query, k=k)

    if service:
        results = [
            r for r in results
            if r.get("service") == service
        ]

    return results
