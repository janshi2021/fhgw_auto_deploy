from abc import ABCMeta, abstractmethod
import six
import logging
from .operator import PXEServerOperator, FHGWOperator
from .exceptions import ExecutionException


@six.add_metaclass(ABCMeta)
class Deployment(object):

    def __init__(self, **kwargs):
        self._steps = []
        self._logger = kwargs.get("logger", logging)
        self._global_params = {}
        pxe_server = kwargs.get("pxe_info")
        fhgw_info = kwargs.get("fhgw_info")
        bmc_info = kwargs.get("bmc_info")
        pxe_operator = PXEServerOperator(host=pxe_server["host"],
                                         username=pxe_server["username"],
                                         password=pxe_server["password"],
                                         **kwargs)
        fhgw_operator = FHGWOperator(host=fhgw_info["host"],
                                     username=fhgw_info["username"],
                                     password=fhgw_info["password"],
                                     root_password=fhgw_info["root_password"],
                                     **kwargs)
        self._global_params = {"pxe_operator": pxe_operator,
                               "fhgw_operator": fhgw_operator,
                               "bmc_info": bmc_info,
                               "fhgw_iso_version": kwargs.get("fhgw_iso_version"),
                               "sled_number": kwargs.get("sled_number"),
                               "pxe_interface": kwargs.get("pxe_interface"),
                               "fhgw_gateway": kwargs.get("fhgw_gateway"),
                               "fhgw_info": kwargs.get("fhgw_info"),
                               "fhgw_netmask": kwargs.get("fhgw_netmask"),
                               "image_tag": kwargs.get("image_tag")}

    def add_step(self, step):
        self._steps.append(step(self._logger, **self._kwargs))

    def _get_step_list_index(self, step_list, klass):
        for index in range(len(step_list)):
            if step_list[index].__class__.__name__ == klass.__name__:
                return index

    def execute(self):
        step_list = self._steps[:]
        while self._steps:
            step = self._steps.pop(0)
            step.global_params = self._global_params
            self._logger.info("## start to do pre-check of step {step_name}".format(step_name=step.step_name))
            if not step.pre_check():
                self._logger.error("## pre check of step {step_name} failed, rest step will be drop".format(step_name=step.step_name))
                raise ExecutionException("pre check of step {step_name} failed, rest step will be drop".format(step_name=step.step_name))
            if not isinstance(step, NoPostCheckStep) and step.post_check():
                self._logger.info("## post check passed, step {step_name} ignored".format(step_name=step.step_name))
                continue
            self._logger.log_header("start to execute step {step_name}".format(step_name=step.step_name))
            step.execute()
            self._logger.info("## start to do post-check of step {step_name}".format(step_name=step.step_name))
            if not step.post_check():
                self._logger.error("## post check of step {step_name} failed, please have a check".format(step_name=step.step_name))
                raise ExecutionException("post check of step {step_name} failed, please have a check".format(step_name=step.step_name))
            if not step.cont:
                self._logger.warn("## the deployment should be end after this step {step_name} because of rest steps are unecessary".format(step_name=step.step_name))
            self._global_params = step.global_params
            if step.step_to_go:
                self._logger.warn("## step {step_name} will go to another step {another_step_name} to exeucte ".format(
                    step_name=step.step_name,
                    another_step_name=step.step_to_go
                ))
                self._steps = step_list[self._get_step_list_index(step_list, step.step_to_go):]
        self._logger.info("fhgw installation finished successfully")

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def teardown(self):
        pass

@six.add_metaclass(ABCMeta)
class Step(object):
    def __init__(self, logger, **kwargs):
        self._logger = logger
        self._kwargs = kwargs
        self.step_name = self.__class__.__name__
        self.global_params = {}
        self.cont = True   # if False, all execution will stop
        self.step_to_go = None  # Step Name to go, if set None, no step will be skipped

    def put_param(self, **kwargs):
        self.global_params.update(kwargs)

    def get_param(self, key_name):
        return self.global_params.get(key_name)

    def pre_check(self):
        return True

    def execute(self):
        self._run()

    @abstractmethod
    def _run(self):
        pass

    def post_check(self):
        return True


@six.add_metaclass(ABCMeta)
class RetriedStep(Step):
    def __init__(self, logger, **kwargs):
        self.retry_max_count = 3
        super(RetriedStep, self).__init__(logger, **kwargs)

    def execute(self):
        retry_count = 0
        while retry_count < self.retry_max_count:
            self._run()
            if self.post_check():
                break
            if retry_count >= 1:
                self._logger.info("retry #{retry_count} for step {step_name}".format(
                    retry_count=retry_count,
                    step_name=self.step_name
                ))
            retry_count += 1

    def _run(self):
        pass

@six.add_metaclass(ABCMeta)
class NoPostCheckStep(Step):
    def __init__(self, logger, **kwargs):
        super(NoPostCheckStep, self).__init__(logger, **kwargs)
