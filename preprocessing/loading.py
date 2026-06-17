from pathlib import Path
from typing import Literal

import pandas as pd

DatasetKind = Literal["candidates", "jobs"]


class DataLoader:
    """Load raw challenge files from CSV, JSON, or JSONL."""

    def load_raw_dataset(self, path: str | Path) -> pd.DataFrame:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)

        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix == ".json":
            return pd.read_json(path)
        if suffix in {".jsonl", ".ndjson"}:
            return pd.read_json(path, lines=True)

        raise ValueError(f"Unsupported dataset file type: {path.suffix}")

    def find_dataset_file(self, raw_dir: str | Path, kind: DatasetKind) -> Path:
        raw_dir = Path(raw_dir)
        candidates = [
            raw_dir / f"{kind}.csv",
            raw_dir / f"{kind}.json",
            raw_dir / f"{kind}.jsonl",
            raw_dir / f"{kind}.ndjson",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        expected = ", ".join(path.name for path in candidates)
        raise FileNotFoundError(f"Expected one of {expected} in {raw_dir}")
