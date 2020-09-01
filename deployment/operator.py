import time
from SSHLibrary import SSHLibrary

class Operator(SSHLibrary):

    def __init__(self, host, username, password, **kwargs):
        self._host = host
        self._username = username
        self._password = password
        self._kwargs = kwargs
        self._logger = kwargs.get("logger")
        self.connected = False
        super(Operator, self).__init__()

    def new_connection(self):
        self.open_connection(host=self._host)
        self.login(self._username, self._password)
        self.connected = True

    def close_connection(self):
        self.close_connection()
        self.connected = False

    def write_with_newline(self, cmd):
        self.write(cmd + "\n")

    def execute(self, cmd, check_result=False):
        self._logger.debug(cmd)
        stdout, stderr, rc = self.execute_command(cmd, return_stderr=True, return_rc=True)
        if rc != 0 and check_result:
            raise RuntimeError(
                "Command '%s' returned '%s' but '%s' was expected" % (cmd, rc, "0"))
        output = stdout + stderr
        self._logger.debug(output)
        return output

    def get_file_size(self, file_path):
        return self.execute("ls -l {file_path} | awk '{{print $5}}'".format(file_path=file_path))

    def file_exists(self, file_path):
        result = self.execute("ls -l {file_path}".format(file_path=file_path))
        if "cannot access" in result:
            return False
        return True

    def remove_file_or_directory(self, file_path):
        self.execute("rm -rf {file_path}".format(file_path=file_path))


class PXEServerOperator(Operator):

    def __init__(self, host, username, password, **kwargs):
        super(PXEServerOperator, self).__init__(host, username, password, **kwargs)

    def get_docker_instances(self):
        docker_list = []
        result = self.execute("docker ps --all")
        lines = result.splitlines()
        header = lines.pop(0)
        for line in lines:
            docker_item = {}
            items = line.split()
            docker_item["id"] = items[0]
            docker_item["image_uri"] = items[1]
            docker_item["status"] = line[header.index("STATUS"): header.index("PORTS")].strip().split()[0].lower()
            docker_list.append(docker_item)
        return docker_list

    def stop_docker_by_ids(self, docker_id_list):
        for docker_id in docker_id_list:
            self.execute("docker stop {docker_id}".format(docker_id=docker_id))

    def start_docker_by_id(self, docker_id):
        self.execute("docker start {docker_id}".format(docker_id=docker_id))

    def remove_docker(self, docker_list):
        running_docker_list = [item["id"] for item in docker_list if item["status"] == "up"]
        if running_docker_list:
            self.stop_docker_by_ids(running_docker_list)
        for docker_item in docker_list:
            self.execute("docker rm {docker_id}".format(docker_id=docker_item["id"]))


class FHGWOperator(Operator):

    def __init__(self, host, username, password, root_password, **kwargs):
        self._root_password = root_password
        self._prompt = r"\[.*?@.*?\]\s*#"
        super(FHGWOperator, self).__init__(host, username, password, **kwargs)

    def new_connection(self):
        self.open_connection(host=self._host)
        self.login(self._username, self._password)
        time.sleep(0.1)
        self.write_with_newline(self._root_password)
        time.sleep(0.2)
        self.read_until_regexp(self._prompt)
        self.connected = True

    def execute(self, command, check_result=False):
        echo_result = self._execute("echo")
        self._logger.debug(command)
        cmd_result = self._execute(command, check_result=check_result)
        output = cmd_result.replace(echo_result.strip(), "").strip()
        self._logger.debug(output)
        return output

    def _check_cmd_result(self, cmd):
        return_code_flag = "return code is:"
        self.write("echo %s$?" % return_code_flag)
        raw_return_code = self.read_until_regexp(self._prompt)
        return_lines = raw_return_code.splitlines()
        return_code = 1
        for line in return_lines:
            if line.startswith(return_code_flag):
                return_code = int(line.lstrip(return_code_flag).strip())
        if return_code != 0:
            raise RuntimeError(
                "Command '%s' returned '%s' but '%s' was expected" % (cmd, return_code, "0"))

    def _execute(self, command, check_result=False):
        try:
            print(self.read())
        except Exception:
            pass
        self.write(command)
        ret = self.read_until_regexp(self._prompt)
        if check_result:
            self._check_cmd_result(command)
        return ret

    def fhgw_get_sw_build(self):
        cmd = "/opt/nokia/bin/fhgwcli swm show node | grep build | awk '{print $5}'"
        result = self.execute(cmd)
        return result

    def fhgw_get_sw_release(self):
        cmd = "/opt/nokia/bin/fhgwcli swm show node | grep Release | awk '{print $5}'"
        result = self.execute(cmd)
        return result









