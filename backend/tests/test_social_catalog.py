from pathlib import Path
from io import BytesIO
import hashlib
import struct
import zipfile

import pytest
from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

from app.print_profiles import MaterialProfilePayload, PrintProfilesRepository, SlicingProfilePayload
from app.search_discovery import SearchDiscoveryRepository
from app.social_catalog import CatalogVariantUpdate, CommunityFeedCreate, CommunityPostCreate, CommunityPostUpdate, DiscussionCommentCreate, DiscussionCommentUpdate, LibraryCollectionCreate, LibraryCollectionItemCreate, LibraryFileMetadata, LibraryItemCreate, LibraryItemUpdate, LibraryVersionCreate, PrintListCreate, PrintListItemCreate, PrintListItemUpdate, PrinterPublicUpdate, PublicProfileUpdate, SocialCatalogRepository
from app.social_moderation import ModerationActionPayload, ModerationReportCreate, SocialModerationRepository
from app.social_notifications import ContentFollowPayload, NotificationPreferenceUpdate, SocialNotificationsRepository
from app.social_ranking import SocialRankingRepository
from app.social_safety import SocialSafetyRepository, SocialSafetySettingsUpdate
from app.social_storage import SocialStorageRepository
from app.technical_profiles import TechnicalPrinterConfigPayload, TechnicalProfilesRepository


def test_catalog_seed_has_voron_models_and_variants(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).list_catalog()

    manufacturer = next(item for item in catalog.manufacturers if item.slug == "voron-design")
    model_slugs = {item.slug for item in manufacturer.models}
    variant_names = {variant.name for model in manufacturer.models for variant in model.variants}

    assert {"voron-0-2", "voron-2-4"}.issubset(model_slugs)
    assert "Voron 2.4 R2 350mm" in variant_names


def test_technical_printer_config_is_public_without_operational_secrets(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="maker@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron bancada", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    social = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in social.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )
    social.update_profile(user.id, PublicProfileUpdate(slug="maker", display_name="Maker", visibility="public"))
    social.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]

    repository = TechnicalProfilesRepository(database_path)
    config = repository.create_config(
        user.id,
        TechnicalPrinterConfigPayload(
            printer_id=printer.id,
            community_slug=community.slug,
            title="Voron 2.4 ABS estável",
            visibility="community",
            mods=["Tap", "Nevermore"],
            components={"hotend": "Revo Voron", "extruder": "Clockwork 2"},
            calibrations={"z_offset": "-0.420", "pressure_advance": "0.035"},
            notes="Perfil técnico público com peças e ajuste documentados.",
        ),
    )

    community_configs = repository.community_configs(community.slug)
    assert config.id in {item.id for item in community_configs}
    assert community_configs[0].manufacturer_name == "Voron Design"
    assert "secret-voron" not in community_configs[0].model_dump_json()
    assert "moonraker" not in community_configs[0].model_dump_json().lower()

    try:
        repository.create_config(
            user.id,
            TechnicalPrinterConfigPayload(
                printer_id=printer.id,
                community_slug=community.slug,
                title="token privado",
                visibility="community",
            ),
        )
    except ValueError as exc:
        assert "sensível" in str(exc)
    else:
        raise AssertionError("configuração com dado sensível deveria falhar")


def test_technical_config_comparison_normalizes_community_fields(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    first = auth.create_user(UserRegisterRequest(email="first@example.com", password="correct-horse"))
    second = auth.create_user(UserRegisterRequest(email="second@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in social.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )
    first_printer = PrinterRepository(database_path, user_id=first.id).create_printer(
        PrinterCreate(name="Voron A", moonraker_url="http://a.local:7125", host_audit_mode="disabled")
    )
    second_printer = PrinterRepository(database_path, user_id=second.id).create_printer(
        PrinterCreate(name="Voron B", moonraker_url="http://b.local:7125", host_audit_mode="disabled")
    )
    social.update_profile(first.id, PublicProfileUpdate(slug="first", display_name="First", visibility="public"))
    social.update_profile(second.id, PublicProfileUpdate(slug="second", display_name="Second", visibility="public"))
    social.update_printer_public(first_printer.id, first.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    social.update_printer_public(second_printer.id, second.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]
    repository = TechnicalProfilesRepository(database_path)

    repository.create_config(
        first.id,
        TechnicalPrinterConfigPayload(
            printer_id=first_printer.id,
            community_slug=community.slug,
            title="ABS rápido",
            visibility="community",
            components={"hotend": "Dragon HF"},
            calibrations={"flow": "0.96"},
        ),
    )
    repository.create_config(
        second.id,
        TechnicalPrinterConfigPayload(
            printer_id=second_printer.id,
            community_slug=community.slug,
            title="ABS qualidade",
            visibility="community",
            components={"hotend": "Revo Voron"},
            calibrations={"flow": "0.98"},
        ),
    )

    comparison = repository.compare_community(community.slug)
    assert len(comparison.configs) == 2
    assert comparison.normalized_components["hotend"] == ["Dragon HF", "Revo Voron"]
    assert comparison.normalized_calibrations["flow"] == ["0.96", "0.98"]


def test_material_and_slicing_profile_tracks_compatibility_and_export(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="material@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in social.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron material", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    social.update_profile(user.id, PublicProfileUpdate(slug="material-maker", display_name="Material Maker", visibility="public"))
    social.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]
    repository = PrintProfilesRepository(database_path)

    profile = repository.create_profile(
        user.id,
        MaterialProfilePayload(
            printer_id=printer.id,
            community_slug=community.slug,
            title="ABS Voron 0.4",
            visibility="community",
            material_brand="KVP",
            material_type="ABS",
            nozzle_diameter_mm=0.4,
            bed_temperature_c=110,
            nozzle_temperature_c=245,
            flow_percent=98,
            version_label="v1",
            compatibility={"printer": "Voron 2.4 R2 350mm", "nozzle": "0.4mm", "material": "ABS"},
            slicing=SlicingProfilePayload(layer_height_mm=0.2, speed_mm_s=180, infill_percent=25, supports_enabled=False, goal="quality"),
        ),
    )
    public_profiles = repository.community_profiles(community.slug)
    exported = repository.export_profile(profile.id)
    imported = repository.import_profile(user.id, exported)

    assert profile.material_type == "ABS"
    assert profile.slicing.layer_height_mm == 0.2
    assert public_profiles[0].title == "ABS Voron 0.4"
    assert "secret-voron" not in public_profiles[0].model_dump_json()
    assert exported.format == "printora.material-profile.v1"
    assert imported.visibility == "private"
    assert imported.title.endswith("importado")

    try:
        repository.create_profile(
            user.id,
            MaterialProfilePayload(title="token privado", visibility="private", material_type="PLA"),
        )
    except ValueError as exc:
        assert "sensível" in str(exc)
    else:
        raise AssertionError("perfil com dado sensível deveria falhar")


def test_search_discovery_indexes_public_content_and_filters_private(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="search@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in social.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Search Voron", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    social.update_profile(user.id, PublicProfileUpdate(slug="search-maker", display_name="Search Maker", visibility="public"))
    social.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]
    social.create_community_post(community.slug, user.id, CommunityPostCreate(content_type="question", title="Stringing com ABS", body="Ajuste de temperatura e PA", material="ABS", component="hotend", problem_tag="stringing"))
    social.create_library_item(
        user.id,
        LibraryItemCreate(
            title="Duto ABS público",
            description="Duto para Voron",
            visibility="community",
            community_slug=community.slug,
            catalog_variant_id=variant.id,
            component="toolhead",
            material_suggestion="ABS",
            license="cc-by",
            original_author_name="Search Maker",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="duto.stl")],
        ),
    )
    social.create_library_item(
        user.id,
        LibraryItemCreate(
            title="Arquivo privado oculto",
            description="Não deve aparecer",
            visibility="private",
            catalog_variant_id=variant.id,
            license="cc-by",
            files=[LibraryFileMetadata(file_kind="stl", file_name="privado.stl")],
        ),
    )
    TechnicalProfilesRepository(database_path).create_config(
        user.id,
        TechnicalPrinterConfigPayload(printer_id=printer.id, community_slug=community.slug, title="Config ABS Tap", visibility="community", mods=["Tap"], components={"hotend": "Revo"}, calibrations={"flow": "0.98"}),
    )
    PrintProfilesRepository(database_path).create_profile(
        user.id,
        MaterialProfilePayload(
            printer_id=printer.id,
            community_slug=community.slug,
            title="Perfil ABS busca",
            visibility="community",
            material_type="ABS",
            nozzle_diameter_mm=0.4,
            compatibility={"material": "ABS"},
            slicing=SlicingProfilePayload(layer_height_mm=0.2, goal="quality"),
        ),
    )

    repository = SearchDiscoveryRepository(database_path)
    results = repository.search(query="ABS", page_size=40)
    material_results = repository.search(query="ABS", material="ABS", page_size=20)
    library = repository.search(entity_type="library_item", file_kind="stl")
    tags = {tag.slug for tag in repository.list_tags()}
    dumped = results.model_dump_json().lower()

    result_titles = {item.title for item in results.results}
    assert {"Stringing com ABS", "Duto ABS público", "Config ABS Tap", "Perfil ABS busca"}.issubset(result_titles)
    assert all("material-abs" in item.tags or "abs" in item.title.lower() for item in material_results.results)
    assert "Arquivo privado oculto" not in result_titles
    assert any(item.entity_type == "catalog_variant" for item in results.results)
    assert library.results and all(item.file_kind == "Stl" for item in library.results)
    assert {"material-abs", "component-hotend", "license-cc-by", "file-stl"}.issubset(tags)
    assert "secret-voron" not in dumped
    assert "moonraker" not in dumped


def test_social_ranking_recommendations_ignore_self_vote_and_explain_score(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="ranking-owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="ranking-peer@example.com", password="correct-horse"))
    social = SocialCatalogRepository(database_path)
    variant_id = _variant_id(database_path, "voron-2-4-r2-350")
    social.update_profile(owner.id, PublicProfileUpdate(slug="ranking-owner", display_name="Ranking Owner", visibility="public"))
    social.update_profile(peer.id, PublicProfileUpdate(slug="ranking-peer", display_name="Ranking Peer", visibility="public"))
    item = social.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Duto recomendado ABS",
            description="Peça validada pela comunidade.",
            visibility="community",
            community_slug="variant-voron-design-voron-2-4-voron-2-4-r2-350",
            catalog_variant_id=variant_id,
            component="toolhead",
            material_suggestion="ABS",
            license="cc-by",
            original_author_name="Ranking Owner",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="duct.stl")],
        ),
    )
    social.set_library_favorite(item.id, owner.id, True)
    social.set_library_favorite(item.id, peer.id, True)
    social.register_library_download(item.id, owner.id)
    social.register_library_download(item.id, peer.id)

    ranking = SocialRankingRepository(database_path)
    recommendations = ranking.recommendations(query="Duto", material="ABS", page_size=5)
    reputation = ranking.profile_reputation("ranking-owner")
    leaderboard = ranking.leaderboard()

    recommended = next(entry for entry in recommendations.items if entry.result.title == "Duto recomendado ABS")
    assert recommended.score >= 6
    assert any("favorito" in reason or "download" in reason for reason in recommended.reasons)
    assert all("None" not in reason for reason in recommended.reasons)
    assert reputation.reputation_score == 6
    assert reputation.breakdown == {"download": 2, "favorite": 4}
    assert leaderboard.records[0].slug == "ranking-owner"

    with connect_database(database_path) as connection:
        signal_count = connection.execute("SELECT COUNT(*) FROM social_quality_signals WHERE entity_type = 'library_item' AND entity_id = ?", (item.id,)).fetchone()[0]
    assert signal_count == 2

    with connect_database(database_path) as connection:
        connection.execute("DELETE FROM social_materialization_state")

    monkeypatch.setattr(ranking, "_rebuild_signals", lambda connection: pytest.fail("sinais atuais não devem reconstruir"))
    monkeypatch.setattr(
        ranking.search_repository,
        "_rebuild_index",
        lambda connection: pytest.fail("índice atual não deve reconstruir"),
    )
    cached = ranking.recommendations(query="Duto", material="ABS", page_size=5)
    assert cached.items[0].result.title == "Duto recomendado ABS"


