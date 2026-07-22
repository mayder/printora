from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.routes import audit, auth


MODULE = ModuleDefinition(
    key="identity",
    owner="Identidade e permissões",
    contract_version="1.0.0",
    routers=(
        RouterRegistration(10, audit.router),
        RouterRegistration(30, auth.router),
    ),
)
