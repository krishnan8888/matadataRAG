from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalRequest:
    query: str
    document_ids: list[str] | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    top_k: int = 5


@dataclass
class RetrievalResult:
    document_id: str
    content: str
    source: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