def test_social_reputation_empty_snapshot_with_state_does_not_rebuild(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    ranking = SocialRankingRepository(database_path)
    with connect_database(database_path) as connection:
        connection.execute(
            """
            INSERT INTO social_materialization_state (name, source_signature)
            VALUES ('social_quality_signals', 'legacy-empty')
            """
        )

    monkeypatch.setattr(ranking, "_rebuild_signals", lambda connection, source_signature=None: pytest.fail("snapshot vazio com estado não deve reconstruir"))

    assert ranking.leaderboard().records == []


def test_catalog_seed_has_broad_diy_klipper_catalog(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).list_catalog()

    manufacturer_slugs = {item.slug for item in catalog.manufacturers}
    variant_names = {variant.name for manufacturer in catalog.manufacturers for model in manufacturer.models for variant in model.variants}
    variant_states = {variant.name: variant.trust_state for manufacturer in catalog.manufacturers for model in manufacturer.models for variant in model.variants}

    assert {
        "voron-design",
        "rat-rig",
        "vzbot",
        "annex-engineering",
        "hevort",
        "printers-for-ants",
        "zero-g",
        "railcore-labs",
        "seckit",
        "blv-projects",
        "hypercube",
        "d-bot",
        "v-king",
        "croxy",
        "rook",
        "positron",
        "the-100",
        "doron",
        "snakeoilxy",
        "maybecube",
        "rolohaun-design",
        "mszturc",
        "tiny3dp",
        "open-lab-starter-kit",
        "babycube",
    }.issubset(manufacturer_slugs)
    assert {"RatRig V-Core 3 400mm", "RatRig V-Core 4 500mm", "VzBot 330", "Annex K3 180mm", "Micron+ 180mm", "Salad Fork 160mm", "ZeroG Mercury One.1 Ender 5 conversion", "RailCore II 300ZL", "The 100 100mm", "Voron Phoenix 600mm draft"}.issubset(variant_names)
    assert {"Salad Fork 120mm", "Salad Fork 180mm", "Tiny-T draft", "Stealth Fork beta", "Magpie draft", "Dynasty draft"}.issubset(variant_names)
    assert {"RatRig V-Chonk 180mm beta", "Annex K1 draft", "Bastion draft", "MaybeCube MC350 draft", "T250 v1 192x212x175", "OLSK Small V3", "OLSK Large V3"}.issubset(variant_names)
    assert len(variant_names) >= 68
    assert variant_states["HevORT 500 draft"] == "draft"
    assert variant_states["SnakeOilXY 250mm draft"] == "draft"
    assert variant_states["SM-100 experimental"] == "draft"


def test_catalog_admin_exposes_enriched_manufacturer_and_model_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).search_catalog_admin(manufacturer="vzbot")
    model = next(item for item in catalog.models if item.slug == "vzbot")

    assert model.manufacturer_website_url == "https://vzbot.org/"
    assert model.manufacturer_logo_url == "https://github.com/VzBoT3D.png"
    assert model.manufacturer_discord_url == "https://discord.gg/vzbot"
    assert model.repository_url == "https://github.com/VzBoT3D/VzBoT-Vz330"
    assert model.documentation_url == "https://docs.vzbot.org/"
    assert "alta velocidade" in (model.description or "")
    assert model.detail["focus"] == "alta velocidade"
    assert model.source_links["github_vz330"] == "https://github.com/VzBoT3D/VzBoT-Vz330"


def test_catalog_admin_exposes_deeper_model_detail_and_avoids_uncertain_logos(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).search_catalog_admin(manufacturer="rat-rig")

    v_chonk = next(item for item in catalog.models if item.slug == "v-chonk")
    v_core_4 = next(item for item in catalog.models if item.slug == "v-core-4")

    assert v_chonk.detail["release"] == "v0.4 beta"
    assert v_chonk.detail["volume"] == "180 x 180 x 180 mm"
    assert v_chonk.source_links["github"] == "https://github.com/Rat-Rig/V-Chonk"
    assert v_core_4.manufacturer_logo_url is None
    assert v_core_4.image_url is None


def test_catalog_admin_search_filters_component_kinematics_firmware_and_state(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SocialCatalogRepository(database_path)

    corexy = repository.search_catalog_admin(component="Stealthburner", kinematics="corexy", firmware_family="klipper", trust_state="official")
    drafts = repository.search_catalog_admin(trust_state="draft")
    blocked = repository.search_catalog_admin(trust_state="blocked")
    default_catalog = repository.search_catalog_admin()

    corexy_variants = [variant for model in corexy.models for variant in model.variants]
    draft_variants = [variant for model in drafts.models for variant in model.variants]
    blocked_variants = [variant for model in blocked.models for variant in model.variants]
    default_slugs = {model.manufacturer_slug for model in default_catalog.models}

    assert any(model.manufacturer_slug == "voron-design" and model.slug == "voron-2-4" for model in corexy.models)
    assert any(variant.name == "Voron 2.4 R2 350mm" for variant in corexy_variants)
    assert {item.trust_state for item in draft_variants} == {"draft"}
    assert "hevort" in {item.manufacturer_slug for item in drafts.models}
    assert "jubilee" in {item.manufacturer_slug for item in blocked.models}
    assert all(variant.trust_state == "blocked" for variant in blocked_variants)
    assert "jubilee" not in default_slugs


def test_catalog_seed_does_not_expose_package_ids_in_source_fields(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)

    with connect_database(database_path) as connection:
        sources = connection.execute(
            """
            SELECT source FROM catalog_manufacturers
            UNION ALL SELECT source FROM catalog_printer_models
            UNION ALL SELECT source FROM catalog_printer_variants
            """
        ).fetchall()

    assert sources
    assert all("pkg" not in str(row["source"]).lower() for row in sources)


def test_catalog_duplicate_variant_slug_is_rejected(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="admin@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    catalog = repository.list_catalog()
    voron_24 = next(model for manufacturer in catalog.manufacturers for model in manufacturer.models if model.slug == "voron-2-4")

    from app.social_catalog import CatalogVariantCreate

    try:
        repository.create_variant(
            CatalogVariantCreate(model_id=voron_24.id, slug="voron-2-4-r2-350", name="Duplicada"),
            actor_user_id=user.id,
        )
    except Exception as exc:
        assert "UNIQUE" in str(exc) or "unique" in str(exc).lower()
    else:
        raise AssertionError("duplicated variant slug should fail")


def test_obsolete_and_blocked_variants_do_not_break_existing_printer_link(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    variant = next(
        variant
        for manufacturer in repository.list_catalog().manufacturers
        for model in manufacturer.models
        for variant in model.variants
        if variant.slug == "voron-2-4-r2-350"
    )

    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    repository.update_variant(variant.id, CatalogVariantUpdate(trust_state="obsolete"), actor_user_id=user.id)
    with connect_database(database_path) as connection:
        linked = connection.execute("SELECT catalog_variant_id FROM printers WHERE id = ?", (printer.id,)).fetchone()
    assert linked["catalog_variant_id"] == variant.id

    try:
        repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    except ValueError as exc:
        assert "inválida" in str(exc)
    else:
        raise AssertionError("obsolete variant should not be accepted for new publication")

    repository.update_variant(variant.id, CatalogVariantUpdate(trust_state="blocked"), actor_user_id=user.id)
    visible_catalog = repository.list_catalog()
    assert all(visible.id != variant.id for manufacturer in visible_catalog.manufacturers for model in manufacturer.models for visible in model.variants)


def test_catalog_detail_api_allows_common_read_and_blocks_common_write(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            common = client.post("/api/auth/register", json={"email": "user@example.com", "password": "correct-horse"})
            admin = client.post("/api/auth/register", json={"email": "breno@mayder.com.br", "password": "correct-horse"})
            common_token = common.json()["access_token"]
            admin_token = admin.json()["access_token"]

            common_read = client.get("/api/catalog/admin", headers={"Authorization": f"Bearer {common_token}"})
            allowed = client.get("/api/catalog/admin", headers={"Authorization": f"Bearer {admin_token}"})
            variant_id = allowed.json()["models"][0]["variants"][0]["id"]
            common_update = client.put(
                f"/api/catalog/variants/{variant_id}",
                headers={"Authorization": f"Bearer {common_token}"},
                json={"trust_state": "community", "source": "common_review"},
            )
            updated = client.put(
                f"/api/catalog/variants/{variant_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"trust_state": "community", "source": "admin_review"},
            )

            assert common_read.status_code == 200
            assert common_read.json()["models"]
            assert allowed.status_code == 200
            assert common_update.status_code == 403
            assert updated.status_code == 200
            assert updated.json()["trust_state"] == "community"
    finally:
        get_settings.cache_clear()


def test_public_profile_is_separate_from_auth_identity(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse", whatsapp="+550099999999"))
    repository = SocialCatalogRepository(database_path)

    profile = repository.update_profile(
        user.id,
        PublicProfileUpdate(
            slug="voron-owner",
            display_name="Voron Owner",
            bio="CoreXY and ABS",
            location="BH",
            social_links={"github": "https://github.com/example", "whatsapp": "+5500"},
            visibility="public",
        ),
    )

    assert profile.slug == "voron-owner"
    assert profile.social_links == {"github": "https://github.com/example"}
    assert "owner@example.com" not in profile.model_dump_json()
    assert "+550099999999" not in profile.model_dump_json()


def test_social_profile_rejects_duplicate_and_reserved_slug(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="peer@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)

    repository.update_profile(owner.id, PublicProfileUpdate(slug="maker-one", display_name="Maker One", visibility="public"))
    repository.update_profile(peer.id, PublicProfileUpdate(slug="maker-two", display_name="Maker Two", visibility="public"))

    try:
        repository.update_profile(peer.id, PublicProfileUpdate(slug="maker-one", display_name="Maker Two", visibility="public"))
    except ValueError as exc:
        assert "uso" in str(exc)
    else:
        raise AssertionError("duplicate profile slug should fail")

    repository.update_profile(owner.id, PublicProfileUpdate(slug="maker-three", display_name="Maker One", visibility="public"))
    try:
        repository.update_profile(peer.id, PublicProfileUpdate(slug="maker-one", display_name="Maker Two", visibility="public"))
    except ValueError as exc:
        assert "anteriormente" in str(exc)
    else:
        raise AssertionError("reserved old profile slug should fail")

    owner_profile = repository.get_or_create_profile(owner.id)
    assert "maker-one" in owner_profile.reserved_slugs


def test_profile_visibility_private_unlisted_and_blocking_rules(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="peer@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)

    repository.update_profile(owner.id, PublicProfileUpdate(slug="hidden-maker", display_name="Hidden Maker", visibility="private"))
    assert repository.public_profile_by_slug("hidden-maker") is None

    repository.update_profile(owner.id, PublicProfileUpdate(slug="direct-maker", display_name="Direct Maker", visibility="unlisted"))
    assert repository.public_profile_by_slug("direct-maker") is not None

    repository.get_or_create_profile(peer.id)
    repository.set_relationship(owner.id, peer.id, "block", "active")
    blocked_view = repository.public_profile_by_slug("direct-maker", viewer_user_id=peer.id)
    assert blocked_view is not None
    assert blocked_view.viewer_blocked is True


def test_profile_rejects_unsafe_avatar_and_social_links(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)

    unsafe_payloads = [
        {"avatar_url": "http://example.com/avatar.png", "social_links": {}},
        {"avatar_url": "https://localhost/avatar.png", "social_links": {}},
        {"avatar_url": None, "social_links": {"github": "https://evil.example/profile"}},
        {"avatar_url": None, "social_links": {"website": "https://127.0.0.1/admin"}},
    ]
    for payload in unsafe_payloads:
        try:
            repository.update_profile(
                user.id,
                PublicProfileUpdate(
                    slug="safe-maker",
                    display_name="Safe Maker",
                    visibility="public",
                    avatar_url=payload["avatar_url"],
                    social_links=payload["social_links"],
                ),
            )
        except ValueError:
            continue
        else:
            raise AssertionError(f"unsafe payload should fail: {payload}")

    profile = repository.update_profile(
        user.id,
        PublicProfileUpdate(
            slug="safe-maker",
            display_name="Safe Maker",
            visibility="public",
            avatar_url="https://cdn.example.com/avatar.png",
            social_links={"github": "https://github.com/example", "website": "https://example.com"},
        ),
    )
    assert profile.avatar_url == "https://cdn.example.com/avatar.png"
    assert profile.social_links == {"github": "https://github.com/example", "website": "https://example.com"}


def test_public_printer_requires_catalog_and_never_exposes_operational_endpoint(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(user.id)

    try:
        repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True))
    except ValueError as exc:
        assert "variante" in str(exc)
    else:
        raise AssertionError("public printer without catalog variant should fail")

    with connect_database(database_path) as connection:
        variant = connection.execute(
            """
            SELECT v.id
            FROM catalog_printer_variants v
            JOIN catalog_printer_models m ON m.id = v.model_id
            WHERE m.slug = 'voron-2-4'
            ORDER BY v.id
            LIMIT 1
            """
        ).fetchone()

    public = repository.update_printer_public(
        printer.id,
        user.id,
        PrinterPublicUpdate(
            public_profile_enabled=True,
            catalog_variant_id=variant["id"],
            public_name="Voron ABS",
            public_description="Perfil público sem endpoint operacional.",
            public_mods=["Tap", "Nevermore", "Tap"],
            public_images=["https://example.com/voron.jpg"],
        ),
    )

    assert public is not None
    assert public.public_name == "Voron ABS"
    assert public.public_mods == ["Tap", "Nevermore"]
    assert "secret-voron" not in public.model_dump_json()


def test_public_printer_rejects_invalid_images_and_blocked_variant(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    variant = _variant_id(database_path, "voron-2-4-r2-350")

    for image_url in ["http://example.com/voron.jpg", "https://localhost/voron.jpg", "https://127.0.0.1/voron.jpg"]:
        try:
            PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant, public_images=[image_url])
        except ValueError as exc:
            assert "https" in str(exc) or "privado" in str(exc)
        else:
            raise AssertionError("invalid public image URL should fail")

    repository.update_variant(variant, CatalogVariantUpdate(trust_state="blocked"), actor_user_id=user.id)
    try:
        repository.update_printer_public(
            printer.id,
            user.id,
            PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant, public_images=["https://example.com/voron.jpg"]),
        )
    except ValueError as exc:
        assert "inválida" in str(exc)
    else:
        raise AssertionError("blocked variant should not publish")


def test_public_printer_privacy_search_profile_community_and_direct_page(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    repository.update_profile(user.id, PublicProfileUpdate(slug="owner-public", display_name="Owner", visibility="public"))
    variant = _variant_id(database_path, "voron-2-4-r2-350")

    assert repository.public_printer(printer.id) is None
    assert repository.list_public_printers_for_profile("owner-public") == []
    assert repository.search_public_printers(manufacturer="Voron") == []
    assert all(item.printer_count == 0 for item in repository.list_communities())

    public = repository.update_printer_public(
        printer.id,
        user.id,
        PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant, public_name="Voron pública"),
    )
    assert public is not None
    assert repository.public_printer(printer.id) is not None
    assert repository.search_public_printers(manufacturer="Voron")
    assert any(item.printer_count > 0 for item in repository.list_communities())

    repository.update_profile(user.id, PublicProfileUpdate(slug="owner-private", display_name="Owner", visibility="private"))
    assert repository.public_printer(printer.id) is None
    assert repository.search_public_printers(manufacturer="Voron") == []
    assert all(item.printer_count == 0 for item in repository.list_communities())

    repository.update_profile(user.id, PublicProfileUpdate(slug="owner-public", display_name="Owner", visibility="public"))
    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=False))
    assert repository.public_printer(printer.id) is None
    assert repository.search_public_printers(manufacturer="Voron") == []
    assert all(item.printer_count == 0 for item in repository.list_communities())


def test_public_printer_api_blocks_other_user_and_sanitizes_direct_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            peer = client.post("/api/auth/register", json={"email": "peer@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            peer_token = peer.json()["access_token"]
            printer_response = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "name": "Secret Voron",
                    "moonraker_url": "http://secret-voron.local:7125",
                    "host_audit_mode": "ssh",
                    "ssh_host": "10.0.0.5",
                    "ssh_username": "pi",
                    "ssh_credential": "secret",
                },
            )
            printer = printer_response.json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")

            blocked = client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {peer_token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant},
            )
            published = client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "public_profile_enabled": True,
                    "catalog_variant_id": variant,
                    "public_name": "Voron ABS",
                    "public_description": "Perfil público",
                    "public_mods": ["Tap"],
                    "public_images": ["https://example.com/voron.jpg"],
                },
            )
            payload = client.get(f"/api/public/printers/{printer['id']}").json()
            private_response = client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"public_profile_enabled": False},
            )
            hidden = client.get(f"/api/public/printers/{printer['id']}")

            assert printer_response.status_code == 200
            assert blocked.status_code == 404
            assert published.status_code == 200
            assert private_response.status_code == 200
            assert hidden.status_code == 404
            dumped = str(payload).lower()
            assert "moonraker" not in dumped
            assert "secret-voron" not in dumped
            assert "ssh" not in dumped
            assert "token" not in dumped
            assert "credential" not in dumped
            assert "organization" not in dumped
            assert "permission" not in dumped
    finally:
        get_settings.cache_clear()


