from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter


@dataclass(frozen=True)
class RouterRegistration:
    order: int
    router: APIRouter


@dataclass(frozen=True)
class ModuleDefinition:
    key: str
    owner: str
    contract_version: str
    routers: tuple[RouterRegistration, ...]
