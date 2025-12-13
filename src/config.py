"""Project configuration for the EDA pipeline.

Edit paths and column-lists here instead of inside the notebook.
"""

from dataclasses import dataclass
from typing import List

# ===== Paths (edit to match your workspace) =====
BEHAVIOURAL_PATH_RAW = "/home/jovyan/work/data/BEHAVIOURAL"
CLIENTS_PATH_RAW     = "/home/jovyan/work/data/CLIENTS"

BEHAVIOURAL_PATH_CLEAN = "/home/jovyan/work/data/BEHAVIOURAL_CLEAN"
CLIENTS_PATH_CLEAN     = "/home/jovyan/work/data/CLIENTS_CLEAN"

BEHAVIOURAL_CSV_CLEAN = "/home/jovyan/work/data/BEHAVIOURAL_CLEAN.csv"
CLIENTS_CSV_CLEAN     = "/home/jovyan/work/data/CLIENTS_CLEAN.csv"

SPARK_APP_NAME = "EDA_PIPELINE_FORMAL"

# ===== Cleaning rules =====
# Behavioural
BEH_DROP_COLS: List[str] = ["CURRENCY"]

# Clients
# NOTE: in your original notebook this list was truncated with "...".
# Add/remove columns to match your real schema.
CLI_DROPNA_SUBSET: List[str] = [
    "NUM_PREVIOUS_LOAN_APP",
    "LOAN_ANNUITY_PAYMENT_MAX",
    "LOAN_ANNUITY_PAYMENT_MIN",
    "LOAN_ANNUITY_PAYMENT_SUM",
    "LOAN_APPLICATION_AMOUNT_MAX",
    "LOAN_APPLICATION_AMOUNT_MIN",
    "LOAN_APPLICATION_AMOUNT_SUM",
    "LOAN_CREDIT_GRANTED_MAX",
    "LOAN_CREDIT_GRANTED_MIN",
    "LOAN_CREDIT_GRANTED_SUM",
    "LOAN_VARIABLE_RATE_MAX",
    "LOAN_VARIABLE_RATE_MIN",
    "NUM_STATUS_ANNULLED",
    "NUM_STATUS_AUTHORIZED",
    "NUM_STATUS_DENIED",
]

CLI_DROP_COLS: List[str] = ["CAR_AGE", "REACTIVE_SCORING", "CURRENCY"]


@dataclass(frozen=True)
class Paths:
    beh_raw: str = BEHAVIOURAL_PATH_RAW
    cli_raw: str = CLIENTS_PATH_RAW
    beh_clean: str = BEHAVIOURAL_PATH_CLEAN
    cli_clean: str = CLIENTS_PATH_CLEAN
    beh_csv: str = BEHAVIOURAL_CSV_CLEAN
    cli_csv: str = CLIENTS_CSV_CLEAN