def test_technical_printer_config_api_crud_and_public_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "tech-owner@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            profile = client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"slug": "tech-owner", "display_name": "Tech Owner", "visibility": "public"},
            )
            printer_response = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "name": "Tech Voron",
                    "moonraker_url": "http://secret-voron.local:7125",
                    "host_audit_mode": "disabled",
                },
            )
            printer = printer_response.json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            published = client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Tech Voron"},
            )
            communities = SocialCatalogRepository(tmp_path / "printora.db").list_communities(variant="voron-2-4-r2-350")
            community_slug = communities[0].slug

            created = client.post(
                "/api/social/technical-configs",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "printer_id": printer["id"],
                    "community_slug": community_slug,
                    "title": "ABS estável",
                    "visibility": "community",
                    "mods": ["Tap"],
                    "components": {"hotend": "Revo Voron"},
                    "calibrations": {"flow": "0.97"},
                    "notes": "Uso público em ABS.",
                },
            )
            config_id = created.json()["id"]
            public_list = client.get(f"/api/social/communities/{community_slug}/technical-configs")
            comparison = client.get(f"/api/social/communities/{community_slug}/technical-configs/comparison")
            updated = client.put(
                f"/api/social/technical-configs/{config_id}",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "printer_id": printer["id"],
                    "community_slug": community_slug,
                    "title": "ABS qualidade",
                    "visibility": "community",
                    "mods": ["Tap", "Nevermore"],
                    "components": {"hotend": "Revo Voron"},
                    "calibrations": {"flow": "0.98"},
                    "notes": "Uso público revisado.",
                },
            )
            bad = client.post(
                "/api/social/technical-configs",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "printer_id": printer["id"],
                    "community_slug": community_slug,
                    "title": "Configuração sensível",
                    "visibility": "community",
                    "components": {"host": "secret-voron.local"},
                },
            )
            archived = client.delete(f"/api/social/technical-configs/{config_id}", headers={"Authorization": f"Bearer {owner_token}"})
            after_archive = client.get(f"/api/social/communities/{community_slug}/technical-configs")

            assert profile.status_code == 200
            assert published.status_code == 200
            assert created.status_code == 200
            assert public_list.status_code == 200
            assert comparison.status_code == 200
            assert updated.status_code == 200
            assert bad.status_code in {400, 422}
            assert archived.status_code == 204
            assert after_archive.status_code == 200
            assert after_archive.json() == []
            dumped = str(public_list.json()).lower()
            assert "secret-voron" not in dumped
            assert "moonraker" not in dumped
            assert comparison.json()["normalized_components"]["hotend"] == ["Revo Voron"]
    finally:
        get_settings.cache_clear()


def test_material_profile_api_crud_export_import_and_public_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "profile-owner@example.com", "password": "correct-horse"})
            token = owner.json()["access_token"]
            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"slug": "profile-owner", "display_name": "Profile Owner", "visibility": "public"},
            )
            printer = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Material Voron", "moonraker_url": "http://secret-voron.local:7125", "host_audit_mode": "disabled"},
            ).json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Material Voron"},
            )
            community_slug = SocialCatalogRepository(tmp_path / "printora.db").list_communities(variant="voron-2-4-r2-350")[0].slug

            payload = {
                "printer_id": printer["id"],
                "catalog_variant_id": variant,
                "community_slug": community_slug,
                "title": "ABS 0.4 qualidade",
                "visibility": "community",
                "material_brand": "KVP",
                "material_type": "ABS",
                "nozzle_diameter_mm": 0.4,
                "bed_temperature_c": 110,
                "nozzle_temperature_c": 245,
                "flow_percent": 98,
                "version_label": "v1",
                "compatibility": {"printer": "Voron 2.4", "nozzle": "0.4mm", "material": "ABS"},
                "slicing": {
                    "layer_height_mm": 0.2,
                    "speed_mm_s": 180,
                    "infill_percent": 25,
                    "supports_enabled": False,
                    "goal": "quality",
                    "settings": {"wall_loops": 4},
                },
            }
            created = client.post("/api/social/material-profiles", headers={"Authorization": f"Bearer {token}"}, json=payload)
            profile_id = created.json()["id"]
            public_list = client.get(f"/api/social/communities/{community_slug}/material-profiles")
            exported = client.get(f"/api/social/material-profiles/{profile_id}/export")
            imported = client.post("/api/social/material-profiles/import", headers={"Authorization": f"Bearer {token}"}, json=exported.json())
            updated = client.put(
                f"/api/social/material-profiles/{profile_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={**payload, "title": "ABS 0.4 resistência", "slicing": {**payload["slicing"], "goal": "strength"}},
            )
            bad = client.post(
                "/api/social/material-profiles",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "token privado", "material_type": "PLA", "visibility": "private", "slicing": {}},
            )
            archived = client.delete(f"/api/social/material-profiles/{profile_id}", headers={"Authorization": f"Bearer {token}"})

            assert created.status_code == 200
            assert public_list.status_code == 200
            assert exported.status_code == 200
            assert imported.status_code == 200
            assert imported.json()["visibility"] == "private"
            assert updated.status_code == 200
            assert updated.json()["slicing"]["goal"] == "strength"
            assert bad.status_code in {400, 422}
            assert archived.status_code == 204
            dumped = str(public_list.json()).lower()
            assert "secret-voron" not in dumped
            assert "moonraker" not in dumped
    finally:
        get_settings.cache_clear()


def test_public_profile_api_does_not_expose_sensitive_account_or_printer_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            created = client.post(
                "/api/auth/register",
                json={"email": "owner@example.com", "password": "correct-horse", "whatsapp": "+550099999999"},
            )
            token = created.json()["access_token"]
            profile_response = client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "slug": "public-owner",
                    "display_name": "Public Owner",
                    "bio": "Voron ABS",
                    "avatar_url": "https://cdn.example.com/avatar.png",
                    "location": "BH",
                    "social_links": {"github": "https://github.com/example"},
                    "visibility": "public",
                },
            )
            payload = client.get("/api/social/profiles/public-owner").json()

            assert profile_response.status_code == 200
            assert payload["slug"] == "public-owner"
            assert "owner@example.com" not in str(payload)
            assert "+550099999999" not in str(payload)
            assert "organizations" not in payload
            assert "permissions" not in payload
            assert "moonraker" not in str(payload).lower()
    finally:
        get_settings.cache_clear()


