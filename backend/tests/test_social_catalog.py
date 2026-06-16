from pathlib import Path
from io import BytesIO
import struct
import zipfile

from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.printers import PrinterCreate, PrinterRepository
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

from app.social_catalog import CatalogVariantUpdate, CommunityFeedCreate, CommunityPostCreate, CommunityPostUpdate, DiscussionCommentCreate, DiscussionCommentUpdate, LibraryFileMetadata, LibraryItemCreate, LibraryItemUpdate, PrinterPublicUpdate, PublicProfileUpdate, SocialCatalogRepository


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
                headers={"Authorization": f"Bearer {token}"},
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
