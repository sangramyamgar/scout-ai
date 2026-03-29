"""
Evaluation pipeline using Ragas.
Creates golden datasets and measures RAG quality.
"""

import json
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document


# Golden evaluation dataset - manually curated Q&A pairs
GOLDEN_DATASET = {
    "finance": [
        {
            "question": "What was the company's gross margin in 2024?",
            "ground_truth": "60%",
            "context_keywords": ["gross margin", "60%", "2024"],
        },
        {
            "question": "What is the net margin for the company Technologies?",
            "ground_truth": "12%",
            "context_keywords": ["net margin", "12%"],
        },
        {
            "question": "How much did the company spend on vendor services?",
            "ground_truth": "$30M",
            "context_keywords": ["vendor services", "30M"],
        },
        {
            "question": "What percentage did revenue grow in 2024?",
            "ground_truth": "25%",
            "context_keywords": ["revenue", "grew", "25%"],
        },
        {
            "question": "What is the company's Days Sales Outstanding (DSO)?",
            "ground_truth": "45 days",
            "context_keywords": ["DSO", "45 days"],
        },
    ],
    "hr": [
        {
            "question": "What is the EPF contribution rate for employees?",
            "ground_truth": "12% employer and employee contribution",
            "context_keywords": ["EPF", "12%", "contribution"],
        },
        {
            "question": "How many weeks of maternity leave are provided?",
            "ground_truth": "26 weeks paid leave for first two children",
            "context_keywords": ["maternity", "26 weeks"],
        },
        {
            "question": "What are the company's core values?",
            "ground_truth": "Integrity, Respect, Innovation, Customer Focus, Accountability",
            "context_keywords": ["integrity", "respect", "innovation"],
        },
    ],
    "engineering": [
        {
            "question": "What compliance standards does the company follow?",
            "ground_truth": "GDPR, DPDP, PCI-DSS",
            "context_keywords": ["GDPR", "DPDP", "PCI-DSS", "compliance"],
        },
    ],
    "marketing": [
        {
            "question": "What marketing initiatives were planned for Q4 2024?",
            "ground_truth": "Digital marketing, B2B initiatives, customer retention programs",
            "context_keywords": ["marketing", "Q4", "digital", "B2B"],
        },
    ],
    "general": [
        {
            "question": "When was the company Technologies founded?",
            "ground_truth": "2016",
            "context_keywords": ["founded", "2016"],
        },
        {
            "question": "What is the company's vision?",
            "ground_truth": "To empower businesses and individuals through innovative technology solutions",
            "context_keywords": ["vision", "empower", "technology"],
        },
    ],
}


def get_evaluation_dataset(departments: List[str] = None) -> List[dict]:
    """
    Get evaluation dataset for specified departments.

    Args:
        departments: List of department names (None = all)

    Returns:
        List of evaluation samples
    """
    if departments is None:
        departments = list(GOLDEN_DATASET.keys())

    samples = []
    for dept in departments:
        if dept in GOLDEN_DATASET:
            for item in GOLDEN_DATASET[dept]:
                samples.append({
                    **item,
                    "department": dept,
                })

    return samples


def evaluate_response(
    question: str,
    response: str,
    ground_truth: str,
    retrieved_docs: List[Document],
) -> dict:
    """
    Evaluate a single RAG response.

    Metrics:
    - Faithfulness: Is the response grounded in retrieved context?
    - Answer Relevancy: Does the response answer the question?
    - Context Recall: Does the context contain the ground truth?

    Args:
        question: User question
        response: Generated response
        ground_truth: Expected answer
        retrieved_docs: Documents used for context

    Returns:
        Dictionary of evaluation metrics
    """
    # Simple rule-based evaluation (for demo)
    # In production, use Ragas with LLM-based evaluation

    # Check if ground truth appears in response
    answer_match = ground_truth.lower() in response.lower()

    # Check if response mentions "don't have information" (failure case)
    no_info = "don't have" in response.lower() or "cannot" in response.lower()

    # Check context recall (is ground truth in retrieved docs?)
    context_text = " ".join([doc.page_content for doc in retrieved_docs])
    context_recall = ground_truth.lower() in context_text.lower()

    # Calculate simple scores
    faithfulness = 1.0 if answer_match and not no_info else 0.0
    relevancy = 1.0 if answer_match else (0.5 if not no_info else 0.0)
    recall = 1.0 if context_recall else 0.0

    return {
        "faithfulness": faithfulness,
        "answer_relevancy": relevancy,
        "context_recall": recall,
        "answer_match": answer_match,
        "no_info_response": no_info,
    }