def test_public_printer_syncs_automatic_communities(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(user.id)
    catalog = repository.list_catalog()
    variant = next(variant for manufacturer in catalog.manufacturers for model in manufacturer.models for variant in model.variants if variant.slug == "voron-2-4-r2-350")

    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant.id))
    communities = repository.list_communities()
    active = [item for item in communities if item.member_count > 0 and item.printer_count > 0]

    assert {item.scope for item in active} == {"manufacturer", "model", "variant"}
    assert any(item.slug.startswith("model-voron-design") for item in active)


def test_public_printer_variant_change_updates_automatic_communities(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    first_variant = _variant_id(database_path, "voron-2-4-r2-300")
    second_variant = _variant_id(database_path, "voron-2-4-r2-350")

    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=first_variant, public_mods=["Tap"]))
    first_detail = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-300")
    assert first_detail is not None
    assert first_detail.printer_count == 1
    assert first_detail.mod_count == 1

    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=second_variant))
    old_detail = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-300")
    new_detail = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-350")

    assert old_detail is not None
    assert new_detail is not None
    assert old_detail.printer_count == 0
    assert new_detail.printer_count == 1
    assert new_detail.member_count == 1


def test_community_filters_use_catalog_and_public_counts_ignore_private(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    private_owner = auth.create_user(UserRegisterRequest(email="private@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    public_printer = PrinterRepository(database_path, user_id=owner.id).create_printer(
        PrinterCreate(name="Voron public", moonraker_url="http://public-voron.local:7125", host_audit_mode="disabled")
    )
    private_printer = PrinterRepository(database_path, user_id=private_owner.id).create_printer(
        PrinterCreate(name="Voron private", moonraker_url="http://private-voron.local:7125", host_audit_mode="disabled")
    )
    variant = _variant_id(database_path, "voron-2-4-r2-350")

    repository.update_printer_public(public_printer.id, owner.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant, public_mods=["Tap"]))
    repository.update_printer_public(private_printer.id, private_owner.id, PrinterPublicUpdate(public_profile_enabled=False, catalog_variant_id=variant, public_mods=["Tap"]))

    communities = repository.list_communities(manufacturer="voron-design", model="voron-2-4", variant="voron-2-4-r2-350", component="stealthburner")
    variant_community = next(item for item in communities if item.scope == "variant")

    assert variant_community.slug == "variant-voron-design-voron-2-4-voron-2-4-r2-350"
    assert variant_community.member_count == 1
    assert variant_community.printer_count == 1
    assert variant_community.file_count == 0
    assert variant_community.mod_count == 1
    assert repository.list_communities(manufacturer="rat-rig", model="voron-2-4") == []


def test_community_obsolete_and_merged_states_are_safe(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    variant = _variant_id(database_path, "voron-2-4-r2-350")
    repository.update_printer_public(printer.id, user.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant))

    repository.update_variant(variant, CatalogVariantUpdate(trust_state="obsolete"), actor_user_id=user.id)
    obsolete = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-350")
    assert obsolete is not None
    assert obsolete.status == "obsolete"
    assert obsolete.member_count == 0
    assert obsolete.printer_count == 0
    assert obsolete.members == []
    assert obsolete.printers == []

    with connect_database(database_path) as connection:
        destination = connection.execute("SELECT id FROM social_communities WHERE slug = 'model-voron-design-voron-2-4'").fetchone()
        assert destination is not None
        connection.execute(
            """
            UPDATE social_communities
            SET status = 'merged', merged_into_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE slug = 'variant-voron-design-voron-2-4-voron-2-4-r2-350'
            """,
            (destination["id"],),
        )

    merged = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-350")
    assert merged is not None
    assert merged.status == "merged"
    assert merged.merged_into_slug == "model-voron-design-voron-2-4"
    assert merged.member_count == 0
    assert merged.printer_count == 0
    assert merged.members == []
    assert merged.printers == []


def test_community_api_by_slug_contract_is_authenticated_and_sanitized(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            token = owner.json()["access_token"]
            printer_response = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": "Secret Voron",
                    "moonraker_url": "http://secret-voron.local:7125",
                    "host_audit_mode": "ssh",
                    "ssh_host": "10.0.0.5",
                    "ssh_username": "pi",
                    "ssh_credential": "secret",
                },
            )
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            published = client.put(
                f"/api/printers/{printer_response.json()['id']}/public-profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Voron ABS"},
            )
            response = client.get(
                "/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350",
                headers={"Authorization": f"Bearer {token}"},
            )
            payload = response.json()
            dumped = str(payload).lower()

            assert printer_response.status_code == 200
            assert published.status_code == 200
            assert response.status_code == 200
            assert payload["slug"] == "variant-voron-design-voron-2-4-voron-2-4-r2-350"
            assert payload["member_count"] == 1
            assert payload["printer_count"] == 1
            assert payload["filters"]["manufacturers"]
            assert "moonraker" not in dumped
            assert "secret-voron" not in dumped
            assert "ssh" not in dumped
            assert "token" not in dumped
            assert "credential" not in dumped
            assert "organization" not in dumped
            assert "permission" not in dumped
    finally:
        get_settings.cache_clear()


def test_community_feed_filters_pagination_and_private_isolation(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    printer = PrinterRepository(database_path, user_id=owner.id).create_printer(
        PrinterCreate(name="Voron real", moonraker_url="http://secret-voron.local:7125", host_audit_mode="disabled")
    )
    variant = _variant_id(database_path, "voron-2-4-r2-350")
    repository.update_profile(owner.id, PublicProfileUpdate(slug="owner-public", display_name="Owner Public", visibility="public"))
    repository.update_printer_public(printer.id, owner.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant))
    community = repository.community_detail("variant-voron-design-voron-2-4-voron-2-4-r2-350")
    assert community is not None

    repository.create_feed_item(
        CommunityFeedCreate(
            community_id=community.id,
            author_user_id=owner.id,
            content_type="question",
            title="Stringing em ABS",
            body="Retracao e temperatura para ABS em camara quente.",
            component="extrusor",
            material="ABS",
            firmware_family="klipper",
            problem_tag="stringing",
        )
    )
    repository.create_feed_item(
        CommunityFeedCreate(
            community_id=community.id,
            author_user_id=owner.id,
            content_type="mod",
            title="Duto auxiliar",
            body="Mod de ventilacao para ponte curta.",
            component="toolhead",
            material="ASA",
            firmware_family="klipper",
            pinned=True,
        )
    )
    repository.create_feed_item(
        CommunityFeedCreate(
            community_id=community.id,
            author_user_id=owner.id,
            content_type="technical_post",
            title="Privado",
            body="Nao deve aparecer",
            visibility="private",
        )
    )

    feed = repository.list_community_feed(community.slug, order="recommended", page_size=2)
    filtered = repository.list_community_feed(community.slug, content_type="question", material="ABS", problem="stringing")

    assert feed is not None
    assert filtered is not None
    assert feed.items
    assert all(item.title != "Privado" for item in feed.items)
    assert feed.items[0].pinned is True
    assert feed.has_more is True
    assert filtered.items[0].title == "Stringing em ABS"
    assert "ABS" in filtered.filters["materials"]
    assert "stringing" in filtered.filters["problems"]
    assert "secret-voron" not in feed.model_dump_json()
    assert "moonraker" not in feed.model_dump_json().lower()


def test_community_feed_api_contract_is_paginated_and_sanitized(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            token = owner.json()["access_token"]
            printer = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Secret Voron", "moonraker_url": "http://secret-voron.local:7125", "host_audit_mode": "disabled"},
            ).json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"slug": "owner-public", "display_name": "Owner Public", "visibility": "public"},
            )
            client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Voron pública"},
            )

            response = client.get(
                "/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350/feed?order=recommended&page_size=5",
            )
            payload = response.json()
            dumped = str(payload).lower()

            assert response.status_code == 200
            assert payload["community"]["slug"] == "variant-voron-design-voron-2-4-voron-2-4-r2-350"
            assert payload["items"]
            assert payload["items"][0]["content_type"] == "curation_notice"
            assert payload["page"] == 1
            assert "components" in payload["filters"]
            assert "moonraker" not in dumped
            assert "secret-voron" not in dumped
            assert "ssh" not in dumped
            assert "token" not in dumped
            assert "organization" not in dumped
    finally:
        get_settings.cache_clear()


