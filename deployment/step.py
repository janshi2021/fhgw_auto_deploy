import os
import time
from base import Step, RetriedStep, NoPostCheckStep


class PXEConnection(Step):

    def _run(self):
        pxe_operator = self.get_param("pxe_operator")
        pxe_operator.new_connection()

    def post_check(self):
        return self.get_param("pxe_operator").connected


class FHGWConnection(NoPostCheckStep):

    def _run(self):
        fhgw_operator = self.get_param("fhgw_operator")
        try:
            fhgw_operator.new_connection()
        except Exception:
            self._logger.warn("FHGW can't be accessed by network, will go to installation directly")
            self.step_to_go = FHGWISOPreparation


class FHGWParamInitialize(NoPostCheckStep):

    def _run(self):
        fhgw_iso_version = self.get_param("fhgw_iso_version")
        fhgw_build = fhgw_iso_version.split("_")[-2]
        fhgw_release = fhgw_iso_version.split("_")[0] + "_" + fhgw_iso_version.split("_")[1]
        input_data_path = "/var/lib/docker/volumes/input/_data"
        output_data_path = "/var/lib/docker/volumes/output/_data"
        self.put_param(fhgw_build=fhgw_build,
                       fhgw_release=fhgw_release,
                       input_data_path=input_data_path,
                       output_data_path=output_data_path)
        self._logger.info("current global parameters are {}".format(self.global_params))


class FHGWVersionCheck(NoPostCheckStep):

    def _run(self):
        fhgw_operator = self.get_param("fhgw_operator")
        fhgw_build = self.get_param("fhgw_build")
        fhgw_release = self.get_param("fhgw_release")
        real_sw_build = fhgw_operator.fhgw_get_sw_build()
        real_sw_release = fhgw_operator.fhgw_get_sw_release()
        if (real_sw_build == fhgw_build and real_sw_release == fhgw_release):
            self._logger.info("Expected build {expected_version} is equal "
                              "to current build {current_version}".format(
                expected_version=fhgw_release + "_" + fhgw_build,
                current_version=real_sw_release + "_" + real_sw_build
            ))
            self._logger.info("target version is equal to expected version")
            # will not execute next steps
            self.cont = False


class FHGWISOPreparation(RetriedStep):

    def _download(self, file_suffix=".iso"):
        self._pxe_operator.execute("cd {input_data_path} && rm *.iso && rm *.iso.sha256".format(input_data_path=self.get_param("input_data_path")))
        download_cmd = "wget --no-check-certificate https://bhisoj70.apac.nsn-net.net" \
                       "/artifactory/fhgw-releasedbuilds/builds/FHGW20/{release}/{iso_version}" \
                       " -P {input_data_path}".format(
            release=self.get_param("fhgw_release"),
            iso_version=self._fhgw_iso_version + file_suffix,
            input_data_path=self.get_param("input_data_path")
        )
        result = self._pxe_operator.execute(download_cmd)
        self._logger.info("download iso successfully")

    def _sha256check(self):
        if not self._pxe_operator.file_exists(self._iso_file_path + ".sha256"):
            self._download(".iso.sha256")
        sha256_code = self._pxe_operator.execute("cat {iso_sha256_file_path}".format(iso_sha256_file_path=self._iso_file_path + ".sha256"))
        generate_code = self._pxe_operator.execute("sha256sum {iso_file_path} | awk '{{print $1}}'".format(iso_file_path=self._iso_file_path))
        self._logger.debug("sha256 code in sha256 file is {sha256_code} and generated sha256 code is {generated_sha256_code}".format(
            sha256_code=sha256_code,
            generated_sha256_code=generate_code))
        if sha256_code.strip() == generate_code.strip():
            self._logger.debug("iso file sha256 check is ok")
            return True
        self._logger.debug("iso file sha256 check is not ok")
        return False

    def pre_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        self._fhgw_iso_version = self.get_param("fhgw_iso_version")
        self._input_data_path = self.get_param("input_data_path")
        self._iso_file_path = os.path.join(self._input_data_path, self._fhgw_iso_version + ".iso")
        self.put_param(iso_file_path=self._iso_file_path)
        return True

    def _wait_iso_file_size_changed_finished(self):
        start_size = self._pxe_operator.get_file_size(self._iso_file_path)
        time.sleep(5)
        while self._pxe_operator.get_file_size(self._iso_file_path) != start_size:
            start_size = self._pxe_operator.get_file_size(self._iso_file_path)
            time.sleep(5)

    def post_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        if self._pxe_operator.file_exists(self._iso_file_path):
            self._wait_iso_file_size_changed_finished()
            if self._sha256check():
                self._logger.info("sha256 of iso build check passed")
                return True
        self._logger.error("sha256 of iso build check failed")
        return False

    def _run(self):
        self._download(file_suffix=".iso")


