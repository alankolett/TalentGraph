"""Ingestion loader: reads raw candidate and job data from various sources."""
from pathlib import Path

import pandas as pd


def load_candidates(path: str | Path) -> pd.DataFrame:
    """Load raw candidate data from a parquet or CSV file."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def load_jobs(path: str | Path) -> pd.DataFrame:
    """Load raw job data from a parquet or CSV file."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)
