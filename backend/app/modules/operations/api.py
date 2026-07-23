from app.modules.assembly import ModuleDefinition, RouterRegistration
from app.routes import (
    agents,
    calibration,
    can_monitor,
    checklists,
    firmware,
    maintenance,
    operation,
    printer_updates,
    printers,
    setup,
    slicing,
    z_offset,
)
from app.modules.operations import manufacturing_api


MODULE = ModuleDefinition(
    key="operations",
    owner="Operação e agentes",
    contract_version="1.0.0",
    routers=(
        RouterRegistration(20, agents.router),
        RouterRegistration(50, calibration.router),
        RouterRegistration(60, can_monitor.router),
        RouterRegistration(70, checklists.router),
        RouterRegistration(90, firmware.router),
        RouterRegistration(100, maintenance.router),
        RouterRegistration(110, operation.router),
        RouterRegistration(150, printer_updates.router),
        RouterRegistration(160, printers.router),
        RouterRegistration(190, setup.router),
        RouterRegistration(200, slicing.router),
        RouterRegistration(310, z_offset.router),
        RouterRegistration(550, manufacturing_api.router),
    ),
)
