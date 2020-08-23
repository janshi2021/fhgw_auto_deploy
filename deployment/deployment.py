from .base import Deployment
from .utils import ToolLock
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

    def _get_lock_name(self, kwargs):
        return "LOCK_" + kwargs["pxe_info"]["host"]

    def __init__(self, **kwargs):
        super(ISODeployment, self).__init__(**kwargs)
        logger = kwargs.get("logger")
        self.tool_lock = ToolLock(self._get_lock_name(kwargs))
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
        self._logger.info("start to acquire lock ...")
        self.tool_lock.lock()
        self._logger.info("lock acquired, let's go ...")

    def teardown(self):
        self.tool_lock.unlock()