def test_discussion_posts_comments_reactions_solution_and_logical_removal(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    author = auth.create_user(UserRegisterRequest(email="author@example.com", password="correct-horse"))
    moderator = auth.create_user(UserRegisterRequest(email="moderator@example.com", password="correct-horse"))
    stranger = auth.create_user(UserRegisterRequest(email="stranger@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    variant = _variant_id(database_path, "voron-2-4-r2-350")
    moderator_printer = PrinterRepository(database_path, user_id=moderator.id).create_printer(
        PrinterCreate(name="Moderador Voron", moonraker_url="http://moderator-voron.local:7125", host_audit_mode="disabled")
    )
    repository.update_profile(author.id, PublicProfileUpdate(slug="author-public", display_name="Author", visibility="public"))
    repository.update_profile(moderator.id, PublicProfileUpdate(slug="moderator-public", display_name="Moderator", visibility="public"))
    repository.get_or_create_profile(stranger.id)
    repository.update_printer_public(moderator_printer.id, moderator.id, PrinterPublicUpdate(public_profile_enabled=True, catalog_variant_id=variant))

    post = repository.create_community_post(
        "variant-voron-design-voron-2-4-voron-2-4-r2-350",
        author.id,
        CommunityPostCreate(
            content_type="question",
            title="Camada ruim em ABS",
            body="Qual ajuste inicial para primeira camada em ABS?",
            component="bed",
            material="ABS",
            firmware_family="klipper",
            problem_tag="first-layer",
            attachments=[{"kind": "link", "url": "https://example.com/ajuste", "label": "referencia"}],
        ),
    )
    comment = repository.create_comment(post.id, moderator.id, DiscussionCommentCreate(body="Revise Z offset e temperatura da mesa."))
    reply = repository.create_comment(post.id, author.id, DiscussionCommentCreate(body="Funcionou depois do ajuste.", parent_comment_id=comment.id))
    repository.set_reaction("post", post.id, moderator.id, "useful", True)
    solved = repository.mark_solution(post.id, comment.id, author.id, False)
    updated = repository.update_post(post.id, author.id, False, CommunityPostUpdate(title="Camada ruim em ABS resolvida"))
    edited_comment = repository.update_comment(comment.id, moderator.id, False, DiscussionCommentUpdate(body="Revise Z offset, mesa e fluxo inicial."))
    detail = repository.discussion_detail(post.id)

    assert solved.solution_comment_id == comment.id
    assert updated.edit_count == 1
    assert edited_comment.edit_count == 1
    assert detail is not None
    assert detail.post.comment_count == 2
    assert detail.post.reaction_count == 1
    assert detail.comments[0].replies[0].id == reply.id
    assert detail.comments[0].body == "Revise Z offset, mesa e fluxo inicial."
    assert "moderator-voron" not in detail.model_dump_json()

    try:
        repository.update_post(post.id, stranger.id, False, CommunityPostUpdate(title="Invasao"))
    except PermissionError as exc:
        assert "autor" in str(exc)
    else:
        raise AssertionError("stranger should not edit post")

    repository.delete_post(post.id, moderator.id, False)
    removed = repository.discussion_detail(post.id)
    visible_feed = repository.list_community_feed("variant-voron-design-voron-2-4-voron-2-4-r2-350")

    assert removed is not None
    assert removed.post.deleted_at is not None
    assert removed.post.title == "Conteúdo removido"
    assert removed.comments
    assert all(item.id != post.id for item in visible_feed.items)

    with connect_database(database_path) as connection:
        history = connection.execute("SELECT action FROM social_discussion_edit_history ORDER BY id").fetchall()
    assert {row["action"] for row in history} >= {"created", "updated", "deleted", "solution_marked"}


def test_discussion_rejects_html_and_api_enforces_permissions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            peer = client.post("/api/auth/register", json={"email": "peer@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            peer_token = peer.json()["access_token"]
            printer = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"name": "Secret Voron", "moonraker_url": "http://secret-voron.local:7125", "host_audit_mode": "disabled"},
            ).json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"slug": "owner-public", "display_name": "Owner Public", "visibility": "public"},
            )
            client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Voron pública"},
            )
            blocked_html = client.post(
                "/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350/posts",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"content_type": "question", "title": "<script>alert(1)</script>", "body": "duvida"},
            )
            created = client.post(
                "/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350/posts",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"content_type": "question", "title": "Fluxo de ABS", "body": "Como melhorar fluxo?", "material": "ABS"},
            )
            post = next(item for item in created.json()["items"] if item["title"] == "Fluxo de ABS")
            comment = client.post(
                f"/api/social/posts/{post['id']}/comments",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"body": "Aumente temperatura em teste controlado."},
            )
            react = client.post(
                f"/api/social/posts/{post['id']}/reactions",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"reaction_type": "useful"},
            )
            solution = client.post(
                f"/api/social/posts/{post['id']}/solution?comment_id={comment.json()['id']}",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            forbidden = client.put(
                f"/api/social/posts/{post['id']}",
                headers={"Authorization": f"Bearer {peer_token}"},
                json={"title": "Nao autorizado"},
            )
            detail = client.get(f"/api/social/posts/{post['id']}/discussion", headers={"Authorization": f"Bearer {owner_token}"}).json()
            dumped = str(detail).lower()

            assert blocked_html.status_code == 422
            assert created.status_code == 200
            assert comment.status_code == 200
            assert react.status_code == 204
            assert solution.status_code == 200
            assert forbidden.status_code == 403
            assert detail["post"]["solution_comment_id"] == comment.json()["id"]
            assert detail["post"]["reaction_count"] == 1
            assert "secret-voron" not in dumped
            assert "moonraker" not in dumped
            assert "ssh" not in dumped
            assert "token" not in dumped
    finally:
        get_settings.cache_clear()


def test_library_items_visibility_catalog_links_and_downloads(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="peer@example.com", password="correct-horse"))
    stranger = auth.create_user(UserRegisterRequest(email="stranger@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    variant = _variant_id(database_path, "voron-2-4-r2-350")
    repository.update_profile(owner.id, PublicProfileUpdate(slug="owner-public", display_name="Owner", visibility="public"))
    repository.update_profile(peer.id, PublicProfileUpdate(slug="peer-public", display_name="Peer", visibility="public"))
    repository.get_or_create_profile(stranger.id)
    repository.set_relationship(owner.id, peer.id, "friend", "pending")
    repository.accept_friend(peer.id, owner.id)

    public_item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Stealthburner duct",
            description="Duto base para ABS.",
            visibility="community",
            community_slug="variant-voron-design-voron-2-4-voron-2-4-r2-350",
            catalog_variant_id=variant,
            component="toolhead",
            material_suggestion="ABS",
            supports_required=True,
            orientation_notes="Imprimir apoiado na face plana.",
            license="cc-by-sa",
            original_author_name="Owner",
            source_url="https://example.com/duct",
            attribution_text="Crédito ao Owner.",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="duct.stl", original_url="https://example.com/duct.stl", sha256="a" * 64)],
        ),
    )
    private_item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Calibracao privada",
            visibility="private",
            catalog_variant_id=variant,
            license="all-rights-reserved",
            files=[LibraryFileMetadata(file_kind="3mf", file_name="private.3mf")],
        ),
    )
    friend_item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Pacote para amigos",
            visibility="friends",
            license="custom",
            files=[LibraryFileMetadata(file_kind="bundle", file_name="bundle.zip")],
        ),
    )

    community_items = repository.list_library_for_community("variant-voron-design-voron-2-4-voron-2-4-r2-350")
    owner_items = repository.list_library_for_profile("owner-public", owner.id)
    peer_items = repository.list_library_for_profile("owner-public", peer.id)
    stranger_items = repository.list_library_for_profile("owner-public", stranger.id)
    downloaded = repository.register_library_download(public_item.id)

    assert [item.title for item in community_items] == ["Stealthburner duct"]
    assert {item.id for item in owner_items} >= {public_item.id, private_item.id, friend_item.id}
    assert friend_item.id in {item.id for item in peer_items}
    assert private_item.id not in {item.id for item in peer_items}
    assert friend_item.id not in {item.id for item in stranger_items}
    assert private_item.id not in {item.id for item in stranger_items}
    assert downloaded is not None and downloaded.download_count == 1
    assert downloaded.manufacturer_name == "Voron Design"
    assert downloaded.files[0].validation_status == "metadata_only"

    updated = repository.update_library_item(public_item.id, owner.id, False, LibraryItemUpdate(title="Stealthburner duct v2"))
    repository.archive_library_item(public_item.id, owner.id, False)

    assert updated.title == "Stealthburner duct v2"
    assert repository.library_item(public_item.id) is None

    try:
        repository.update_library_item(private_item.id, stranger.id, False, LibraryItemUpdate(title="Invasao"))
    except PermissionError as exc:
        assert "dono" in str(exc)
    else:
        raise AssertionError("stranger should not edit library item")


def test_library_api_contract_filters_private_items(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")
            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"slug": "owner-public", "display_name": "Owner Public", "visibility": "public"},
            )
            created_public = client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "title": "Fan shroud",
                    "description": "Arquivo base de fan shroud.",
                    "visibility": "community",
                    "community_slug": "variant-voron-design-voron-2-4-voron-2-4-r2-350",
                    "catalog_variant_id": variant,
                    "license": "cc-by",
                    "original_author_name": "Owner Public",
                    "source_url": "https://example.com/fan-shroud",
                    "attribution_text": "Crédito ao Owner Public.",
                    "publication_terms_accepted": True,
                    "files": [{"file_kind": "stl", "file_name": "fan-shroud.stl", "original_url": "https://example.com/fan-shroud.stl"}],
                },
            )
            client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "title": "Private fixture",
                    "visibility": "private",
                    "catalog_variant_id": variant,
                    "license": "custom",
                    "files": [{"file_kind": "3mf", "file_name": "private.3mf"}],
                },
            )

            community = client.get("/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350/library")
            profile = client.get("/api/social/profiles/owner-public/library")
            download = client.post(f"/api/social/library/{created_public.json()['id']}/downloads")
            blocked_name = client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "title": "Unsafe",
                    "visibility": "public",
                    "license": "cc0",
                    "original_author_name": "Owner Public",
                    "publication_terms_accepted": True,
                    "files": [{"file_kind": "stl", "file_name": "../unsafe.stl"}],
                },
            )
            dumped = str(community.json()).lower()

            assert created_public.status_code == 200
            assert community.status_code == 200
            assert profile.status_code == 200
            assert download.status_code == 200
            assert blocked_name.status_code == 422
            assert [item["title"] for item in community.json()] == ["Fan shroud"]
            assert [item["title"] for item in profile.json()] == ["Fan shroud"]
            assert download.json()["download_count"] == 1
            assert "private fixture" not in dumped
            assert "token" not in dumped
            assert "moonraker" not in dumped
    finally:
        get_settings.cache_clear()


def test_library_upload_quarantine_rejects_unsafe_zip_and_deduplicates(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.update_profile(owner.id, PublicProfileUpdate(slug="owner-public", display_name="Owner", visibility="public"))
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Upload real",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="placeholder.stl")],
        ),
    )

    valid_stl = b"solid test\n" + b"facet normal 0 0 1\n" + b"x" * 128
    uploaded = repository.upload_library_file(item.id, owner.id, False, "valid.stl", valid_stl)
    repeated = repository.upload_library_file(item.id, owner.id, False, "valid-copy.stl", valid_stl)
    unsafe_zip = BytesIO()
    with zipfile.ZipFile(unsafe_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../evil.stl", "solid bad")
    rejected = repository.upload_library_file(item.id, owner.id, False, "unsafe.zip", unsafe_zip.getvalue())

    upload_file = next(file for file in uploaded.files if file.file_name == "valid.stl")
    repeated_file = next(file for file in repeated.files if file.file_name == "valid-copy.stl")
    rejected_file = next(file for file in rejected.files if file.file_name == "unsafe.zip")

    assert upload_file.validation_status == "quarantined"
    assert upload_file.quarantine_key is not None
    assert upload_file.uploaded_size_bytes == len(valid_stl)
    assert repeated_file.deduplicated_from_file_id is not None
    assert rejected_file.validation_status == "rejected"
    assert "path perigoso" in (rejected_file.rejection_reason or "")
    assert (database_path.parent / "library_uploads" / "quarantine" / upload_file.quarantine_key).is_file()


def test_library_storage_quota_blocks_upload_before_writing_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="quota-owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.update_profile(owner.id, PublicProfileUpdate(slug="quota-owner", display_name="Quota owner", visibility="public"))
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Modelo com cota",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="placeholder.stl")],
        ),
    )
    with connect_database(database_path) as connection:
        connection.execute(
            """
            INSERT INTO social_file_storage_policies (
                scope_type, scope_id, quota_bytes, retention_days, cost_per_gb_month_cents
            )
            VALUES ('user', ?, 64, 180, 8)
            """,
            (owner.id,),
        )

    body = b"solid too-large\n" + b"x" * 128
    checksum = hashlib.sha256(body).hexdigest()
    with pytest.raises(ValueError, match="cota de armazenamento"):
        repository.upload_library_file(item.id, owner.id, False, "blocked.stl", body)

    assert not (database_path.parent / "library_uploads" / "quarantine" / f"{checksum}.stl").exists()


def test_library_storage_report_and_retention_review_are_supervised(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="storage-owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.update_profile(owner.id, PublicProfileUpdate(slug="storage-owner", display_name="Storage owner", visibility="public"))
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Modelo com retenção",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="placeholder.stl")],
        ),
    )
    uploaded = repository.upload_library_file(item.id, owner.id, False, "broken.stl", b"solid bad\n" + b"x" * 128)
    file_id = next(file.id for file in uploaded.files if file.file_name == "broken.stl")
    with connect_database(database_path) as connection:
        connection.execute("UPDATE social_library_files SET validation_status = 'analysis_failed' WHERE id = ?", (file_id,))

    storage = SocialStorageRepository(database_path)
    report = storage.report_for_user(owner.id)
    review = storage.create_retention_review(owner.id, owner.id)

    assert report.usage.used_bytes > 0
    assert report.usage.remaining_bytes < report.usage.quota_bytes
    assert report.retention.candidate_count == 1
    assert review.review_id is not None
    assert review.reclaimable_bytes > 0
    with connect_database(database_path) as connection:
        retained = connection.execute("SELECT validation_status FROM social_library_files WHERE id = ?", (file_id,)).fetchone()
        audit = connection.execute("SELECT candidate_count, reclaimable_bytes FROM social_file_retention_reviews WHERE id = ?", (review.review_id,)).fetchone()
    assert retained["validation_status"] == "analysis_failed"
    assert audit["candidate_count"] == 1
    assert audit["reclaimable_bytes"] == review.reclaimable_bytes


