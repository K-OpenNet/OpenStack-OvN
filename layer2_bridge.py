import logging
import subprocess
import shlex


class BridgeController:
    def __init__(self):
        self.logger = None
        pass

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def check_remote_ovsdb(self, __remote_ip):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:"+__remote_ip+":"+remote_port,
                   "show"]
        (returncode, cmdout, cmderr) = self.shell_command(command)

        if returncode is 0:
            self.logger.warn("OVSDB is connectable: " + __remote_ip)
        elif returncode is 1:
            self.logger.warn("OVSDB is not connectable: " + __remote_ip)

        self.logger.debug(str(returncode) + cmdout + cmderr)
        return returncode, cmdout, cmderr

    def add_bridge(self, __remote_ip, __bridge):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:"+__remote_ip+":"+remote_port,
                   "add-br",
                   __bridge]
        (returncode, cmdout, cmderr) = self.shell_command(command)

        self.logger.debug(str(returncode) + cmdout + cmderr)
        return returncode

    def add_port_pair(self, __box1, __box2):
        # need to implement
        pass

    def shell_command(self, __cmd):
        self.logger.debug("Shell command: " + __cmd.__str__())
        if isinstance(__cmd, basestring):
            subproc = subprocess.Popen(shlex.split(__cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
        elif isinstance(__cmd, dict):
            subproc = subprocess.Popen(__cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        (cmdout, cmderr) = subproc.communicate()
        return subproc.returncode, cmdout, cmderr
