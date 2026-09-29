from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.modules.community.contracts import (
    CatalogSummary,
    Community,
    CommunityDetail,
    CommunityFeedSummary,
    PublicProfile,
)


@runtime_checkable
class CommunityRepositoryPort(Protocol):
    def list_catalog(
        self,
        *,
        include_blocked: bool = False,
        include_obsolete: bool = True,
    ) -> CatalogSummary: ...

    def get_or_create_profile(self, user_id: int) -> PublicProfile: ...

    def list_communities(self) -> list[Community]: ...

    def community_detail(self, community_slug: str) -> CommunityDetail | None: ...

    def list_community_feed(
        self,
        community_slug: str,
        **filters: object,
    ) -> CommunityFeedSummary | None: ...
