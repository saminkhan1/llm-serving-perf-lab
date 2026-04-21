from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from subprocess import Popen
from typing import Any

from lsp.workloads import NormalizedRequest


@dataclass(frozen=True)
class BackendLifecycleError(RuntimeError):
    phase: str
    message: str
    details: dict[str, Any]

    def __str__(self) -> str:
        if not self.details:
            return f"{self.phase}: {self.message}"
        detail_pairs = ", ".join(f"{key}={value}" for key, value in sorted(self.details.items()))
        return f"{self.phase}: {self.message} ({detail_pairs})"


@dataclass(frozen=True)
class BackendResponse:
    request_id: str
    status: str
    output_text: str
    output_tokens: int | None
    finish_reason: str | None
    raw_response: dict[str, Any]


@dataclass(frozen=True)
class BackendLaunchInfo:
    base_url: str
    scrape_endpoint: str
    version: str | None
    runtime_metadata: dict[str, Any]


class BackendAdapter(ABC):
    process: Popen[str] | None

    @abstractmethod
    def launch(self) -> BackendLaunchInfo:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def submit(self, request: NormalizedRequest) -> BackendResponse:
        raise NotImplementedError

    @abstractmethod
    def collect_metrics(self) -> list[dict[str, Any]]:
        raise NotImplementedError
