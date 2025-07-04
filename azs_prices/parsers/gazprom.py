from __future__ import annotations

from typing import List

import polars as pl
import requests
from tqdm import tqdm

from ..base import BaseParser


class GazpromParser(BaseParser):
    """Parser for Gazpromneft network using https://gpnbonus.ru/api/stations endpoints."""

    LIST_URL = "https://gpnbonus.ru/api/stations/list"
    DETAIL_URL = "https://gpnbonus.ru/api/stations/{station_id}"

    def fetch_data(self) -> pl.DataFrame:  # type: ignore[override]
        # Step 1: fetch list of station ids
        resp = requests.get(self.LIST_URL, timeout=30)
        resp.raise_for_status()
        stations = resp.json()
        station_ids: List[int] = [s["id"] for s in stations]

        records: List[dict] = []
        for sid in tqdm(station_ids, desc="Gazprom stations"):
            r = requests.get(self.DETAIL_URL.format(station_id=sid), timeout=15)
            if r.status_code != 200:
                continue
            data = r.json()
            fuels = data.get("fuels", [])
            for fuel in fuels:
                records.append(
                    {
                        "station_id": sid,
                        "name": data.get("title"),
                        "address": data.get("address"),
                        "fuel_type": fuel.get("title"),
                        "price": fuel.get("price"),
                    }
                )
        if records:
            df = pl.DataFrame(records)
            df = df.with_columns(pl.col("price").cast(pl.Float64))
            return df
        return pl.DataFrame([])