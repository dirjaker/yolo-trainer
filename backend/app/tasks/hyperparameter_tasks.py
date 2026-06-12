"""Hyperparameter search Celery tasks using Optuna for Bayesian optimization."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from celery import shared_task

logger = logging.getLogger(__name__)


def _suggest_param(trial, name: str, spec: dict):
    """Use optuna trial to suggest a parameter value based on the search space spec."""
    ptype = spec.get("type", "float")
    values = spec.get("values")
    low = spec.get("low")
    high = spec.get("high")
    log = spec.get("log", False)
    step = spec.get("step")

    if values is not None:
        return trial.suggest_categorical(name, values)

    if ptype == "int":
        if low is not None and high is not None:
            return trial.suggest_int(name, int(low), int(high), log=log, step=int(step) if step else None)
        return trial.suggest_categorical(name, [16, 32, 64])

    # float
    if low is not None and high is not None:
        return trial.suggest_float(name, float(low), float(high), log=log, step=step)

    return trial.suggest_float(name, 1e-5, 1e-1, log=True)


def _run_single_trial(
    search_config: dict,
    model_version: str,
    dataset_config_path: str,
    params: dict,
    epochs: int,
) -> Dict[str, Any]:
    """Run a single training trial with the given hyperparameters.

    Returns:
        dict with training metrics
    """
    from worker.trainer import get_trainer
    from worker.trainer.base import TrainConfig

    config = TrainConfig(
        model_version=model_version,
        dataset_config=dataset_config_path,
        epochs=epochs,
        batch_size=int(params.get("batch_size", 16)),
        img_size=int(params.get("img_size", 640)),
        learning_rate=float(params.get("learning_rate", 0.01)),
        device=params.get("device", "0"),
        workers=int(params.get("workers", 8)),
        patience=int(params.get("patience", 50)),
        output_dir="runs/hyperparam",
        project_name=f"trial_{int(time.time())}",
    )

    trainer = get_trainer(model_version)
    result = trainer.train(config)

    if result.success:
        return result.metrics
    else:
        raise RuntimeError(result.error or "Training failed")


@shared_task(bind=True, name="tasks.run_hyperparameter_search", max_retries=1)
def run_hyperparameter_search_task(self, search_id: str, config: dict) -> dict:
    """Execute hyperparameter search using Optuna.

    Supports:
    - Bayesian Optimization (TPE sampler)
    - Random Search (RandomSampler)
    - Grid Search (brute-force with GridSampler)

    Args:
        search_id: Search job ID
        config: Search configuration

    Returns:
        dict: Search results
    """
    import optuna

    from app.core.database import SessionLocal
    from app.services.hyperparameter_service import (
        update_search_status,
        create_trial,
        update_trial_result,
        get_search,
    )

    db = SessionLocal()
    try:
        update_search_status(db, search_id, "running")
        logger.info(f"Hyperparameter search {search_id} started")

        search_space = config["search_space"]
        search_config = config["search_config"]
        model_version = config["model_version"]
        base_config = config.get("base_config", {})

        method = search_config.get("method", "bayesian")
        n_trials = search_config.get("n_trials", 20)
        metric_name = search_config.get("metric", "metrics/mAP50-95(B)")
        direction = search_config.get("direction", "maximize")
        epochs_per_trial = search_config.get("epochs_per_trial", 50)
        timeout = search_config.get("timeout")
        seed = search_config.get("seed")

        # Create Optuna study
        if method == "grid":
            # Grid search: build search space for GridSampler
            grid_space = {}
            for name, spec in search_space.items():
                if spec.get("values"):
                    grid_space[name] = spec["values"]
                elif spec.get("low") is not None and spec.get("high") is not None:
                    step = spec.get("step", 1)
                    low, high = spec["low"], spec["high"]
                    if spec.get("type") == "int":
                        grid_space[name] = list(range(int(low), int(high) + 1, int(step)))
                    else:
                        grid_space[name] = []
                        v = low
                        while v <= high:
                            grid_space[name].append(round(v, 8))
                            v += step
            sampler = optuna.samplers.GridSampler(grid_space, seed=seed)
        elif method == "random":
            sampler = optuna.samplers.RandomSampler(seed=seed)
        else:
            # Bayesian: TPE (Tree-structured Parzen Estimator)
            sampler = optuna.samplers.TPESampler(seed=seed)

        study = optuna.create_study(
            direction=direction,
            sampler=sampler,
            study_name=f"search_{search_id}",
        )

        dataset_config_path = base_config.get("dataset_config", f"datasets/{config['dataset_id']}/data.yaml")
        best_metric = None
        best_params = None
        completed = 0

        def objective(trial):
            nonlocal best_metric, best_params, completed

            # Suggest parameters
            params = {}
            for name, spec in search_space.items():
                params[name] = _suggest_param(trial, name, spec)

            # Create trial record in DB
            db_trial = create_trial(db, search_id, trial.number, params)
            update_trial_result(db, str(db_trial.id), "running")

            try:
                metrics = _run_single_trial(
                    search_config=search_config,
                    model_version=model_version,
                    dataset_config_path=dataset_config_path,
                    params=params,
                    epochs=epochs_per_trial,
                )

                metric_value = float(metrics.get(metric_name, 0.0))
                update_trial_result(
                    db, str(db_trial.id), "completed",
                    metric_value=metric_value,
                    metrics=metrics,
                )

                # Update best
                completed += 1
                if best_metric is None or (
                    (direction == "maximize" and metric_value > best_metric) or
                    (direction == "minimize" and metric_value < best_metric)
                ):
                    best_metric = metric_value
                    best_params = params

                # Update search status periodically
                update_search_status(
                    db, search_id, "running",
                    best_metric=best_metric,
                    best_params=best_params,
                    completed_trials=completed,
                )

                return metric_value

            except Exception as e:
                logger.error(f"Trial {trial.number} failed: {e}")
                update_trial_result(
                    db, str(db_trial.id), "failed",
                    error=str(e),
                )
                raise

        # Check if search was cancelled
        search = get_search(db, search_id)
        if search and search.status == "cancelled":
            logger.info(f"Search {search_id} was cancelled before start")
            return {"status": "cancelled"}

        study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            catch=(RuntimeError,),
        )

        update_search_status(
            db, search_id, "completed",
            best_metric=best_metric,
            best_params=best_params,
            completed_trials=completed,
        )

        logger.info(
            f"Search {search_id} completed. Best metric: {best_metric}, "
            f"Best params: {best_params}"
        )

        return {
            "status": "completed",
            "best_metric": best_metric,
            "best_params": best_params,
            "completed_trials": completed,
        }

    except Exception as exc:
        logger.error(f"Search {search_id} failed: {exc}")
        update_search_status(db, search_id, "failed")
        raise
    finally:
        db.close()
