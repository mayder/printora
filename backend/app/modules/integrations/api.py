from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.routes import plugins


MODULE = ModuleDefinition(
    key="integrations",
    owner="Integrações",
    contract_version="1.0.0",
    routers=(RouterRegistration(120, plugins.router),),
)
