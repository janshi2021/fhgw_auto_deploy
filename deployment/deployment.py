from .base import Deployment
from .step import (PXEConnection,
                   FHGWConnection,
                   FHGWParamInitialize,
                   FHGWVersionCheck,
                   FHGWISOPreparation,
                   PXERestartDockerIfFHGWSessionFailed,
                   PXEModifyUserConfig,
                   PXEDockerExist,
                   PXERemoveExistDocker,
                   PXEInstallNewDocker,
                   TriggerFHGWStartInstallation,
                   ClearFirewallAndStopRelatedSerices,
                   )


class ISODeployment(Deployment):
    def __init__(self, **kwargs):
        super(ISODeployment, self).__init__(**kwargs)
        logger = kwargs.get("logger")
        self._steps = [
            FHGWParamInitialize(logger),
            PXEConnection(logger),
            FHGWConnection(logger),
            FHGWVersionCheck(logger),
            FHGWISOPreparation(logger),
            PXEModifyUserConfig(logger),
            PXEDockerExist(logger),
            PXERemoveExistDocker(logger),
            ClearFirewallAndStopRelatedSerices(logger),
            PXEInstallNewDocker(logger),
            PXERestartDockerIfFHGWSessionFailed(logger),
            TriggerFHGWStartInstallation(logger)
        ]

    def setup(self):
        pass

    def teardown(self):
        pass