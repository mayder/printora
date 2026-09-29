from app.modules.accessibility.routes import router
from app.modules.assembly import ModuleDefinition, RouterRegistration


MODULE = ModuleDefinition(
    key="accessibility",
    owner="Accessibility",
    contract_version="1.0.0",
    routers=(RouterRegistration(325, router),),
)

