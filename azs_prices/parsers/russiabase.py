from __future__ import annotations

import json
import time
from typing import List, Tuple, Type

import polars as pl
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..base import BaseParser


class RussiabaseParser(BaseParser):
    """Parser for https://russiabase.ru/prices endpoint.

    Usage: subclass with brand_id or create via classmethod with_brand.
    """

    BASE_URL = "https://russiabase.ru/prices"

    def __init__(self, brand_id: int, max_pages: int | None = None, delay: float = 1.0):
        self.brand_id = brand_id
        self.max_pages = max_pages
        self.delay = delay

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    @classmethod
    def with_brand(cls: Type["RussiabaseParser"], brand_id: int) -> Type["RussiabaseParser"]:
        """Factory returning a subclass with pre-configured brand id."""

        class _ConcreteRussiabaseParser(cls):
            _brand_id = brand_id

            def __init__(self, max_pages: int | None = None, delay: float = 1.0):
                super().__init__(brand_id=self._brand_id, max_pages=max_pages, delay=delay)

            def __repr__(self):
                return f"<RussiabaseParser brand={self._brand_id}>"

        _ConcreteRussiabaseParser.__name__ = f"RussiabaseParser_{brand_id}"
        return _ConcreteRussiabaseParser

    # ------------------------------------------------------------------
    # Core implementation
    # ------------------------------------------------------------------
    def _iter_pages(self) -> List[str]:
        """Build list of page URLs to iterate over.

        If max_pages is None, we iterate until a page returns no matching script tags.
        """
        urls: List[str] = []
        page = 1
        empty_streak = 0
        while True:
            if page == 1:
                url = f"{self.BASE_URL}?brand={self.brand_id}"
            else:
                url = f"{self.BASE_URL}?brand={self.brand_id}&page={page}"
            urls.append(url)
            if self.max_pages and page >= self.max_pages:
                break
            page += 1
            if self.max_pages is None and page > 1000:  # safety cap
                break
        return urls

    def _extract_json_strings(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        divs = soup.find_all("script")
        json_strings = [div.text.strip() for div in divs if "@context" in div.text]
        return json_strings

    def _expand_df(self, df: pl.DataFrame) -> pl.DataFrame:
        expanded_rows: List[dict] = []
        for row in df.iter_rows(named=True):
            description = row.get("description")
            if description is None:
                continue
            items = [item.strip() for item in description.split(";") if item.strip()]
            for item in items:
                parts: Tuple[str, str] | List[str] = item.split(" - ")
                description_part1 = parts[0].strip() if len(parts) > 0 else ""
                description_part2 = parts[1].strip() if len(parts) > 1 else ""
                expanded_rows.append(
                    {
                        "legalName": row.get("legalName"),
                        "address": row.get("address"),
                        "fuel_type": description_part1,
                        "price": description_part2,
                    }
                )
        if not expanded_rows:
            return pl.DataFrame([])
        expanded_df = pl.DataFrame(expanded_rows)
        with_price = expanded_df.with_columns(
            pl.col("price").str.replace(",", ".").cast(pl.Float64)  # convert commas
        )
        return with_price

    def fetch_data(self) -> pl.DataFrame:  # type: ignore[override]
        urls = self._iter_pages()
        frames: List[pl.DataFrame] = []
        for url in tqdm(urls, desc=f"Fetching brand {self.brand_id}"):
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                break
            json_strings = self._extract_json_strings(response.text)
            if not json_strings:
                # stop if no data found
                if self.max_pages is None:
                    break
                else:
                    continue
            data = []
            for js in json_strings:
                try:
                    data_dict = json.loads(js)
                    data.append(data_dict)
                except json.JSONDecodeError:
                    continue
            if not data:
                continue
            df = pl.DataFrame(data)
            expanded_df = self._expand_df(df)
            if expanded_df.height == 0:
                continue
            frames.append(expanded_df)
            time.sleep(self.delay)
        if frames:
            return pl.concat(frames, how="vertical")
        return pl.DataFrame([])