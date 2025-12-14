# eval/evaluate_rag.py

import asyncio

QUERIES = [
    ("lung CT", "CHEST"),
    ("brain MRI", "HEAD")
]

async def evaluate(store):
    score = 0
    for query, expected in QUERIES:
        results = await store.similarity_search(query)
        if expected in str(results[0].metadata):
            score += 1
    return score / len(QUERIES)
