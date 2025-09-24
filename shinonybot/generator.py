"""Character generator for the Shinobi tabletop RPG."""

from __future__ import annotations

import html
import random
import textwrap
from dataclasses import dataclass
from string import Template
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


HTML_SECTIONS: Tuple[Tuple[str, str], ...] = (
    ("biography", "Биография"),
    ("motivation", "Мотивация"),
    ("appearance", "Внешность"),
    ("personality", "Черты характера"),
    ("augmentations", "Аугментации"),
    ("skills", "Навыки"),
    ("gear", "Снаряжение"),
    ("lifestyle", "Образ жизни"),
    ("transport", "Транспорт"),
    ("rank", "Ранг"),
)


HTML_TEMPLATE = Template(
    textwrap.dedent(
        """
        <!DOCTYPE html>
        <html lang="ru">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Shinobi Dossier</title>
            <style>
              :root {
                color-scheme: dark;
                --bg: #04020c;
                --panel: rgba(25, 17, 48, 0.85);
                --accent: #7df9ff;
                --accent-2: #ff00ff;
                --text: #e4f1ff;
                --muted: #8ca1c1;
                --shadow: 0 0 30px rgba(125, 249, 255, 0.25);
              }
              * {
                box-sizing: border-box;
              }
              body {
                margin: 0;
                padding: 24px 12px 48px;
                font-family: "Orbitron", "Russo One", "Segoe UI", sans-serif;
                background: radial-gradient(circle at top, #120a28, #03010a 55%, #010006);
                color: var(--text);
              }
              .dossier {
                max-width: 720px;
                margin: 0 auto;
                background: var(--panel);
                border: 2px solid var(--accent);
                border-radius: 18px;
                padding: 24px 20px;
                box-shadow: var(--shadow);
                backdrop-filter: blur(6px);
              }
              header {
                text-align: center;
                margin-bottom: 24px;
              }
              header h1 {
                font-size: clamp(1.6rem, 3vw, 2.6rem);
                letter-spacing: 0.28em;
                margin: 0 0 6px;
                text-transform: uppercase;
                color: var(--accent);
                text-shadow: 0 0 16px rgba(125, 249, 255, 0.6);
              }
              header p {
                margin: 0;
                font-size: 0.95rem;
                color: var(--muted);
                letter-spacing: 0.16em;
                text-transform: uppercase;
              }
              .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 12px;
                margin-bottom: 24px;
              }
              .info-row {
                background: rgba(12, 9, 26, 0.9);
                border: 1px solid rgba(125, 249, 255, 0.35);
                border-radius: 12px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 6px;
                box-shadow: 0 0 12px rgba(255, 0, 255, 0.18);
              }
              .label {
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.22em;
                color: var(--muted);
              }
              .value {
                font-size: 1.05rem;
                letter-spacing: 0.02em;
              }
              .block {
                margin-bottom: 22px;
                padding: 16px 14px;
                border: 1px solid rgba(255, 0, 255, 0.25);
                border-radius: 12px;
                background: rgba(10, 6, 24, 0.9);
                position: relative;
                overflow: hidden;
              }
              .block::before {
                content: "";
                position: absolute;
                inset: 0;
                border: 1px solid rgba(125, 249, 255, 0.15);
                border-radius: 12px;
                pointer-events: none;
              }
              .block h2 {
                margin: 0 0 12px;
                font-size: 1rem;
                letter-spacing: 0.32em;
                text-transform: uppercase;
                color: var(--accent-2);
              }
              .block ul {
                list-style: none;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                gap: 10px;
              }
              .block li {
                display: flex;
                gap: 10px;
                align-items: flex-start;
                font-size: 0.95rem;
                line-height: 1.45;
              }
              .bullet {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-top: 6px;
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
                box-shadow: 0 0 10px rgba(125, 249, 255, 0.9);
                flex-shrink: 0;
              }
              @media (prefers-reduced-motion: reduce) {
                * {
                  transition: none !important;
                }
              }
            </style>
          </head>
          <body>
            <main class="dossier">
              <header>
                <h1>SHINOBI DOSSIER</h1>
                <p>Cyberpunk операционный файл</p>
              </header>
              <section class="info-grid">$info_cards</section>
              $sections
            </main>
          </body>
        </html>
        """
    )
)


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

    def _build_sections(self, sheet: CharacterSheet) -> Dict[str, Sequence[str]]:
        """Prepare formatted text snippets for different sheet sections."""

        def normalize(text: str) -> str:
            return " ".join(text.split()) if text else text

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
        rank_line = (
            f"{sheet.rank.name} (бонус: {sheet.rank.benefit or '—'}, "
            f"опыт: {sheet.rank.xp_needed or '0'})"
        )

        return {
            "biography": [background_text],
            "motivation": [motivation_text],
            "appearance": appearance_lines,
            "personality": personality_lines,
            "augmentations": augmentation_lines,
            "skills": skill_lines,
            "gear": gear_lines,
            "lifestyle": [lifestyle_line],
            "transport": [transport_line],
            "rank": [rank_line],
        }

    def format_sheet(self, sheet: CharacterSheet) -> str:
        width = 60
        border_top = "╔" + "═" * (width - 2) + "╗"
        border_mid = "╠" + "═" * (width - 2) + "╣"
        border_sep = "╟" + "─" * (width - 2) + "╢"
        border_bottom = "╚" + "═" * (width - 2) + "╝"

        def format_line(label: str, value: str) -> str:
            label = f"{label}:"
            return f"║ {label:<18} {value:<{width - 23}} ║"

        def format_list(title: str, rows: Sequence[str]) -> str:
            lines = [f"• {row}" for row in rows]
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(
                    textwrap.wrap(line, width=width - 4) or [""]
                )
            body = "\n".join(f"║ {line:<{width - 4}} ║" for line in wrapped_lines)
            return f"║ {title:<{width - 4}} ║\n{body}"

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

        sections = self._build_sections(sheet)

        blocks = [
            format_list("Биография", sections["biography"]),
            border_sep,
            format_list("Мотивация", sections["motivation"]),
            border_sep,
            format_list("Внешность", sections["appearance"]),
            border_sep,
            format_list("Черты характера", sections["personality"]),
            border_sep,
            format_list("Аугментации", sections["augmentations"]),
            border_sep,
            format_list("Навыки", sections["skills"]),
            border_sep,
            format_list("Снаряжение", sections["gear"]),
            border_sep,
            format_list("Образ жизни", sections["lifestyle"]),
            border_sep,
            format_list("Транспорт", sections["transport"]),
            border_sep,
            format_list("Ранг", sections["rank"]),
            border_bottom,
        ]

        return "\n".join(header + blocks)

    def format_sheet_html(self, sheet: CharacterSheet) -> str:
        """Return a cyberpunk-styled responsive HTML representation."""

        sections = self._build_sections(sheet)
        info_cards = "".join(
            self._render_html_info_row(label, value)
            for label, value in self._html_info_rows(sheet)
        )
        section_markup = "".join(
            self._render_html_section(title, sections[key])
            for key, title in HTML_SECTIONS
        )
        return HTML_TEMPLATE.substitute(info_cards=info_cards, sections=section_markup)

    def _html_info_rows(self, sheet: CharacterSheet) -> Sequence[Tuple[str, str]]:
        gender_label = "Женский" if sheet.gender == "Ж" else "Мужской"
        return [
            ("Имя", sheet.name or "—"),
            ("Пол", gender_label),
            ("Значение имени", sheet.name_meaning or "—"),
            ("Концепт", sheet.concept.name or "—"),
        ]

    @staticmethod
    def _render_html_info_row(label: str, value: str) -> str:
        safe_label = html.escape(label)
        safe_value = html.escape(value or "—")
        return (
            "<div class=\"info-row\">"
            f"<span class=\"label\">{safe_label}</span>"
            f"<span class=\"value\">{safe_value}</span>"
            "</div>"
        )

    @staticmethod
    def _render_html_section(title: str, items: Sequence[str]) -> str:
        normalized_items = [item or "—" for item in items] or ["—"]
        list_items = "".join(
            "<li><span class=\"bullet\"></span><span>"
            f"{html.escape(item)}</span></li>"
            for item in normalized_items
        )
        return (
            "<section class=\"block\">"
            f"<h2>{html.escape(title)}</h2>"
            f"<ul>{list_items}</ul>"
            "</section>"
        )

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
