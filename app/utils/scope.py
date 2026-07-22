"""Global filter scope.

A ``FactScope`` captures the sidebar filter selections. It is a frozen dataclass with
tuple fields so it is hashable — usable as a Streamlit cache key — and it can emit a
safe SQL ``WHERE`` clause (referencing the standard dim aliases d/p/r/c) used to build
a filtered in-memory warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactScope:
    years: tuple[int, ...] = ()
    markets: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    sub_categories: tuple[str, ...] = ()
    segments: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        return not any([self.years, self.markets, self.regions, self.countries,
                        self.categories, self.sub_categories, self.segments])

    @staticmethod
    def _quote(value: str) -> str:
        return "'" + str(value).replace("'", "''") + "'"

    def where(self) -> str:
        """SQL WHERE clause over aliases d(date)/p(product)/r(region)/c(customer)."""
        conds: list[str] = []
        if self.years:
            conds.append("d.year IN (" + ",".join(str(int(y)) for y in self.years) + ")")
        str_filters = [
            ("r.market", self.markets), ("r.region", self.regions), ("r.country", self.countries),
            ("p.category", self.categories), ("p.sub_category", self.sub_categories),
            ("c.segment", self.segments),
        ]
        for col, values in str_filters:
            if values:
                conds.append(f"{col} IN (" + ",".join(self._quote(v) for v in values) + ")")
        return ("WHERE " + " AND ".join(conds)) if conds else ""

    def summary(self) -> str:
        """Human-readable one-line description of the active filters."""
        parts = []
        for name, values in [("Year", self.years), ("Market", self.markets), ("Region", self.regions),
                             ("Country", self.countries), ("Category", self.categories),
                             ("Sub-category", self.sub_categories), ("Segment", self.segments)]:
            if values:
                parts.append(f"{name}: {', '.join(str(v) for v in values)}")
        return " | ".join(parts) if parts else "All data (no filters)"