class PXEStopAllDockers(Step):

    def pre_check(self):
        if self.get_param("docker_exists"):
            return False
        self.pxe_operator = self.get_param("pxe_operator")
        return True

    def _run(self):
        docker_instances = self.pxe_operator.get_docker_instances()
        running_docker_id_list = []
        for docker_instance in docker_instances:
            running_docker_id_list.append(docker_instance["id"])
        self.pxe_operator.stop_docker_by_ids(running_docker_id_list)
        self._logger.info("runnder container list {} have been stoped".format(running_docker_id_list))

    def post_check(self):
        docker_instances = self.pxe_operator.get_docker_instances()
        self._loger.info("docker instances are {}".format(docker_instances))
        for docker_instance in self.docker_instances:
            if docker_instance["status"] == "up":
                return False
        return True


class PXEDockerExist(Step):

    def pre_check(self):
        image_tag = self.get_param("image_tag")
        fhgw_release = self.get_param("fhgw_release")
        swinstallenabler_repo = "fhgw-ci-docker-local.bhisoj70.apac.nsn-net.net"
        self.image_uri = swinstallenabler_repo + "/" + fhgw_release.lower() + "/swinstallenabler:" + image_tag
        self.pxe_operator = self.get_param("pxe_operator")
        return True

    def _run(self):
        for docker_item in self.pxe_operator.get_docker_instances():
            if docker_item["image_uri"] == self.image_uri:
                if docker_item["status"] == "exited":
                    self.pxe_operator.start_docker_by_id(docker_item["id"])

    def post_check(self):
        for docker_item in self.pxe_operator.get_docker_instances():
            if docker_item["image_uri"] == self.image_uri and docker_item["status"] == "up":
                self._logger.debug("matched docker instance is exist")
                self.put_param(docker_exists=True)
        self.put_param(docker_exists=False)
        return True


class PXERemoveExistDocker(Step):

    def pre_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        return True

    def _run(self):
        docker_instances = self._pxe_operator.get_docker_instances()
        running_docker_ids = [docker_instance["id"] for docker_instance in docker_instances if docker_instance["status"] == "up"]
        self._pxe_operator.stop_docker_by_ids(running_docker_ids)
        self._pxe_operator.remove_docker(docker_instances)
        self._logger.info("remove docker instances {} successfully".format(docker_instances))

    def post_check(self):
        if self.get_param("docker_exists"):
            return True
        if self._pxe_operator.get_docker_instances():
            return False
        return True


class PXEInstallNewDocker(Step):

    def _run(self):
        input_data_path = self.get_param("input_data_path")
        self._fhgw_iso_version = self.get_param("fhgw_iso_version")
        iso_file_path = os.path.join(input_data_path, self._fhgw_iso_version + ".iso")
        iso_sha256_file_path = os.path.join(input_data_path, self._fhgw_iso_version + ".iso.sha256")
        pxe_operator = self.get_param("pxe_operator")
        image_tag = self.get_param("image_tag")
        pxe_operator.execute("mount -o loop {iso_file_path} /mnt".format(iso_file_path=iso_file_path))
        pxe_operator.execute("cp -f /mnt/MISC/SWInstallEnabler/scripts/startInstallation.sh {input_data_path}".format(input_data_path=input_data_path))
        pxe_operator.execute("umount /mnt")
        pxe_operator.execute("sha256sum {iso_file_path} | awk '{{print $1}}' > {iso_sha256_file_path}".format(
            iso_file_path=iso_file_path,
            iso_sha256_file_path=iso_sha256_file_path))
        pxe_operator.execute("cd {input_data_path} && yes | ./startInstallation.sh {image_tag}".format(input_data_path=input_data_path, image_tag=image_tag))

    def post_check(self):
        if self.get_param("docker_exists"):
            return True
        image_tag = self.get_param("image_tag")
        fhgw_release = self.get_param("fhgw_release")
        swinstallenabler_repo = "fhgw-ci-docker-local.bhisoj70.apac.nsn-net.net"
        self.image_uri = swinstallenabler_repo + "/" + fhgw_release.lower() + "/swinstallenabler:" + image_tag
        self.pxe_operator = self.get_param("pxe_operator")
        for docker_item in self.pxe_operator.get_docker_instances():
            if docker_item["image_uri"] == self.image_uri and docker_item["status"] == "up":
                    return True
        self._logger.info("current docker status is {}".format(self.pxe_operator.get_docker_instances()))
        return False


