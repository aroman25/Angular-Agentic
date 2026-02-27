from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Role = Literal["planner", "developer", "validator"]


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    path: Path
    tags: tuple[str, ...] = ()
    mandatory_for: tuple[Role, ...] = ()


@dataclass(frozen=True)
class ContextCard:
    card_id: str
    source_id: str
    heading: str
    content: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    role: Role
    context: str
    selected_card_ids: tuple[str, ...]
    dropped_card_ids: tuple[str, ...]
    truncated: bool


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "your",
    "must",
    "should",
    "when",
    "what",
    "where",
    "have",
    "has",
    "into",
    "will",
    "then",
    "than",
    "they",
    "them",
    "their",
    "about",
    "only",
    "using",
    "use",
    "used",
    "also",
    "are",
    "was",
    "were",
    "can",
    "could",
    "would",
    "not",
    "all",
}


def infer_story_signals(user_story: str) -> set[str]:
    normalized = user_story.lower()
    signals: set[str] = set()
    if re.search(r"\bform|field|submit|reactive\b", normalized):
        signals.add("form")
    if re.search(r"\bvalidat|error message|invalid\b", normalized):
        signals.add("validation")
    if re.search(r"\broute|redirect|navigation|path\b", normalized):
        signals.add("routing")
    if re.search(r"\bapp-[a-z0-9-]+\b", normalized):
        signals.add("selectors")
    if re.search(r"\btabs?|table|grid|tree|pagination|data grid\b", normalized):
        signals.add("grid_table_tabs")
    if re.search(r"\baria|accessib|keyboard|screen reader\b", normalized):
        signals.add("aria")
    return signals


def build_card_index(sources: list[SourceDocument]) -> list[ContextCard]:
    cards: list[ContextCard] = []
    for source in sources:
        if not source.path.exists():
            continue
        text = source.path.read_text(encoding="utf-8")
        sections = _split_sections(text)
        for idx, (heading, content) in enumerate(sections, start=1):
            compact = _compact_content(content)
            if not compact:
                continue
            cards.append(
                ContextCard(
                    card_id=f"{source.source_id}_{idx:03d}",
                    source_id=source.source_id,
                    heading=heading,
                    content=compact,
                    tags=source.tags,
                )
            )
    return cards


def retrieve_context_for_role(
    *,
    role: Role,
    user_story: str,
    cards: list[ContextCard],
    source_map: dict[str, SourceDocument],
    max_chars: int,
    per_card_max_chars: int = 700,
) -> RetrievalResult:
    if max_chars <= 0 or not cards:
        return RetrievalResult(role=role, context="", selected_card_ids=(), dropped_card_ids=(), truncated=False)

    signals = infer_story_signals(user_story)
    story_tokens = _tokenize(user_story)
    mandatory_sources = {
        src.source_id
        for src in source_map.values()
        if role in src.mandatory_for
    }

    scored: list[tuple[float, ContextCard]] = []
    mandatory_cards: list[ContextCard] = []
    optional_cards: list[ContextCard] = []

    for card in cards:
        if card.source_id in mandatory_sources:
            mandatory_cards.append(card)
            continue
        score = _score_card(card, role=role, signals=signals, story_tokens=story_tokens)
        scored.append((score, card))

    mandatory_cards.sort(key=lambda c: c.card_id)
    scored.sort(key=lambda item: (-item[0], item[1].card_id))
    optional_cards = [item[1] for item in scored]

    selected: list[ContextCard] = []
    dropped: list[str] = []
    budget = 0

    def format_card(card: ContextCard) -> str:
        compact_content = card.content if len(card.content) <= per_card_max_chars else f"{card.content[:per_card_max_chars]} ..."
        return f"[{card.card_id}] {card.heading}\n{compact_content}"

    chunks: list[str] = []

    for card in mandatory_cards:
        rendered = format_card(card)
        chunks.append(rendered)
        selected.append(card)
        budget += len(rendered) + 2

    for card in optional_cards:
        rendered = format_card(card)
        projected = budget + len(rendered) + 2
        if projected > max_chars:
            dropped.append(card.card_id)
            continue
        chunks.append(rendered)
        selected.append(card)
        budget = projected

    context = "\n\n".join(chunks)
    truncated = len(dropped) > 0
    return RetrievalResult(
        role=role,
        context=context,
        selected_card_ids=tuple(card.card_id for card in selected),
        dropped_card_ids=tuple(dropped),
        truncated=truncated,
    )


def _split_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    heading_re = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
    has_headings = any(heading_re.match(line) for line in lines)

    if has_headings:
        sections: list[tuple[str, str]] = []
        current_heading = "Overview"
        current_lines: list[str] = []
        for line in lines:
            match = heading_re.match(line)
            if match:
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines).strip()))
                current_heading = match.group(1).strip()
                current_lines = []
                continue
            current_lines.append(line)
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines).strip()))
        return [section for section in sections if section[1]]

    blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
    return [(f"Block {idx}", block) for idx, block in enumerate(blocks, start=1)]


def _compact_content(content: str) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", content.strip())
    compact = re.sub(r"[ \t]+", " ", compact)
    return compact


def _tokenize(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", text.lower())
        if token not in STOP_WORDS
    }
    return tokens


def _score_card(card: ContextCard, *, role: Role, signals: set[str], story_tokens: set[str]) -> float:
    role_affinity: dict[Role, set[str]] = {
        "planner": {"PLANNER_WORKORDERS", "PATTERN_CATALOG", "PATTERN_INDEX", "BLUEPRINT", "INSTRUCTIONS"},
        "developer": {"DEVELOPER_EXECUTION", "PATTERN_CATALOG", "BLUEPRINT", "INSTRUCTIONS"},
        "validator": {"VALIDATOR_AUDIT", "BLUEPRINT", "INSTRUCTIONS"},
    }

    score = 0.0
    if card.source_id in role_affinity[role]:
        score += 60.0

    card_tokens = _tokenize(f"{card.heading}\n{card.content}")
    overlap = len(card_tokens.intersection(story_tokens))
    score += min(40.0, overlap * 2.0)

    for signal in signals:
        if signal in card.tags:
            score += 20.0

    return score
