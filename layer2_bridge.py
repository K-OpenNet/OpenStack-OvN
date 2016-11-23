import logging
import subprocess
import shlex


class L2BridgeController:
    def __init__(self):
        self.logger = None
        self.initialize_logger()

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

    def add_patch_port_pair(self,
                            __box1_ip, __box1_br, __box1_port,
                            __box2_ip, __box2_br, __box2_port):

        self.add_port(__box1_ip, __box1_br, __box1_port)
        self.add_port(__box2_ip, __box2_br, __box2_port)

        self.set_patch_option(__box1_ip, __box1_port, __box2_port)
        self.set_patch_option(__box2_ip, __box2_port, __box1_port)

    def add_vxlan_port_pair(self,
                            __box1_ip, __box1_vtep_ip, __box1_br, __box1_port,
                            __box2_ip, __box2_vtep_ip, __box2_br, __box2_port,
                            __vni="33333"):

        self.add_port(__box1_ip, __box1_br, __box1_port)
        self.add_port(__box2_ip, __box2_br, __box2_port)

        self.set_vxlan_option(__box1_ip, __box1_port, __box2_vtep_ip, __vni)
        self.set_vxlan_option(__box2_ip, __box2_port, __box1_vtep_ip, __vni)

    def add_port(self, __box_ip, __bridge, __port):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:" + __box_ip + ":" + remote_port,
                   "add-port",
                   __bridge,
                   __port]
        (returncode, cmdout, cmderr) = self.shell_command(command)
        self.logger.debug(str(returncode) + cmdout + cmderr)

        return returncode, cmdout, cmderr

    def set_patch_option(self, __box_ip, __port, __peer_port):
        remote_port = "6640"

        command = ["ovs-vsctl",
                   "--db=tcp:" + __box_ip + ":" + remote_port,
                   "set interface", __port,
                   "type=patch",
                   "options:" + "peer=" + __peer_port]
        (returncode, cmdout, cmderr) = self.shell_command(command)
        self.logger.debug(str(returncode) + cmdout + cmderr)

        return returncode, cmdout, cmderr

    def set_vxlan_option(self, __box_ip, __port, __peer_ip, __vni):
        remote_port = "6640"

        command = ["ovs-vsctl",
                   "--db=tcp:" + __box_ip + ":" + remote_port,
                   "set interface", __port,
                   "type=vxlan",
                   "options:", "key=" + __vni,
                   "options:", "remote_ip=" + __peer_ip]
        (returncode, cmdout, cmderr) = self.shell_command(command)
        self.logger.debug(str(returncode) + cmdout + cmderr)

        return returncode, cmdout, cmderr

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
