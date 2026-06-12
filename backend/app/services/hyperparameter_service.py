"""Hyperparameter search service."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.hyperparameter import HyperparameterSearch, HyperparameterTrial


def create_search(db: Session, config: dict) -> HyperparameterSearch:
    """Create a hyperparameter search job.

    Args:
        db: Database session
        config: Search configuration dict

    Returns:
        HyperparameterSearch: Created search job
    """
    search = HyperparameterSearch(
        id=str(uuid.uuid4()),
        name=config["name"],
        model_version=config["model_version"],
        dataset_id=config["dataset_id"],
        user_id=config["user_id"],
        status="pending",
        method=config.get("method", "bayesian"),
        search_space=config.get("search_space"),
        search_config=config.get("search_config"),
        base_config=config.get("base_config"),
        n_trials=config.get("n_trials", 20),
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


def get_search(db: Session, search_id: str) -> Optional[HyperparameterSearch]:
    """Get a hyperparameter search job by ID.

    Args:
        db: Database session
        search_id: Search job ID

    Returns:
        HyperparameterSearch or None
    """
    return db.query(HyperparameterSearch).filter(HyperparameterSearch.id == search_id).first()


def get_trials(db: Session, search_id: str) -> List[HyperparameterTrial]:
    """Get all trials for a search job.

    Args:
        db: Database session
        search_id: Search job ID

    Returns:
        List of HyperparameterTrial
    """
    return (
        db.query(HyperparameterTrial)
        .filter(HyperparameterTrial.search_id == search_id)
        .order_by(HyperparameterTrial.trial_number)
        .all()
    )


def update_search_status(
    db: Session,
    search_id: str,
    status: str,
    best_metric: Optional[float] = None,
    best_params: Optional[dict] = None,
    completed_trials: Optional[int] = None,
) -> Optional[HyperparameterSearch]:
    """Update search job status.

    Args:
        db: Database session
        search_id: Search job ID
        status: New status
        best_metric: Best metric value found so far
        best_params: Best params found so far
        completed_trials: Number of completed trials

    Returns:
        HyperparameterSearch or None
    """
    search = get_search(db, search_id)
    if not search:
        return None

    search.status = status
    if best_metric is not None:
        search.best_metric = best_metric
    if best_params is not None:
        search.best_params = best_params
    if completed_trials is not None:
        search.completed_trials = completed_trials

    db.commit()
    db.refresh(search)
    return search


def create_trial(
    db: Session,
    search_id: str,
    trial_number: int,
    params: dict,
) -> HyperparameterTrial:
    """Create a new trial record.

    Args:
        db: Database session
        search_id: Search job ID
        trial_number: Trial number
        params: Trial hyperparameters

    Returns:
        HyperparameterTrial
    """
    trial = HyperparameterTrial(
        id=str(uuid.uuid4()),
        search_id=search_id,
        trial_number=trial_number,
        status="pending",
        params=params,
        started_at=datetime.now(timezone.utc),
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


def update_trial_result(
    db: Session,
    trial_id: str,
    status: str,
    metric_value: Optional[float] = None,
    metrics: Optional[dict] = None,
    error: Optional[str] = None,
) -> Optional[HyperparameterTrial]:
    """Update a trial with results.

    Args:
        db: Database session
        trial_id: Trial ID
        status: New status
        metric_value: The optimized metric value
        metrics: Full metrics dict
        error: Error message if failed

    Returns:
        HyperparameterTrial or None
    """
    trial = db.query(HyperparameterTrial).filter(HyperparameterTrial.id == trial_id).first()
    if not trial:
        return None

    trial.status = status
    if metric_value is not None:
        trial.metric_value = metric_value
    if metrics is not None:
        trial.metrics = metrics
    if error is not None:
        trial.error = error

    trial.completed_at = datetime.now(timezone.utc)
    if trial.started_at:
        trial.duration = (trial.completed_at - trial.started_at).total_seconds()

    db.commit()
    db.refresh(trial)
    return trial
