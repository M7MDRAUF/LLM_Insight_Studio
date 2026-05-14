"""Centralised model + metric defaults shared across services and routers."""

from __future__ import annotations

from apps.api.schemas.datasets import TaskLane

DEFAULT_MODELS: dict[TaskLane, str] = {
    TaskLane.CLASSIFICATION: "distilbert-base-uncased-finetuned-sst-2-english",
    TaskLane.SUMMARIZATION: "google/flan-t5-base",
    TaskLane.QA: "deepset/roberta-base-squad2",
    TaskLane.INSTRUCT: "Qwen/Qwen2.5-7B-Instruct",
}

# Per-lane "primary" score used to rank winners in the compare endpoint.
BEST_METRIC_BY_LANE: dict[TaskLane, str] = {
    TaskLane.CLASSIFICATION: "f1_macro",
    TaskLane.SUMMARIZATION: "rougeL",
    TaskLane.QA: "f1",
    TaskLane.INSTRUCT: "support",
}


def default_model_for(lane: TaskLane) -> str:
    return DEFAULT_MODELS[lane]
