import csv
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from app.retrieval import retrieve_chunks

load_dotenv()
logger = logging.getLogger("editorial_rag.evaluation")

EVAL_CSV = Path(__file__).parent.parent / "data" / "eval_queries.csv"


def load_eval_queries(csv_path: Path) -> list[dict]:
    queries = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row)
    return queries


def compute_recall_at_k(retrieved_sources: list[str], relevant_source: str, k: int) -> float:
    pass


def compute_mrr(retrieved_sources: list[str], relevant_source: str) -> float:
    pass


def run_evaluation(k: int = 5) -> dict:
    queries = load_eval_queries(EVAL_CSV)
    if not queries:
        logger.warning("No evaluation queries found in %s", EVAL_CSV)
        return {"recall@k": 0.0, "mrr": 0.0, "k": k, "num_queries": 0}

    recall_scores = []
    mrr_scores = []

    for entry in queries:
        question = entry.get("question", "")
        relevant_source = entry.get("relevant_source", "")

        if not question or not relevant_source:
            logger.warning("Skipping malformed eval row: %s", entry)
            continue

        chunks = retrieve_chunks(question, top_k=k)
        retrieved_sources = [c["source"] for c in chunks]

        recall = compute_recall_at_k(retrieved_sources, relevant_source, k)
        mrr = compute_mrr(retrieved_sources, relevant_source)

        recall_scores.append(recall)
        mrr_scores.append(mrr)

    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    return {
        "recall@k": round(avg_recall, 4),
        "mrr": round(avg_mrr, 4),
        "k": k,
        "num_queries": len(recall_scores),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_evaluation(k=5)
    print(f"Evaluation Results:")
    print(f"  recall@5 : {results['recall@k']}")
    print(f"  MRR      : {results['mrr']}")
    print(f"  Queries  : {results['num_queries']}")