def test_library_upload_api_uses_raw_body_without_multipart(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            token = owner.json()["access_token"]
            created = client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": "Raw upload",
                    "visibility": "private",
                    "license": "custom",
                    "files": [{"file_kind": "stl", "file_name": "placeholder.stl"}],
                },
            ).json()
            response = client.post(
                f"/api/social/library/{created['id']}/files/upload?file_name=part.stl",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
                content=b"solid part\nfacet normal 0 0 1\n" + b"x" * 128,
            )
            oversized = client.post(
                f"/api/social/library/{created['id']}/files/upload?file_name=huge.stl",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
                content=b"x" * (25 * 1024 * 1024 + 1),
            )

            assert response.status_code == 200
            assert any(file["file_name"] == "part.stl" and file["validation_status"] == "quarantined" for file in response.json()["files"])
            assert oversized.status_code == 400
            assert "25 MB" in oversized.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_library_analysis_extracts_dimensions_thumbnail_and_warnings(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Analise STL",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="placeholder.stl")],
        ),
    )

    uploaded = repository.upload_library_file(item.id, owner.id, False, "box.stl", _binary_stl([(0, 0, 0), (20, 0, 0), (0, 30, 0), (0, 0, 80)]))
    file_id = next(file.id for file in uploaded.files if file.file_name == "box.stl")
    analyzed = repository.analyze_library_file(file_id or 0, owner.id, False)
    analyzed_file = next(file for file in analyzed.files if file.id == file_id)

    assert analyzed_file.validation_status == "analyzed"
    assert analyzed_file.analyzed_at is not None
    assert analyzed_file.analysis["dimensions_mm"] == {"x": 20.0, "y": 30.0, "z": 80.0}
    assert analyzed_file.analysis["triangle_count"] == 4
    assert analyzed_file.analysis["support_likely"] is True
    assert analyzed_file.thumbnail_svg and "<svg" in analyzed_file.thumbnail_svg
    assert any(problem["code"] == "support_likely" for problem in analyzed_file.analysis["problems"])


def test_library_analysis_failure_is_scoped_to_file(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Analise falha",
            visibility="private",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="placeholder.stl")],
        ),
    )

    uploaded = repository.upload_library_file(item.id, owner.id, False, "flat.stl", b"solid empty\nendsolid empty\n" + b"x" * 100)
    with connect_database(database_path) as connection:
        file_id = connection.execute("SELECT id FROM social_library_files WHERE file_name = 'flat.stl'").fetchone()["id"]
        connection.execute("UPDATE social_library_files SET validation_status = 'quarantined' WHERE id = ?", (file_id,))
    analyzed = repository.analyze_library_file(file_id, owner.id, False)
    failed_file = next(file for file in analyzed.files if file.id == file_id)

    assert failed_file.validation_status == "analysis_failed"
    assert failed_file.analysis["status"] == "failed"
    assert analyzed.id == item.id
    assert len(analyzed.files) >= 2


def test_library_publication_requires_author_terms_and_keeps_attribution(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)

    try:
        repository.create_library_item(
            owner.id,
            LibraryItemCreate(
                title="Sem autoria",
                visibility="public",
                license="cc-by",
                files=[LibraryFileMetadata(file_kind="stl", file_name="model.stl")],
            ),
        )
    except ValueError as exc:
        assert "autoria" in str(exc)
    else:
        raise AssertionError("public item without author should fail")

    created = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Com crédito",
            visibility="public",
            license="cc-by",
            original_author_name="Owner Maker",
            source_url="https://example.com/original",
            attribution_text="Modelo publicado por Owner Maker.",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="model.stl")],
        ),
    )

    assert created.original_author_name == "Owner Maker"
    assert created.source_url == "https://example.com/original"
    assert created.publication_terms_accepted_at is not None


def test_library_remix_references_origin_when_public(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    original = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Origem",
            visibility="public",
            license="cc-by-sa",
            original_author_name="Autor Original",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="origin.stl")],
        ),
    )
    remix = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Remix",
            visibility="public",
            license="cc-by-sa",
            original_author_name="Autor Remix",
            attribution_text="Derivado com crédito ao modelo original.",
            remix_source_item_id=original.id,
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="remix.stl")],
        ),
    )

    assert remix.remix_source_item_id == original.id
    assert remix.remix_source_title == "Origem"


def test_library_versions_are_immutable_and_can_be_promoted(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Modelo versionado",
            visibility="private",
            version_label="v1",
            license="custom",
            files=[LibraryFileMetadata(file_kind="stl", file_name="model-v1.stl", sha256="a" * 64)],
        ),
    )

    versioned = repository.create_library_version(
        item.id,
        owner.id,
        False,
        LibraryVersionCreate(
            version_label="v2",
            changelog="Ajusta encaixe do duto.",
            files=[LibraryFileMetadata(file_kind="stl", file_name="model-v2.stl", sha256="b" * 64)],
        ),
    )
    promoted = repository.promote_library_version(item.id, item.current_version_id or 0, owner.id, False)

    assert [version.version_label for version in versioned.versions] == ["v2", "v1"]
    assert versioned.version_label == "v2"
    assert versioned.versions[1].files[0].file_name == "model-v1.stl"
    assert promoted.version_label == "v1"
    assert promoted.files[0].file_name == "model-v1.stl"
    assert next(version for version in promoted.versions if version.version_label == "v1").is_current is True


def test_library_version_download_and_permissions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            stranger = client.post("/api/auth/register", json={"email": "stranger@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            stranger_token = stranger.json()["access_token"]
            created = client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "title": "Public versioned",
                    "visibility": "public",
                    "version_label": "v1",
                    "license": "cc-by",
                    "original_author_name": "Owner",
                    "publication_terms_accepted": True,
                    "files": [{"file_kind": "stl", "file_name": "model-v1.stl", "sha256": "a" * 64}],
                },
            ).json()
            version = client.post(
                f"/api/social/library/{created['id']}/versions",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "version_label": "v2",
                    "changelog": "Refina tolerância.",
                    "files": [{"file_kind": "stl", "file_name": "model-v2.stl", "sha256": "b" * 64}],
                },
            )
            forbidden = client.post(
                f"/api/social/library/{created['id']}/versions",
                headers={"Authorization": f"Bearer {stranger_token}"},
                json={
                    "version_label": "v3",
                    "changelog": "Invasão.",
                    "files": [{"file_kind": "stl", "file_name": "model-v3.stl"}],
                },
            )
            version_id = next(item["id"] for item in version.json()["versions"] if item["version_label"] == "v1")
            download = client.post(f"/api/social/library/{created['id']}/versions/{version_id}/downloads")

            assert version.status_code == 200
            assert forbidden.status_code == 403
            assert download.status_code == 200
            assert next(item for item in download.json()["versions"] if item["id"] == version_id)["download_count"] == 1
            assert next(item for item in download.json()["versions"] if item["version_label"] == "v1")["files"][0]["file_name"] == "model-v1.stl"
    finally:
        get_settings.cache_clear()


def test_library_organizer_keeps_private_collections_and_versioned_print_lists(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    stranger = auth.create_user(UserRegisterRequest(email="stranger@example.com", password="correct-horse"))
    printer = PrinterRepository(database_path, user_id=owner.id).create_printer(
        PrinterCreate(name="Voron lista", moonraker_url="http://voron.local:7125", host_audit_mode="disabled")
    )
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    repository.get_or_create_profile(stranger.id)
    item = repository.create_library_item(
        owner.id,
        LibraryItemCreate(
            title="Modelo para organizar",
            visibility="public",
            version_label="v1",
            license="cc-by",
            original_author_name="Owner",
            publication_terms_accepted=True,
            files=[LibraryFileMetadata(file_kind="stl", file_name="model-v1.stl")],
        ),
    )
    versioned = repository.create_library_version(
        item.id,
        owner.id,
        False,
        LibraryVersionCreate(
            version_label="v2",
            changelog="Ajuste final.",
            files=[LibraryFileMetadata(file_kind="stl", file_name="model-v2.stl")],
        ),
    )
    repository.set_library_favorite(item.id, owner.id, True)
    organizer = repository.create_library_collection(
        owner.id,
        LibraryCollectionCreate(name="Peças da Voron", visibility="private"),
    )
    collection_id = organizer.collections[0].id
    organizer = repository.add_library_collection_item(
        collection_id,
        owner.id,
        LibraryCollectionItemCreate(item_id=item.id, version_id=versioned.current_version_id, notes="Imprimir em ABS."),
    )
    organizer = repository.create_print_list(owner.id, PrintListCreate(name="Fila Voron", printer_id=printer.id))
    print_list_id = organizer.print_lists[0].id
    organizer = repository.add_print_list_item(
        print_list_id,
        owner.id,
        PrintListItemCreate(item_id=item.id, version_id=versioned.current_version_id or 0),
    )
    list_item_id = organizer.print_lists[0].items[0].id
    organizer = repository.update_print_list_item(list_item_id, owner.id, PrintListItemUpdate(status="printed", notes="Impresso sem suporte."))
    repository.register_library_download(item.id, owner.id, versioned.current_version_id)

    stranger_summary = repository.library_organizer(stranger.id)
    owner_summary = repository.library_organizer(owner.id)

    assert owner_summary.favorites[0].title == "Modelo para organizar"
    assert owner_summary.collections[0].item_count == 1
    assert owner_summary.print_lists[0].printer_id == printer.id
    assert owner_summary.print_lists[0].items[0].version_id == versioned.current_version_id
    assert owner_summary.print_lists[0].items[0].status == "printed"
    assert owner_summary.downloads[0].version_label == "v2"
    assert stranger_summary.collections == []
    assert stranger_summary.print_lists == []
    assert stranger_summary.favorites == []


def test_library_organizer_api_blocks_cross_user_collection_and_printer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            stranger = client.post("/api/auth/register", json={"email": "stranger@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            stranger_token = stranger.json()["access_token"]
            printer = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"name": "Voron API", "moonraker_url": "http://voron.local:7125", "host_audit_mode": "disabled"},
            )
            created = client.post(
                "/api/social/library",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "title": "Organizer API",
                    "visibility": "public",
                    "license": "cc-by",
                    "original_author_name": "Owner",
                    "publication_terms_accepted": True,
                    "files": [{"file_kind": "stl", "file_name": "model.stl"}],
                },
            ).json()
            collection = client.post(
                "/api/social/library/collections",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"name": "Privada", "visibility": "private"},
            ).json()["collections"][0]
            forbidden_collection = client.post(
                f"/api/social/library/collections/{collection['id']}/items",
                headers={"Authorization": f"Bearer {stranger_token}"},
                json={"item_id": created["id"], "version_id": created["current_version_id"]},
            )
            forbidden_printer = client.post(
                "/api/social/print-lists",
                headers={"Authorization": f"Bearer {stranger_token}"},
                json={"name": "Fila alheia", "printer_id": printer.json()["id"]},
            )
            favorite = client.post(
                f"/api/social/library/{created['id']}/favorite",
                headers={"Authorization": f"Bearer {stranger_token}"},
            )
            summary = client.get("/api/social/me/library/organizer", headers={"Authorization": f"Bearer {stranger_token}"})

            assert forbidden_collection.status_code == 403
            assert forbidden_printer.status_code == 400
            assert favorite.status_code == 200
            assert summary.status_code == 200
            assert summary.json()["favorites"][0]["id"] == created["id"]
            assert summary.json()["collections"] == []
    finally:
        get_settings.cache_clear()


