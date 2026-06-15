from pathlib import Path

from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

from app.social_catalog import CatalogVariantUpdate, PrinterPublicUpdate, PublicProfileUpdate, SocialCatalogRepository


def test_catalog_seed_has_voron_models_and_variants(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).list_catalog()

    manufacturer = next(item for item in catalog.manufacturers if item.slug == "voron-design")
    model_slugs = {item.slug for item in manufacturer.models}
    variant_names = {variant.name for model in manufacturer.models for variant in model.variants}

    assert {"voron-0-2", "voron-2-4"}.issubset(model_slugs)
    assert "Voron 2.4 R2 350mm" in variant_names


def test_catalog_seed_has_broad_diy_klipper_catalog(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    catalog = SocialCatalogRepository(database_path).list_catalog()

    manufacturer_slugs = {item.slug for item in catalog.manufacturers}
    variant_names = {variant.name for manufacturer in catalog.manufacturers for model in manufacturer.models for variant in model.variants}
    variant_states = {variant.name: variant.trust_state for manufacturer in catalog.manufacturers for model in manufacturer.models for variant in model.variants}

    assert {"voron-design", "rat-rig", "vzbot", "annex-engineering", "hevort", "jubilee", "printers-for-ants"}.issubset(manufacturer_slugs)
    assert {"RatRig V-Core 3 400mm", "VzBot 330", "Annex K3 180mm", "Micron+ 180mm", "Salad Fork 160mm"}.issubset(variant_names)
    assert variant_states["HevORT 500 draft"] == "draft"
    assert variant_states["Jubilee Toolchanger draft"] == "draft"


def test_catalog_admin_search_filters_component_kinematics_firmware_and_state(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SocialCatalogRepository(database_path)

    corexy = repository.search_catalog_admin(component="Stealthburner", kinematics="corexy", firmware_family="klipper", trust_state="official")
    drafts = repository.search_catalog_admin(trust_state="draft")

    assert any(item.manufacturer_slug == "voron-design" and item.model_slug == "voron-2-4" for item in corexy.variants)
    assert {item.trust_state for item in drafts.variants} == {"draft"}
    assert {"hevort", "jubilee"}.issubset({item.manufacturer_slug for item in drafts.variants})


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
    variant = repository.list_catalog().manufacturers[0].models[0].variants[0]

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


def test_catalog_admin_api_blocks_common_user_and_allows_admin_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            common = client.post("/api/auth/register", json={"email": "user@example.com", "password": "correct-horse"})
            admin = client.post("/api/auth/register", json={"email": "breno@mayder.com.br", "password": "correct-horse"})
            common_token = common.json()["access_token"]
            admin_token = admin.json()["access_token"]

            blocked = client.get("/api/catalog/admin", headers={"Authorization": f"Bearer {common_token}"})
            allowed = client.get("/api/catalog/admin", headers={"Authorization": f"Bearer {admin_token}"})
            variant_id = allowed.json()["variants"][0]["id"]
            updated = client.put(
                f"/api/catalog/variants/{variant_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"trust_state": "community", "source": "admin_review"},
            )

            assert blocked.status_code == 403
            assert allowed.status_code == 200
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
