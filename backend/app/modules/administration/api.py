from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.routes import backups, frontend, reports, snapshots, system, technical_profiles


MODULE = ModuleDefinition(
    key="administration",
    owner="Administração",
    contract_version="1.0.0",
    routers=(
        RouterRegistration(40, backups.router),
        RouterRegistration(170, reports.router),
        RouterRegistration(210, snapshots.router),
        RouterRegistration(290, system.router),
        RouterRegistration(300, technical_profiles.router),
        RouterRegistration(320, frontend.router),
    ),
)
