import logging
import yaml
import subprocess
import shlex
import simplejson as json


class Utils:
    def __init__(self):
        self.logger = logging.getLogger("ovn.util")

    def parse_yaml_file(self, __file):
        """ Parse the data from YAML template. """
        with open(__file, 'r') as stream:
            try:
                file_str = stream.read()
                self.logger.info("Parse YAML from the file: \n" + file_str)
                return yaml.load(file_str)
            except yaml.YAMLError, exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    self.logger.error(("YAML Format Error: " + __file
                                       + " (Position: line %s, column %s)" %
                                       (mark.line + 1, mark.column + 1)))
                    return None

    def parse_json_str(self, str):
        try:
            return json.loads(str)
        except json.JSONDecodeError, exc:
            self.logger.error(("JSON Format Error: " + str
                                       + " (Position: line %s, column %s)" %
                                       (exc.lineno + 1, exc.colno + 1)))

    def check_box_connect(self, __remote_ip):
        command = ["ping", "-c 1", "-W 1", __remote_ip]
        (returncode, cmdout, cmderr) = self.shell_command(command)

        if returncode is 0:
            self.logger.info("Box is connectable: " + __remote_ip)
        elif returncode is 1:
            self.logger.error("Box is not connectable: " + __remote_ip)
        return returncode


    def shell_command(self, __cmd):
        self.logger.debug("Shell command: " + __cmd.__str__())
        subproc = None
        if isinstance(__cmd, basestring):
            subproc = subprocess.Popen(shlex.split(__cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        elif isinstance(__cmd, list):
            subproc = subprocess.Popen(__cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        (cmdout, cmderr) = subproc.communicate()
        return subproc.returncode, cmdout, cmderr
