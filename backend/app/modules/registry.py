from __future__ import annotations

from typing import Iterable

from fastapi import APIRouter

from app.modules.assembly import ModuleDefinition


def module_definitions() -> tuple[ModuleDefinition, ...]:
    from app.modules.accessibility.api import MODULE as accessibility
    from app.modules.administration.api import MODULE as administration
    from app.modules.community.api import MODULE as community
    from app.modules.design_system.api import MODULE as design_system
    from app.modules.identity.api import MODULE as identity
    from app.modules.finance.api import MODULE as finance
    from app.modules.integrations.api import MODULE as integrations
    from app.modules.operations.api import MODULE as operations

    definitions = (
        identity,
        community,
        operations,
        administration,
        design_system,
        accessibility,
        finance,
        integrations,
    )
    keys = [definition.key for definition in definitions]
    if len(keys) != len(set(keys)):
        raise RuntimeError("chave de módulo duplicada")
    return definitions


def module_routers() -> Iterable[APIRouter]:
    registrations = [
        registration
        for definition in module_definitions()
        for registration in definition.routers
    ]
    orders = [registration.order for registration in registrations]
    if len(orders) != len(set(orders)):
        raise RuntimeError("ordem de router duplicada")
    for registration in sorted(registrations, key=lambda item: item.order):
        yield registration.router
