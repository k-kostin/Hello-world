from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class BaseParser(ABC):
    """Abstract base class for all gas station price parsers."""

    @abstractmethod
    def fetch_data(self) -> pl.DataFrame:
        """Retrieve raw data and return Polars DataFrame."""

    def save(self, df: pl.DataFrame, filename: str | Path) -> Path:
        """Save DataFrame to CSV inside data directory and return path."""
        out_path = DATA_DIR / filename
        df.write_csv(out_path)
        return out_path

    def run(self, **kwargs: Dict[str, Any]) -> Path:
        """High-level method: fetch data, optionally postprocess, save.

        Returns path to saved file.
        """
        df = self.fetch_data(**kwargs)  # type: ignore[arg-type]
        outfile = self.save(df, f"{self.__class__.__name__.lower()}.csv")
        return outfile