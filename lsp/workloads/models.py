from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedRequest:
    request_id: str
    prompt: str
    prompt_token_count: int
    arrival_timestamp_ms: int
    max_new_tokens: int
    decoding_params: dict[str, Any]
    tags: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
