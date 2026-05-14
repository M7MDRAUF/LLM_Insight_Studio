"""Classification metrics (pure Python, no sklearn dependency)."""

from __future__ import annotations

from collections import Counter


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def classification_metrics(
    y_true: list[str], y_pred: list[str]
) -> dict[str, float | dict[str, dict[str, int]]]:
    """Compute accuracy, macro precision/recall/F1, and confusion matrix.

    Returns a dict serializable to JSON.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be the same length")
    if not y_true:
        return {
            "accuracy": 0.0,
            "precision_macro": 0.0,
            "recall_macro": 0.0,
            "f1_macro": 0.0,
            "support": 0,
            "confusion": {},
        }

    labels = sorted(set(y_true) | set(y_pred))
    confusion: dict[str, dict[str, int]] = {t: dict.fromkeys(labels, 0) for t in labels}
    for t, p in zip(y_true, y_pred, strict=True):
        confusion[t][p] += 1

    correct = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p)
    accuracy = correct / len(y_true)

    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    true_counts = Counter(y_true)
    pred_counts = Counter(y_pred)
    for label in labels:
        tp = confusion[label][label]
        fp = pred_counts[label] - tp
        fn = true_counts[label] - tp
        prec = _safe_div(tp, tp + fp)
        rec = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * prec * rec, prec + rec)
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    n = max(1, len(labels))
    return {
        "accuracy": round(accuracy, 6),
        "precision_macro": round(sum(precisions) / n, 6),
        "recall_macro": round(sum(recalls) / n, 6),
        "f1_macro": round(sum(f1s) / n, 6),
        "support": len(y_true),
        "confusion": confusion,
    }
