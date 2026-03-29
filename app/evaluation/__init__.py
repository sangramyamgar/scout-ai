"""Evaluation pipeline for RAG quality measurement."""

from app.evaluation.eval_pipeline import (
    run_evaluation,
    get_evaluation_dataset,
    GOLDEN_DATASET,
)

__all__ = ["run_evaluation", "get_evaluation_dataset", "GOLDEN_DATASET"]