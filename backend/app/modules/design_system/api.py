from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.modules.design_system.routes import router


MODULE = ModuleDefinition(
    key="design_system",
    owner="Design system",
    contract_version="1.0.0",
    routers=(RouterRegistration(320, router),),
)
