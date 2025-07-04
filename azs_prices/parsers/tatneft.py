from __future__ import annotations

from typing import List

import polars as pl
import requests
from tqdm import tqdm

from ..base import BaseParser


class TatneftParser(BaseParser):
    """Parser for Tatneft gas stations using open GIS API."""

    LIST_URL = "https://api.gs.tatneft.ru/api/v2/azs/"

    def fetch_data(self) -> pl.DataFrame:  # type: ignore[override]
        response = requests.get(self.LIST_URL, timeout=30)
        response.raise_for_status()
        stations = response.json()

        records: List[dict] = []
        for st in tqdm(stations, desc="Tatneft stations"):
            station_id = st.get("id")
            fuels = st.get("fuels", []) or st.get("fuels_info", [])
            for fuel in fuels:
                records.append(
                    {
                        "station_id": station_id,
                        "name": st.get("name") or st.get("title"),
                        "address": st.get("address"),
                        "fuel_type": fuel.get("name") or fuel.get("type"),
                        "price": fuel.get("price") or fuel.get("value"),
                    }
                )
        if records:
            df = pl.DataFrame(records)
            df = df.with_columns(pl.col("price").str.replace(",", ".").cast(pl.Float64))
            return df
        return pl.DataFrame([])