class PXERestartDockerIfFHGWSessionFailed(RetriedStep):

    def pre_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        self._output_session_log = os.path.join(self.get_param("output_data_path"), "session_create.log")
        return True

    def _wait_until_session_started(self):
        start_time = time.time()
        while time.time() - start_time < 5*60:
            result = self._pxe_operator.execute("tail -10 {} | grep 'session \"fhgw\" started' |  wc -l".format(self._output_session_log))
            if int(result.strip()):
                break
            time.sleep(5)
        else:
            self._logger.error("time out of waiting for fhgw session started")
            return False
        return True

    def _run(self):
        for docker_instance in self._pxe_operator.get_docker_instances():
            if docker_instance["status"] == "up":
                self._pxe_operator.stop_docker_by_ids([docker_instance["id"]])
                self._pxe_operator.start_docker_by_id(docker_instance["id"])

    def post_check(self):
        if self._pxe_operator.file_exists(self._output_session_log) and self._wait_until_session_started():
            return True
        return False


class PXEModifyUserConfig(Step):

    def pre_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        self._input_data_path = self.get_param("input_data_path")
        self._sled_num = self.get_param("sled_number")
        self._pxe_interface = self.get_param("pxe_interface")
        self._fhgw_gateway = self.get_param("fhgw_gateway")
        self._fhgw_netmask = self.get_param("fhgw_netmask")
        self._user_config_name = "fhgw-user-config_{sled_num}.yaml".format(sled_num=self._sled_num)
        self._user_deployer_config_name = "fhgw-deployer-config.yaml"
        self._user_config_path = os.path.join(self._input_data_path, self._user_config_name)
        self._user_deployer_path = os.path.join(self._input_data_path, self._user_deployer_config_name)
        code_dir = os.path.dirname(os.path.abspath(__file__))
        self._template_user_config_path = os.path.join(code_dir, "template/fhgw-user-config.yaml")
        self._template_user_deployer_path = os.path.join(code_dir, "template/fhgw-deployer-config.yaml")
        return True

    def _run(self):
        self._pxe_operator.put_file(self._template_user_config_path, self._user_config_path)
        self._pxe_operator.put_file(self._template_user_deployer_path, self._user_deployer_path)
        self._pxe_operator.execute("sed -i 's/    ipAddress.*/    ipAddress: {}/' {}".format(
            self.get_param("fhgw_info")["host"],
            self._user_config_path))
        self._pxe_operator.execute("sed -i 's/    ipPrefixLength.*/    ipPrefixLength: {}/' {}".format(
            self.get_param("fhgw_netmask"),
            self._user_config_path))
        self._pxe_operator.execute("sed -i 's/    gateway.*/    gateway: {}/' {}".format(
            self.get_param("fhgw_gateway"),
            self._user_config_path))
        self._pxe_operator.execute("sed -i 's/    ethIfName.*/    ethIfName: {}/' {}".format(
            self.get_param("pxe_interface"),
            self._user_deployer_path))

    def _get_value_by_key(self, file_path, key):
        value = self._pxe_operator.execute("echo `cat {}  | grep \"{}\" | awk -F : '{{print $2}}'`".format(file_path, key))
        return value.splitlines()

    def _is_user_config_file_ok(self):
        fhgw_ips = self._get_value_by_key(self._user_config_path, "    ipAddress")
        fhgw_netmasks = self._get_value_by_key(self._user_config_path, "    ipPrefixLength")
        fhgw_gateways = self._get_value_by_key(self._user_config_path, "     gateway")
        if fhgw_ips and fhgw_netmasks and fhgw_gateways:
            if (fhgw_ips[0].lower().strip() == self.get_param("fhgw_info").get("host").lower() and
                    fhgw_netmasks[0].lower().strip() == self.get_param("fhgw_netmask").lower() and
                    fhgw_gateways[0].lower().strip() == self.get_param("fhgw_gateway").lower()):
                return True
        return False

    def _is_user_deployer_file_ok(self):
        itf_names = self._get_value_by_key(self._user_deployer_path, "    ethIfName")
        if itf_names and itf_names[0].strip().lower() == self._pxe_interface.strip().lower():
            return True
        return False

    def post_check(self):
        if (self._pxe_operator.file_exists(self._user_config_path) and self._is_user_config_file_ok() and
        self._pxe_operator.file_exists(self._user_deployer_path) and self._is_user_deployer_file_ok()):
            return True
        return False