def test_social_relationship_block_ends_follow_and_friendship(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="peer@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    repository.get_or_create_profile(peer.id)

    repository.set_relationship(owner.id, peer.id, "follow", "active")
    repository.set_relationship(owner.id, peer.id, "friend", "pending")
    repository.accept_friend(peer.id, owner.id)
    repository.set_relationship(owner.id, peer.id, "block", "active")

    summary = repository.relationship_summary(owner.id)
    peer_summary = repository.relationship_summary(peer.id)

    assert summary.following == []
    assert summary.friends == []
    assert summary.blocked[0].target_user_id == peer.id
    assert peer_summary.friends == []


def test_social_relationship_full_lifecycle_and_idempotency(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner@example.com", password="correct-horse"))
    peer = auth.create_user(UserRegisterRequest(email="peer@example.com", password="correct-horse"))
    third = auth.create_user(UserRegisterRequest(email="third@example.com", password="correct-horse"))
    repository = SocialCatalogRepository(database_path)
    repository.get_or_create_profile(owner.id)
    repository.get_or_create_profile(peer.id)
    repository.get_or_create_profile(third.id)

    repository.set_relationship(owner.id, peer.id, "follow", "active")
    repository.set_relationship(owner.id, peer.id, "follow", "active")
    assert [item.target_user_id for item in repository.relationship_summary(owner.id).following] == [peer.id]

    repository.set_relationship(owner.id, peer.id, "follow", "ended")
    repository.set_relationship(owner.id, peer.id, "follow", "ended")
    assert repository.relationship_summary(owner.id).following == []

    repository.set_relationship(owner.id, peer.id, "friend", "pending")
    assert repository.relationship_summary(peer.id).pending_friend_requests[0].target_user_id == owner.id
    assert repository.relationship_summary(owner.id).sent_friend_requests[0].target_user_id == peer.id
    repository.reject_friend(peer.id, owner.id)
    assert repository.relationship_summary(peer.id).pending_friend_requests == []

    repository.set_relationship(owner.id, peer.id, "friend", "pending")
    repository.cancel_friend_request(owner.id, peer.id)
    assert repository.relationship_summary(owner.id).sent_friend_requests == []

    repository.set_relationship(owner.id, peer.id, "friend", "pending")
    repository.accept_friend(peer.id, owner.id)
    assert repository.relationship_summary(owner.id).friends[0].target_user_id == peer.id
    assert repository.relationship_summary(peer.id).friends[0].target_user_id == owner.id
    repository.unfriend(owner.id, peer.id)
    assert repository.relationship_summary(owner.id).friends == []
    assert repository.relationship_summary(peer.id).friends == []

    try:
        repository.set_relationship(owner.id, owner.id, "follow", "active")
    except ValueError as exc:
        assert "consigo" in str(exc)
    else:
        raise AssertionError("self relationship should fail")

    repository.set_relationship(owner.id, third.id, "block", "active")
    try:
        repository.set_relationship(third.id, owner.id, "friend", "pending")
    except PermissionError as exc:
        assert "bloqueio social" in str(exc)
    else:
        raise AssertionError("blocked user should not create social relationship")
    repository.set_relationship(owner.id, third.id, "block", "ended")
    assert repository.relationship_summary(owner.id).blocked == []
    assert repository.relationship_summary(owner.id).friends == []

    with connect_database(database_path) as connection:
        audit_rows = connection.execute(
            "SELECT payload_json FROM catalog_audit_events WHERE entity_type = 'social_relationship'"
        ).fetchall()
    dumped = " ".join(str(row["payload_json"]).lower() for row in audit_rows)
    assert audit_rows
    assert "owner@example.com" not in dumped
    assert "peer@example.com" not in dumped
    assert "password" not in dumped


def test_social_relationship_api_reject_cancel_unfriend_and_blocks_sensitive_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            peer = client.post("/api/auth/register", json={"email": "peer@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            peer_token = peer.json()["access_token"]
            owner_id = owner.json()["user"]["id"]
            peer_id = peer.json()["user"]["id"]

            profile_owner = client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"slug": "owner-public", "display_name": "Owner Public", "visibility": "public"},
            )
            profile_peer = client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {peer_token}"},
                json={"slug": "peer-public", "display_name": "Peer Public", "visibility": "public"},
            )
            follow = client.post(f"/api/social/relationships/{peer_id}/follow", headers={"Authorization": f"Bearer {owner_token}"})
            unfollow = client.delete(f"/api/social/relationships/{peer_id}/follow", headers={"Authorization": f"Bearer {owner_token}"})
            request = client.post(f"/api/social/relationships/{peer_id}/friend-request", headers={"Authorization": f"Bearer {owner_token}"})
            reject = client.post(f"/api/social/relationships/{owner_id}/friend-reject", headers={"Authorization": f"Bearer {peer_token}"})
            request_again = client.post(f"/api/social/relationships/{peer_id}/friend-request", headers={"Authorization": f"Bearer {owner_token}"})
            cancel = client.delete(f"/api/social/relationships/{peer_id}/friend-request", headers={"Authorization": f"Bearer {owner_token}"})
            request_final = client.post(f"/api/social/relationships/{peer_id}/friend-request", headers={"Authorization": f"Bearer {owner_token}"})
            accept = client.post(f"/api/social/relationships/{owner_id}/friend-accept", headers={"Authorization": f"Bearer {peer_token}"})
            unfriend = client.delete(f"/api/social/relationships/{peer_id}/friend", headers={"Authorization": f"Bearer {owner_token}"})
            self_follow = client.post(f"/api/social/relationships/{owner_id}/follow", headers={"Authorization": f"Bearer {owner_token}"})
            block = client.post(f"/api/social/relationships/{peer_id}/block", headers={"Authorization": f"Bearer {owner_token}"})
            blocked_request = client.post(f"/api/social/relationships/{owner_id}/friend-request", headers={"Authorization": f"Bearer {peer_token}"})
            unblock = client.delete(f"/api/social/relationships/{peer_id}/block", headers={"Authorization": f"Bearer {owner_token}"})
            summary = client.get("/api/social/me/relationships", headers={"Authorization": f"Bearer {owner_token}"}).json()

            assert profile_owner.status_code == 200
            assert profile_peer.status_code == 200
            assert follow.status_code == 200
            assert unfollow.status_code == 204
            assert request.status_code == 200
            assert reject.status_code == 204
            assert request_again.status_code == 200
            assert cancel.status_code == 204
            assert request_final.status_code == 200
            assert accept.status_code == 200
            assert unfriend.status_code == 204
            assert self_follow.status_code == 400
            assert block.status_code == 200
            assert blocked_request.status_code == 403
            assert unblock.status_code == 204
            assert summary["friends"] == []
            assert summary["blocked"] == []
            dumped = str(summary).lower()
            assert "owner@example.com" not in dumped
            assert "peer@example.com" not in dumped
            assert "whatsapp" not in dumped
            assert "permission" not in dumped
    finally:
        get_settings.cache_clear()


def test_social_profile_discovery_visibility_blocking_and_operational_isolation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correct-horse"})
            peer = client.post("/api/auth/register", json={"email": "peer@example.com", "password": "correct-horse"})
            owner_token = owner.json()["access_token"]
            peer_token = peer.json()["access_token"]
            owner_id = owner.json()["user"]["id"]
            peer_id = peer.json()["user"]["id"]
            printer = client.post(
                "/api/printers",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"name": "Secret Voron", "moonraker_url": "http://secret-voron.local:7125", "host_audit_mode": "disabled"},
            ).json()
            variant = _variant_id(tmp_path / "printora.db", "voron-2-4-r2-350")

            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"slug": "owner-public", "display_name": "Owner Public", "visibility": "public"},
            )
            client.put(
                "/api/social/me/profile",
                headers={"Authorization": f"Bearer {peer_token}"},
                json={"slug": "peer-unlisted", "display_name": "Peer Hidden", "visibility": "unlisted"},
            )
            client.put(
                f"/api/printers/{printer['id']}/public-profile",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"public_profile_enabled": True, "catalog_variant_id": variant, "public_name": "Voron pública"},
            )

            public_search = client.get("/api/social/profiles?q=owner").json()
            public_directory = client.get("/api/social/profiles").json()
            unlisted_exact = client.get("/api/social/profiles?q=peer-unlisted").json()
            unlisted_name = client.get("/api/social/profiles?q=hidden").json()
            operational_blocked = client.get(f"/api/printers/{printer['id']}", headers={"Authorization": f"Bearer {peer_token}"})
            client.post(f"/api/social/relationships/{peer_id}/block", headers={"Authorization": f"Bearer {owner_token}"})
            blocked_search = client.get("/api/social/profiles?q=owner", headers={"Authorization": f"Bearer {peer_token}"}).json()
            blocked_profile = client.get("/api/social/profiles/owner-public", headers={"Authorization": f"Bearer {peer_token}"})
            blocked_printers = client.get("/api/social/printers?manufacturer=Voron", headers={"Authorization": f"Bearer {peer_token}"}).json()
            client.delete(f"/api/social/relationships/{peer_id}/block", headers={"Authorization": f"Bearer {owner_token}"})
            after_unblock = client.get("/api/social/profiles/owner-public", headers={"Authorization": f"Bearer {peer_token}"})
            summary = client.get("/api/social/me/relationships", headers={"Authorization": f"Bearer {owner_token}"}).json()

            assert any(item["slug"] == "owner-public" for item in public_search)
            assert any(item["slug"] == "owner-public" and item["public_printer_count"] == 1 for item in public_directory)
            assert all(item["slug"] != "peer-unlisted" for item in public_directory)
            assert [item["slug"] for item in unlisted_exact] == ["peer-unlisted"]
            assert all(item["slug"] != "peer-unlisted" for item in unlisted_name)
            assert operational_blocked.status_code == 404
            assert blocked_search == []
            assert blocked_profile.status_code == 403
            assert blocked_printers == []
            assert after_unblock.status_code == 200
            assert summary["friends"] == []
            assert summary["following"] == []
            assert "moonraker" not in str(public_search).lower()
            assert "owner@example.com" not in str(public_search)
            assert owner_id != peer_id
    finally:
        get_settings.cache_clear()


