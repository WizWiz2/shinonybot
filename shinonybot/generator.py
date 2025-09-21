"""Character generator for the Shinobi tabletop RPG."""

from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .database import Database, Feat, InventoryItem, Rank, Skill

MELEE_SKILLS = {
    "Айкидо",
    "Будзюцу",
    "Чанбара",
    "Иайдо",
    "Карате",
    "Некоде",
}


@dataclass
class CharacterSheet:
    name: str
    gender: str
    name_meaning: str
    concept: Feat
    background: Feat
    feud: Optional[Feat]
    motivation: Feat
    clothing: Feat
    features: List[Feat]
    problems: List[Feat]
    augmentations: List[Feat]
    augmentation_roll: int
    skills: List[Skill]
    rank: Rank
    armor: Optional[InventoryItem]
    primary_weapon: Optional[InventoryItem]
    backup_weapon: Optional[InventoryItem]
    support_items: List[InventoryItem]
    lifestyle: Optional[InventoryItem]
    transport: Optional[InventoryItem]


class CharacterGenerator:
    """Generate randomized character sheets using ``DATABASE.md`` data."""

    def __init__(self, rng: Optional[random.Random] = None, base_path: str = "."):
        self.rng = rng or random.Random()
        self.db = Database.load(base_path)

    def generate(self) -> CharacterSheet:
        name_entry, gender = self._choose_name()
        concept = self.rng.choice(self.db.feats_by_type("Концепт"))
        background_entry, feud_entry = self._choose_background()
        motivation = self.rng.choice(self.db.feats_by_type("Мотивация"))
        clothing = self.rng.choice(self.db.feats_by_type("Одежда"))
        features = self._pick_unique(self.db.feats_by_type("Особые черты"), 2)
        problems = self._pick_unique(self.db.feats_by_type("Личностные проблемы"), 2)
        augmentation_roll, augmentations = self._roll_augmentations()
        skills = self._pick_unique(self.db.skills, 6)
        rank = self._starting_rank()
        armor = self._pick_one(self.db.inventory_by_type("Броня"))
        primary_weapon, backup_weapon = self._choose_weapons(skills)
        support_items = self._choose_support_items(skills)
        lifestyle = self._pick_one(self.db.inventory_by_type("Образ жизни"))
        transport = self._pick_one(self.db.inventory_by_type("Транспорт"))

        return CharacterSheet(
            name=name_entry.name,
            gender="Ж" if gender == "female" else "М",
            name_meaning=name_entry.description,
            concept=concept,
            background=background_entry,
            feud=feud_entry,
            motivation=motivation,
            clothing=clothing,
            features=features,
            problems=problems,
            augmentations=augmentations,
            augmentation_roll=augmentation_roll,
            skills=skills,
            rank=rank,
            armor=armor,
            primary_weapon=primary_weapon,
            backup_weapon=backup_weapon,
            support_items=support_items,
            lifestyle=lifestyle,
            transport=transport,
        )

    def format_sheet(self, sheet: CharacterSheet) -> str:
        width = 74
        border_top = "╔" + "═" * (width - 2) + "╗"
        border_mid = "╠" + "═" * (width - 2) + "╣"
        border_sep = "╟" + "─" * (width - 2) + "╢"
        border_bottom = "╚" + "═" * (width - 2) + "╝"

        def format_line(label: str, value: str) -> str:
            label = f"{label}:"
            return f"║ {label:<18} {value:<{width - 23}} ║"

        def wrap_block(title: str, text: str) -> str:
            wrapped = textwrap.fill(text, width=width - 4)
            return f"║ {title:<{width - 4}} ║\n" + "\n".join(
                f"║ {line:<{width - 4}} ║" for line in wrapped.splitlines()
            )

        def format_list(title: str, rows: Sequence[str]) -> str:
            lines = [f"• {row}" for row in rows]
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(
                    textwrap.wrap(line, width=width - 4) or [""]
                )
            body = "\n".join(f"║ {line:<{width - 4}} ║" for line in wrapped_lines)
            return f"║ {title:<{width - 4}} ║\n{body}"

        def describe_feat(feat: Optional[Feat]) -> str:
            if not feat:
                return "—"
            desc = feat.description.strip() if feat.description else ""
            if desc in {"-", "—"}:
                desc = ""
            if desc:
                name_clean = feat.name.strip()
                if not name_clean or name_clean.lower().startswith("таблица"):
                    return desc
                if desc.lower().startswith(name_clean.lower()):
                    return desc
                return f"{name_clean} — {desc}"
            return feat.name.strip()

        def describe_item(item: Optional[InventoryItem]) -> str:
            if not item:
                return "—"
            parts = [normalize(item.name)]
            if item.description:
                description = normalize(item.description)
                if description not in {"-", "—"}:
                    parts.append(description)
            if item.price is not None:
                parts.append(f"¥{item.price:,}".replace(",", " "))
            return " — ".join(parts)

        header = [
            border_top,
            "║ SHINOBI // CYBERPUNK DOSSIER".ljust(width - 1) + "║",
            border_mid,
            format_line("Имя", sheet.name),
            format_line("Пол", "Женский" if sheet.gender == "Ж" else "Мужской"),
            format_line("Значение", sheet.name_meaning or "—"),
            format_line("Концепт", sheet.concept.name),
            border_sep,
        ]

        def normalize(text: str) -> str:
            return " ".join(text.split()) if text else text

        background_text = normalize(describe_feat(sheet.background))
        if sheet.feud:
            feud_text = sheet.feud.description or sheet.feud.name
            background_text += f"; Вражда: {normalize(feud_text)}"
        motivation_text = normalize(describe_feat(sheet.motivation))
        appearance_lines = [
            normalize(describe_feat(sheet.clothing)),
            *[normalize(describe_feat(feat)) for feat in sheet.features],
        ]
        personality_lines = [normalize(describe_feat(feat)) for feat in sheet.problems]
        augmentation_lines = [
            f"Бросок d6 на аугментации: {sheet.augmentation_roll}",
            *[normalize(describe_feat(feat)) for feat in sheet.augmentations],
        ]
        skill_lines = [
            normalize(f"{skill.name} — {skill.description}") for skill in sheet.skills
        ]
        gear_lines = [
            f"Броня: {describe_item(sheet.armor)}",
            f"Основное оружие: {describe_item(sheet.primary_weapon)}",
            f"Запасное оружие: {describe_item(sheet.backup_weapon)}",
        ]
        if sheet.support_items:
            for idx, item in enumerate(sheet.support_items, start=1):
                gear_lines.append(f"Поддержка {idx}: {describe_item(item)}")
        lifestyle_line = describe_item(sheet.lifestyle)
        transport_line = describe_item(sheet.transport)
        rank_line = f"{sheet.rank.name} (бонус: {sheet.rank.benefit or '—'}, опыт: {sheet.rank.xp_needed or '0'})"

        blocks = [
            format_list("Биография", [background_text]),
            border_sep,
            format_list("Мотивация", [motivation_text]),
            border_sep,
            format_list("Внешность", appearance_lines),
            border_sep,
            format_list("Черты характера", personality_lines),
            border_sep,
            format_list("Аугментации", augmentation_lines),
            border_sep,
            format_list("Навыки", skill_lines),
            border_sep,
            format_list("Снаряжение", gear_lines),
            border_sep,
            format_list("Образ жизни", [lifestyle_line]),
            border_sep,
            format_list("Транспорт", [transport_line]),
            border_sep,
            format_list("Ранг", [rank_line]),
            border_bottom,
        ]

        return "\n".join(header + blocks)

    def _choose_name(self) -> Tuple[Feat, str]:
        male_names = self.db.feats_by_type("Мужские имена")
        female_names = self.db.feats_by_type("Женские имена")
        gender = self.rng.choice(["male", "female"])
        if gender == "male" and male_names:
            return self.rng.choice(male_names), gender
        if female_names:
            return self.rng.choice(female_names), "female"
        return self.rng.choice(male_names or female_names), gender

    def _choose_background(self) -> Tuple[Feat, Optional[Feat]]:
        all_history = self.db.feats_by_type("Предыстория")
        backgrounds = [
            feat
            for feat in all_history
            if feat.name.strip() != "Таблица вражды"
        ]
        feud_table = [
            feat for feat in all_history if feat.name.strip() == "Таблица вражды"
        ]
        background = self.rng.choice(backgrounds)
        feud: Optional[Feat] = None
        name_lower = background.name.lower()
        if "нужна" in name_lower and "не нужна" not in name_lower and feud_table:
            feud = self.rng.choice(feud_table)
        return background, feud

    def _roll_augmentations(self) -> Tuple[int, List[Feat]]:
        roll = self.rng.randint(1, 6)
        plan: Dict[str, int]
        if roll == 1:
            plan = {"А": 1}
        elif roll == 2:
            plan = {"B": 1, "D": 1}
        elif roll == 3:
            plan = {"C": 2}
        elif roll == 4:
            plan = {"C": 1, "D": 2}
        else:
            plan = {"D": 4}
        augmentations: List[Feat] = []
        for cls, count in plan.items():
            feats = self.db.feats_by_type(f"Аугментации класса {cls}")
            if not feats:
                continue
            augmentations.extend(self._pick_unique(feats, count))
        return roll, augmentations

    def _pick_unique(self, pool: Sequence, count: int) -> List:
        if not pool:
            return []
        if len(pool) <= count:
            return list(self.rng.sample(list(pool), len(pool)))
        return list(self.rng.sample(list(pool), count))

    def _pick_one(self, pool: Sequence) -> Optional:
        if not pool:
            return None
        return self.rng.choice(list(pool))

    def _choose_weapons(self, skills: Sequence[Skill]) -> Tuple[Optional[InventoryItem], Optional[InventoryItem]]:
        skill_names = {skill.name for skill in skills}
        heavy = "Тяжёлое оружие" in skill_names or "Тяжелое оружие" in skill_names
        light = "Лёгкое оружие" in skill_names or "Легкое оружие" in skill_names
        melee = bool(MELEE_SKILLS.intersection(skill_names))

        primary: Optional[InventoryItem] = None
        backup: Optional[InventoryItem] = None

        if heavy:
            primary = self._pick_one(self.db.inventory_by_type("Тяжелое оружие"))
        if not primary:
            primary = self._pick_one(self.db.inventory_by_type("Лёгкое оружие"))
        if melee:
            backup = self._pick_one(self.db.inventory_by_type("Лёгкое оружие"))
        if not backup:
            backup = self._pick_one(self.db.inventory_by_type("Холодное оружие"))
        return primary, backup

    def _choose_support_items(self, skills: Sequence[Skill]) -> List[InventoryItem]:
        skill_names = {skill.name for skill in skills}
        support: List[InventoryItem] = []
        categories: List[Tuple[str, str]] = []
        if "Киберпространство" in skill_names:
            categories.extend([
                ("Кибердека", "Основная кибердека"),
                ("Программа", "Программное обеспечение"),
            ])
        if "Контрбезопасность" in skill_names:
            categories.append(("Охранное оборудование", "Инструменты безопасности"))
        if "Технологии" in skill_names:
            categories.append(("Техника", "Технический набор"))
        if "Медицина" in skill_names:
            categories.append(("Медицинские товары и услуги", "Медицинские средства"))
        if "Взрывчатка" in skill_names:
            categories.append(("Взрывчатка", "Взрывчатка"))
        if not categories:
            categories.extend(
                [
                    ("Техника", "Техника"),
                    ("Компьютер", "Компьютер"),
                ]
            )
        seen_types = set()
        for type_name, _ in categories:
            if type_name in seen_types:
                continue
            seen_types.add(type_name)
            item = self._pick_one(self.db.inventory_by_type(type_name))
            if item:
                support.append(item)
        return support

    def _starting_rank(self) -> Rank:
        ranks = sorted(self.db.ranks, key=lambda r: r.id)
        return ranks[0] if ranks else Rank(0, "", "", "", "")


def generate_character_sheet(seed: Optional[int] = None, base_path: str = ".") -> str:
    rng = random.Random(seed)
    generator = CharacterGenerator(rng=rng, base_path=base_path)
    sheet = generator.generate()
    return generator.format_sheet(sheet)


if __name__ == "__main__":
    print(generate_character_sheet())