class TriggerFHGWStartInstallation(RetriedStep):

    def pre_check(self):
        self._pxe_operator = self.get_param("pxe_operator")
        self._fhgw_operator = self.get_param("fhgw_operator")
        self._bmc_info = self.get_param("bmc_info")
        code_dir = os.path.dirname(os.path.abspath(__file__))
        self._pxe_operator.put_file(os.path.join(code_dir, "scripts", "boot_priority.json"), "/root/boot_priority.json")
        self._pxe_operator.put_file(os.path.join(code_dir, "scripts", "setbootdevice.sh"), "/root/setbootdevice.sh")
        self._logger.info("uploaded boot_priority.json and setbootdevice.sh to pxe server")
        self._pxe_operator.execute("chmod +x /root/setbootdevice.sh")
        return True

    def _wait_until_fhgw_connection_created(self, timeout=25 * 60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self._fhgw_operator.new_connection()
                break
            except Exception:
                pass
        else:
            self._logger.warn("fhgw connection create timeout after installation")
            return False
        return True

    def _run(self):
        for i in range(3):
            result = self._pxe_operator.execute("cd /root && ./setbootdevice.sh -i {bmc_host} -m Legacy -o Once -b Pxe -u {bmc_user} -p {bmc_password}".format(
                bmc_host=self._bmc_info["host"],
                bmc_user=self._bmc_info["username"],
                bmc_password=self._bmc_info["password"]))
            if "successfully" not in result:
                self._logger.warn("reboot fhgw failed through bmc")
                continue
            time.sleep(5)
        time.sleep(20)
        result = self._wait_until_fhgw_connection_created()
        if not result:
            self._logger.warn("fhgw connection can't be created in 25 minutes")

    def post_check(self):
        result = self._wait_until_fhgw_connection_created(30)
        if not result:
            return False
        current_release = self._fhgw_operator.fhgw_get_sw_release()
        current_build = self._fhgw_operator.fhgw_get_sw_build()
        if (current_build == self.get_param("fhgw_build") and
                current_release == self.get_param("fhgw_release")):
            return True
        self._logger.warn("current release: {current_release} and current build: {current_build}, not equal to "
                          "target release: {target_release} and target build: {target_build}".format(current_release=current_release,
                                                                                                     current_build=current_build,
                                                                                                     target_release=self.get_param("fhgw_release"),
                                                                                                     target_build=self.get_param("fhgw_build")))
        return False


class ClearFirewallAndStopRelatedSerices(NoPostCheckStep):

    def _run(self):
        self._pxe_operator = self.get_param("pxe_operator")
        self._pxe_operator.execute("ip a | grep 192.168.0.2 | awk '{print $5}' | xargs ip a del 192.168.0.2 dev")
        self._pxe_operator.execute("iptables -F")
        self._pxe_operator.execute("iptables -t nat -F")
        self._pxe_operator.execute("setenforce 0")
        self._pxe_operator.execute("systemctl stop firewalld")
        self._pxe_operator.execute("systemctl stop tftp.socket")
        self._logger.info("clear firewall successfully")