def run_evaluation(
    role: str = "c_level",
    output_file: Optional[str] = None,
) -> dict:
    """
    Run full evaluation on the RAG pipeline.

    Args:
        role: Role to use for evaluation (c_level has full access)
        output_file: Optional path to save results

    Returns:
        Evaluation results summary
    """
    from app.agents.rag_pipeline import run_query
    from app.core.vectorstore import get_vector_store

    # Get role's accessible departments
    from app.core.config import ROLES
    role_config = ROLES.get(role, ROLES["c_level"])
    accessible_depts = role_config["collections"]

    # Get evaluation samples for accessible departments
    samples = get_evaluation_dataset(accessible_depts)

    results = []
    total_faithfulness = 0
    total_relevancy = 0
    total_recall = 0

    print(f"\n🔬 Running evaluation with {len(samples)} samples...")
    print("=" * 60)

    for i, sample in enumerate(samples):
        question = sample["question"]
        ground_truth = sample["ground_truth"]

        print(f"\n[{i+1}/{len(samples)}] {question[:50]}...")

        # Run query through pipeline
        result = run_query(question, role)

        # Get retrieved docs for evaluation
        store = get_vector_store()
        retrieved_docs = store.search_by_role(question, role, top_k=5)

        # Evaluate
        metrics = evaluate_response(
            question=question,
            response=result.get("response", ""),
            ground_truth=ground_truth,
            retrieved_docs=retrieved_docs,
        )

        results.append({
            "question": question,
            "department": sample["department"],
            "ground_truth": ground_truth,
            "response": result.get("response", "")[:200],
            "metrics": metrics,
        })

        total_faithfulness += metrics["faithfulness"]
        total_relevancy += metrics["answer_relevancy"]
        total_recall += metrics["context_recall"]

        status = "✅" if metrics["answer_match"] else "❌"
        print(f"   {status} Faithfulness: {metrics['faithfulness']:.2f}")

    # Calculate averages
    n = len(samples)
    summary = {
        "total_samples": n,
        "avg_faithfulness": total_faithfulness / n if n > 0 else 0,
        "avg_relevancy": total_relevancy / n if n > 0 else 0,
        "avg_context_recall": total_recall / n if n > 0 else 0,
        "results": results,
    }

    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Samples: {n}")
    print(f"Avg Faithfulness: {summary['avg_faithfulness']:.2%}")
    print(f"Avg Relevancy: {summary['avg_relevancy']:.2%}")
    print(f"Avg Context Recall: {summary['avg_context_recall']:.2%}")

    # Quality gate check
    QUALITY_THRESHOLD = 0.7
    passed = summary["avg_faithfulness"] >= QUALITY_THRESHOLD

    print("\n" + "=" * 60)
    if passed:
        print(f"✅ QUALITY GATE PASSED (threshold: {QUALITY_THRESHOLD:.0%})")
    else:
        print(f"❌ QUALITY GATE FAILED (threshold: {QUALITY_THRESHOLD:.0%})")
    print("=" * 60)

    # Save results
    if output_file:
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n📁 Results saved to: {output_file}")

    return summary


if __name__ == "__main__":
    # Run evaluation
    run_evaluation(role="c_level", output_file="evaluation_results.json")
