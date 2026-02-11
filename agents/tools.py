from typing import List, Optional
from rag.search import search
import re


def search_docs(query: str, service: Optional[str] = None, k: int = 5) -> List[dict]:
    """
    Semantic search with multi-service detection using
    hybrid semantic + lexical service scoring.
    """

    # --- If explicit service provided, respect it ---
    if service:
        return search(query, service=service.lower(), k=k)

    q = query.lower()
    query_tokens = set(re.findall(r"\w+", q))

    # --- Global search first ---
    global_results = search(query, service=None, k=10)

    if not global_results:
        return []

    service_scores = {}

    for r in global_results:
        svc = r.get("service")
        if not svc:
            continue

        base_score = r["score"]

        heading = (r.get("heading") or "").lower()
        text_sample = (r.get("text") or "")[:300].lower()

        lexical_hits = sum(
            1 for token in query_tokens
            if token in heading or token in text_sample
        )

        lexical_boost = 1 + 0.05 * lexical_hits
        adjusted_score = base_score * lexical_boost

        service_scores.setdefault(svc, 0.0)
        service_scores[svc] += adjusted_score

    if not service_scores:
        return global_results[:k]

    # Sort services by total adjusted score
    sorted_services = sorted(
        service_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_service, top_score = sorted_services[0]
    significant = [top_service]

    # Include secondary services if meaningful
    for svc, score in sorted_services[1:]:
        if score >= 0.6 * top_score:
            significant.append(svc)

    print("Service scores:", service_scores)
    print("Significant:", significant)

    service_context = {}
    for svc in significant:
        svc_results = search(query, service=svc, k=k)
        service_context[svc] = svc_results

    return service_context
