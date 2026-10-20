"""Stage 4 model-engineering helpers for shared references and evaluation."""

from .contract import CONTRACT_PATH, ModelTrainingConfig, ModelTrainingError, resolve_root
from .pipeline import ModelTrainingResult, build_model_training, run_summary

__all__ = [
    "CONTRACT_PATH",
    "ModelTrainingConfig",
    "ModelTrainingError",
    "ModelTrainingResult",
    "build_model_training",
    "resolve_root",
    "run_summary",
]
