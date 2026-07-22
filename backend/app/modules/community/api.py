from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.routes import (
    external_library,
    print_profiles,
    print_projects,
    search_discovery,
    social_catalog,
    social_moderation,
    social_notifications,
    social_ranking,
    social_safety,
    social_storage,
)


MODULE = ModuleDefinition(
    key="community",
    owner="Comunidade e projetos",
    contract_version="1.0.0",
    routers=(
        RouterRegistration(80, external_library.router),
        RouterRegistration(130, print_profiles.router),
        RouterRegistration(140, print_projects.router),
        RouterRegistration(180, search_discovery.router),
        RouterRegistration(220, social_catalog.router),
        RouterRegistration(230, social_moderation.router),
        RouterRegistration(240, social_notifications.router),
        RouterRegistration(250, social_ranking.router),
        RouterRegistration(260, social_safety.router),
        RouterRegistration(270, social_storage.router),
    ),
)