def test_social_safety_settings_hide_profile_from_discovery_but_keep_direct_url(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    user = auth.create_user(UserRegisterRequest(email="safe-maker@example.com", password="correct-horse", display_name="Safe Maker"))
    social = SocialCatalogRepository(database_path)
    safety = SocialSafetyRepository(database_path)

    social.update_profile(user.id, PublicProfileUpdate(slug="safe-maker", display_name="Safe Maker", visibility="public"))
    visible = social.search_profiles("safe")
    updated = safety.update_settings(
        user.id,
        SocialSafetySettingsUpdate(
            profile_discoverable=False,
            followers_visibility="friends",
            messages_from="none",
            allow_content_mentions=False,
            allow_download_tracking=False,
        ),
    )
    hidden_by_name = social.search_profiles("safe")
    direct_lookup = social.search_profiles("safe-maker")
    public_profile = social.public_profile_by_slug("safe-maker")

    assert [item.slug for item in visible] == ["safe-maker"]
    assert hidden_by_name == []
    assert [item.slug for item in direct_lookup] == ["safe-maker"]
    assert public_profile is not None
    assert public_profile.slug == "safe-maker"
    assert updated.profile_discoverable is False
    assert updated.followers_visibility == "friends"
    assert updated.messages_from == "none"


def test_social_safety_rate_limit_creates_actionable_abuse_signal(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    actor = auth.create_user(UserRegisterRequest(email="limit-actor@example.com", password="correct-horse"))
    target = auth.create_user(UserRegisterRequest(email="limit-target@example.com", password="correct-horse"))
    safety = SocialSafetyRepository(database_path)

    allowed = [
        safety.check_rate_limit(
            actor_user_id=actor.id,
            action="moderation_report",
            subject=f"user:{actor.id}:report:{index}",
            target_user_id=target.id,
        )
        for index in range(10)
    ]
    blocked = safety.check_rate_limit(
        actor_user_id=actor.id,
        action="moderation_report",
        subject=f"user:{actor.id}:report:blocked",
        target_user_id=target.id,
    )
    signals = safety.abuse_signals(status="active")

    assert all(item.allowed for item in allowed)
    assert blocked.allowed is False
    assert blocked.retry_after_seconds == 3600
    assert signals
    assert signals[0].subject_user_id == actor.id
    assert signals[0].target_user_id == target.id
    assert signals[0].action == "moderation_report"
    assert "limit-actor@example.com" not in signals[0].model_dump_json()
    assert "limit-target@example.com" not in signals[0].model_dump_json()
    with connect_database(database_path) as connection:
        audit_payloads = connection.execute("SELECT payload_json FROM catalog_audit_events WHERE entity_type = 'social_safety'").fetchall()
    assert audit_payloads
    assert "limit-actor@example.com" not in str(audit_payloads)


def test_social_safety_api_controls_and_admin_abuse_queue(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            admin = client.post("/api/auth/register", json={"email": "breno@mayder.com.br", "password": "correct-horse"})
            user = client.post("/api/auth/register", json={"email": "safety-user@example.com", "password": "correct-horse"})
            admin_token = admin.json()["access_token"]
            user_token = user.json()["access_token"]
            user_id = user.json()["user"]["id"]

            initial = client.get("/api/social/me/safety", headers={"Authorization": f"Bearer {user_token}"})
            update = client.put(
                "/api/social/me/safety",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "profile_discoverable": False,
                    "followers_visibility": "private",
                    "messages_from": "none",
                    "allow_content_mentions": False,
                    "allow_download_tracking": False,
                },
            )
            safety = SocialSafetyRepository(tmp_path / "printora.db")
            for index in range(11):
                safety.check_rate_limit(
                    actor_user_id=user_id,
                    action="moderation_report",
                    subject=f"user:{user_id}:api:{index}",
                    target_user_id=None,
                )
            user_queue = client.get("/api/social/moderation/abuse-signals", headers={"Authorization": f"Bearer {user_token}"})
            admin_queue = client.get("/api/social/moderation/abuse-signals", headers={"Authorization": f"Bearer {admin_token}"})

            assert initial.status_code == 200
            assert initial.json()["settings"]["profile_discoverable"] is True
            assert update.status_code == 200
            assert update.json()["messages_from"] == "none"
            assert user_queue.status_code == 403
            assert admin_queue.status_code == 200
            dumped = str(admin_queue.json()).lower()
            assert "safety-user@example.com" not in dumped
            assert "password" not in dumped
            assert "token" not in dumped
    finally:
        get_settings.cache_clear()


def test_social_safety_limits_anonymous_profile_enumeration_across_queries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            statuses = [client.get(f"/api/social/profiles?q=unknown-{index}").status_code for index in range(31)]
            admin = client.post("/api/auth/register", json={"email": "breno@mayder.com.br", "password": "correct-horse"})
            admin_token = admin.json()["access_token"]
            signals = client.get("/api/social/moderation/abuse-signals", headers={"Authorization": f"Bearer {admin_token}"})

            assert statuses[:30] == [200] * 30
            assert statuses[30] == 429
            assert signals.status_code == 200
            assert signals.json()[0]["subject_user_id"] is None
            dumped = str(signals.json()).lower()
            assert "127.0.0.1" not in dumped
            assert "unknown-30" not in dumped
    finally:
        get_settings.cache_clear()


def test_social_moderation_reports_hide_restore_and_audit_post(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    admin = auth.create_user(UserRegisterRequest(email="breno@mayder.com.br", password="correct-horse", display_name="Moderador"))
    reporter = auth.create_user(UserRegisterRequest(email="reporter@example.com", password="correct-horse", display_name="Reporter"))
    author = auth.create_user(UserRegisterRequest(email="author@example.com", password="correct-horse", display_name="Author"))
    social = SocialCatalogRepository(database_path)
    social.update_profile(author.id, PublicProfileUpdate(slug="author", display_name="Author", visibility="public"))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]
    post = social.create_community_post(
        community.slug,
        author.id,
        CommunityPostCreate(
            content_type="question",
            title="Orientação perigosa",
            body="Conteúdo reportado para moderação técnica.",
            component="hotend",
        ),
    )
    moderation = SocialModerationRepository(database_path)

    report = moderation.create_report(
        reporter.id,
        ModerationReportCreate(entity_type="post", entity_id=post.id, reason="unsafe", detail="Recomendação insegura para iniciantes."),
    )
    queued = moderation.queue()
    hidden = moderation.apply_action(report.id, admin.id, ModerationActionPayload(action="hide", reason="Ocultação preventiva durante revisão técnica"))
    feed_after_hide = social.list_community_feed(community.slug)
    restored = moderation.apply_action(report.id, admin.id, ModerationActionPayload(action="restore", reason="Conteúdo ajustado e restaurado"))
    feed_after_restore = social.list_community_feed(community.slug)

    assert queued.reports[0].id == report.id
    assert hidden.status == "resolved"
    assert hidden.entity_status == "removed"
    assert all(item.id != post.id for item in feed_after_hide.items)
    assert restored.entity_status == "public"
    assert any(item.id == post.id for item in feed_after_restore.items)
    with connect_database(database_path) as connection:
        actions = connection.execute("SELECT action, reason FROM social_moderation_actions WHERE report_id = ? ORDER BY id", (report.id,)).fetchall()
        audits = connection.execute("SELECT action FROM catalog_audit_events WHERE entity_type = 'social_moderation_post' AND entity_id = ?", (post.id,)).fetchall()
    assert [row["action"] for row in actions] == ["hide", "restore"]
    assert [row["action"] for row in audits] == ["report", "hide", "restore"]


def test_social_moderation_queue_is_admin_only_and_curates_tags(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            admin_response = client.post(
                "/api/auth/register",
                json={"email": "breno@mayder.com.br", "password": "correct-horse", "display_name": "Moderador"},
            )
            user_response = client.post(
                "/api/auth/register",
                json={"email": "maker@example.com", "password": "correct-horse", "display_name": "Maker"},
            )
            admin_token = admin_response.json()["access_token"]
            user_token = user_response.json()["access_token"]
            with connect_database(tmp_path / "printora.db") as connection:
                cursor = connection.execute("INSERT INTO social_content_tags (slug, label, source) VALUES ('unsafe-tag', 'Unsafe Tag', 'user')")
                tag_id = int(cursor.lastrowid)

            report_response = client.post(
                "/api/social/reports",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"entity_type": "tag", "entity_id": tag_id, "reason": "wrong_metadata", "detail": "Tag incorreta para o catálogo."},
            )
            user_queue = client.get("/api/social/moderation/queue", headers={"Authorization": f"Bearer {user_token}"})
            admin_queue = client.get("/api/social/moderation/queue", headers={"Authorization": f"Bearer {admin_token}"})
            action_response = client.post(
                f"/api/social/moderation/reports/{report_response.json()['id']}/actions",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"action": "block", "reason": "Tag bloqueada por curadoria de metadados"},
            )

            assert report_response.status_code == 200
            assert user_queue.status_code == 403
            assert admin_queue.status_code == 200
            assert admin_queue.json()["reports"][0]["entity_type"] == "tag"
            assert action_response.status_code == 200
            assert action_response.json()["entity_status"] == "blocked"
            with connect_database(tmp_path / "printora.db") as connection:
                tag = connection.execute("SELECT status, source FROM social_content_tags WHERE id = ?", (tag_id,)).fetchone()
            assert dict(tag) == {"status": "blocked", "source": "curation"}
    finally:
        get_settings.cache_clear()


def test_social_notifications_follow_preferences_and_blocking(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    auth = AuthRepository(database_path)
    owner = auth.create_user(UserRegisterRequest(email="owner-notify@example.com", password="correct-horse", display_name="Owner"))
    watcher = auth.create_user(UserRegisterRequest(email="watcher@example.com", password="correct-horse", display_name="Watcher"))
    blocked = auth.create_user(UserRegisterRequest(email="blocked-notify@example.com", password="correct-horse", display_name="Blocked"))
    social = SocialCatalogRepository(database_path)
    social.update_profile(owner.id, PublicProfileUpdate(slug="owner-notify", display_name="Owner", visibility="public"))
    social.update_profile(watcher.id, PublicProfileUpdate(slug="watcher", display_name="Watcher", visibility="public"))
    community = social.list_communities(variant="voron-2-4-r2-350")[0]
    post = social.create_community_post(
        community.slug,
        owner.id,
        CommunityPostCreate(content_type="question", title="Ajuste de ABS", body="Qual perfil técnico usar?", material="ABS"),
    )
    notifications = SocialNotificationsRepository(database_path)

    follow = notifications.follow_content(watcher.id, ContentFollowPayload(entity_type="post", entity_id=post.id))
    notifications.notify_content_followers(
        actor_user_id=owner.id,
        entity_type="post",
        entity_id=post.id,
        notification_type="comment",
        title="Nova resposta",
        body="Há uma nova resposta técnica.",
        action_url="/?section=social",
    )
    center = notifications.notification_center(watcher.id)
    read = notifications.mark_read(watcher.id, center.notifications[0].id)
    notifications.update_preference(watcher.id, NotificationPreferenceUpdate(notification_type="comment", in_app_enabled=False, digest_enabled=True))
    notifications.notify_content_followers(
        actor_user_id=owner.id,
        entity_type="post",
        entity_id=post.id,
        notification_type="comment",
        title="Resposta silenciada",
        body="Esta notificação não deve entrar.",
        action_url="/?section=social",
    )
    muted_center = notifications.notification_center(watcher.id)
    social.set_relationship(watcher.id, blocked.id, "block", "active")
    notifications.create_notification(
        watcher.id,
        actor_user_id=blocked.id,
        notification_type="follow",
        entity_type="relationship",
        entity_id=blocked.id,
        title="Bloqueado",
        body="Não deve notificar.",
        action_url="/?section=social",
    )
    after_block = notifications.notification_center(watcher.id)

    assert follow.title == "Ajuste de ABS"
    assert center.unread_count == 1
    assert center.notifications[0].notification_type == "comment"
    assert read.status == "read"
    assert muted_center.unread_count == 0
    assert len(muted_center.notifications) == 1
    assert after_block.notifications == muted_center.notifications


def test_social_notification_routes_emit_relationship_and_comment_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            owner = client.post("/api/auth/register", json={"email": "notify-owner@example.com", "password": "correct-horse", "display_name": "Owner"}).json()
            peer = client.post("/api/auth/register", json={"email": "notify-peer@example.com", "password": "correct-horse", "display_name": "Peer"}).json()
            owner_token = owner["access_token"]
            peer_token = peer["access_token"]
            owner_id = owner["user"]["id"]
            peer_id = peer["user"]["id"]
            slug = SocialCatalogRepository(tmp_path / "printora.db").list_communities(variant="voron-2-4-r2-350")[0].slug
            post_feed = client.post(
                f"/api/social/communities/{slug}/posts",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"content_type": "question", "title": "Resposta notificada", "body": "Como ajustar fluxo?"},
            ).json()
            post_id = next(item["id"] for item in post_feed["items"] if item["title"] == "Resposta notificada")
            client.post(
                "/api/social/content-follows",
                headers={"Authorization": f"Bearer {peer_token}"},
                json={"entity_type": "post", "entity_id": post_id},
            )
            comment = client.post(
                f"/api/social/posts/{post_id}/comments",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"body": "Resposta técnica com contexto."},
            )
            follow = client.post(f"/api/social/relationships/{peer_id}/follow", headers={"Authorization": f"Bearer {owner_token}"})
            peer_center = client.get("/api/social/notifications", headers={"Authorization": f"Bearer {peer_token}"}).json()
            owner_center = client.get("/api/social/notifications", headers={"Authorization": f"Bearer {owner_token}"}).json()
            mark_all = client.post("/api/social/notifications/read-all", headers={"Authorization": f"Bearer {peer_token}"})
            after_read = client.get("/api/social/notifications", headers={"Authorization": f"Bearer {peer_token}"}).json()

            assert comment.status_code == 200
            assert follow.status_code == 200
            assert any(item["notification_type"] == "comment" for item in peer_center["notifications"])
            assert any(item["notification_type"] == "follow" for item in peer_center["notifications"])
            assert mark_all.status_code == 204
            assert after_read["unread_count"] == 0
            assert "moonraker" not in str(peer_center).lower()
            assert "notify-peer@example.com" not in str(owner_center)
    finally:
        get_settings.cache_clear()


def _variant_id(database_path: Path, slug: str) -> int:
    with connect_database(database_path) as connection:
        row = connection.execute("SELECT id FROM catalog_printer_variants WHERE slug = ?", (slug,)).fetchone()
    assert row is not None
    return int(row["id"])


def _binary_stl(points: list[tuple[float, float, float]]) -> bytes:
    triangles = [
        (points[0], points[1], points[2]),
        (points[0], points[1], points[3]),
        (points[0], points[2], points[3]),
        (points[1], points[2], points[3]),
    ]
    payload = bytearray(b"Printora test STL".ljust(80, b"\0"))
    payload.extend(struct.pack("<I", len(triangles)))
    for triangle in triangles:
        payload.extend(struct.pack("<fff", 0.0, 0.0, 1.0))
        for vertex in triangle:
            payload.extend(struct.pack("<fff", *vertex))
        payload.extend(struct.pack("<H", 0))
    return bytes(payload)
