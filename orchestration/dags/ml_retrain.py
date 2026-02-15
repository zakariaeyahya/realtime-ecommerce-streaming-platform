"""Airflow DAG: ML model retraining pipeline.

Retrains fraud detection and inventory forecasting models daily,
then evaluates model accuracy.
"""

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)

SCRIPTS_DIR = "/opt/airflow/scripts"

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=1),
}

with DAG(
    dag_id="ml_retrain",
    default_args=default_args,
    description="Re-entrainement quotidien des modeles ML (fraud + inventory)",
    schedule_interval="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ml", "training", "sprint8"],
) as dag:

    train_fraud_model = BashOperator(
        task_id="train_fraud_model",
        bash_command=f"python {SCRIPTS_DIR}/train_fraud_model.py",
    )

    train_inventory_model = BashOperator(
        task_id="train_inventory_model",
        bash_command=f"python {SCRIPTS_DIR}/train_inventory_model.py",
    )

    evaluate_models = BashOperator(
        task_id="evaluate_models",
        bash_command=f"python {SCRIPTS_DIR}/evaluate_inventory_models.py",
    )

    notify_success = BashOperator(
        task_id="notify_success",
        bash_command='echo "ML retraining completed successfully at $(date)"',
    )

    [train_fraud_model, train_inventory_model] >> evaluate_models >> notify_success
