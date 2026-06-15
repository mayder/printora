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


def _variant_id(database_path: Path, slug: str) -> int:
    with connect_database(database_path) as connection:
        row = connection.execute("SELECT id FROM catalog_printer_variants WHERE slug = ?", (slug,)).fetchone()
    assert row is not None
    return int(row["id"])
