"""Utilities for loading structured data from ``DATABASE.md``."""

from __future__ import annotations

import dataclasses
import html
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

DATABASE_FILE = "DATABASE.md"


@dataclass(frozen=True)
class Feat:
    id: int
    name: str
    description: str
    type: str
    roll_code: str


@dataclass(frozen=True)
class InventoryItem:
    id: int
    name: str
    description: str
    type: str
    price: Optional[int]


@dataclass(frozen=True)
class Skill:
    id: int
    name: str
    description: str
    roll_code: str


@dataclass(frozen=True)
class Rank:
    id: int
    name: str
    benefit: str
    mercenary: str
    xp_needed: str


@dataclass
class Database:
    feats: List[Feat]
    inventory: List[InventoryItem]
    skills: List[Skill]
    ranks: List[Rank]

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls, base_path: str = ".") -> "Database":
        path = os.path.join(base_path, DATABASE_FILE)
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        tables = _parse_markdown_tables(lines)
        feats = [
            Feat(
                id=int(row["ID"]),
                name=row["name"].strip(),
                description=_clean_cell(row.get("description", "")),
                type=row.get("type", "").strip(),
                roll_code=row.get("roll_code", "").strip(),
            )
            for row in tables.get("Черты и таблицы (shinobiSite_feat)", [])
        ]
        inventory = [
            InventoryItem(
                id=int(row["ID"]),
                name=row["name"].strip(),
                description=_clean_cell(row.get("description", "")),
                type=row.get("type", "").strip(),
                price=_parse_int(row.get("price")),
            )
            for row in tables.get("Снаряжение и услуги (shinobiSite_inventory)", [])
        ]
        skills = [
            Skill(
                id=int(row["ID"]),
                name=row["name"].strip(),
                description=_clean_cell(row.get("description", "")),
                roll_code=row.get("roll_code", "").strip(),
            )
            for row in tables.get("Навыки (shinobiSite_skill)", [])
        ]
        ranks = [
            Rank(
                id=int(row["ID"]),
                name=row["name"].strip(),
                benefit=row.get("benefit", "").strip(),
                mercenary=row.get("mercenary", "").strip(),
                xp_needed=row.get("xp_needed", "").strip(),
            )
            for row in tables.get("Ранги (shinobiSite_rang)", [])
        ]
        return cls(feats=feats, inventory=inventory, skills=skills, ranks=ranks)

    def feats_by_type(self, type_name: str) -> List[Feat]:
        return [feat for feat in self.feats if feat.type == type_name]

    def feats_by_type_prefix(self, prefix: str) -> List[Feat]:
        return [feat for feat in self.feats if feat.type.startswith(prefix)]

    def feats_with_name_prefix(self, type_name: str, prefix: str) -> List[Feat]:
        return [
            feat
            for feat in self.feats
            if feat.type == type_name and feat.name.startswith(prefix)
        ]

    def inventory_by_type(self, type_name: str) -> List[InventoryItem]:
        return [item for item in self.inventory if item.type == type_name]


def _parse_markdown_tables(lines: Iterable[str]) -> Dict[str, List[Dict[str, str]]]:
    tables: Dict[str, List[Dict[str, str]]] = {}
    current_section = None
    lines = list(lines)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_section = line[3:].strip()
            i += 1
            continue
        if line.startswith("|") and current_section:
            header_line = line
            if i + 1 >= len(lines):
                break
            divider = lines[i + 1]
            if "---" not in divider:
                i += 1
                continue
            headers = [cell.strip() for cell in header_line.strip().strip("|").split("|")]
            rows: List[Dict[str, str]] = []
            i += 2
            while i < len(lines):
                row_line = lines[i]
                if not row_line.startswith("|"):
                    break
                cells = [
                    cell.strip()
                    for cell in row_line.strip().strip("|").split("|")
                ]
                if len(cells) != len(headers):
                    i += 1
                    continue
                row = {header: cell for header, cell in zip(headers, cells)}
                rows.append(row)
                i += 1
            existing = tables.setdefault(current_section, [])
            existing.extend(rows)
            continue
        i += 1
    return tables


def _clean_cell(value: str) -> str:
    value = value.replace("<br>", "\n").replace("<br />", "\n")
    value = html.unescape(value)
    return value.strip()


def _parse_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
