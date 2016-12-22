import logging
import util


class L2BridgeController:
    def __init__(self):
        self.logger = None
        self.initialize_logger()
        self._util = util.Utils()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def parse_ovs(self, __ovs):
        self.logger.debug("Parse Networking Template for OVS, config: " + __ovs.__str__())

        try:
            # Split box and bridge
            end1 = __ovs['end1'].split('.')
            end2 = __ovs['end2'].split('.')

            __ovs['end1_name'] = end1[0]
            __ovs['end2_name'] = end2[0]

            __ovs['end1_bridge'] = end1[1]
            __ovs['end2_bridge'] = end2[1]

            return __ovs

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

    def config_ovs(self, __ovs):
        self.logger.debug("Configure OVS, config: " + __ovs.__str__())

        # Need to add codes to check valid OVS configuration format
        self.check_ovs_format()

        try:
            # Split box and bridge
            end1_ipaddr = __ovs['end1_ipaddr']
            end2_ipaddr = __ovs['end2_ipaddr']

            end1_name = __ovs['end1_hostname']
            end2_name = __ovs['end2_hostname']

            end1_bridge = __ovs['end1_bridge']
            end2_bridge = __ovs['end2_bridge']

            # Check Box connectivity
            if self.check_box_connect(end1_ipaddr) is 1 \
                    or self.check_box_connect(end2_ipaddr) is 1:
                return None

            if self.check_remote_ovsdb(end1_ipaddr) is 1:
                self.config_remote_ovsdb(end1_ipaddr)
                return None

            if self.check_remote_ovsdb(end2_ipaddr) is 1:
                self.config_remote_ovsdb(end2_ipaddr)
                return None

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

        # Add a bridge
        self.add_bridge(end1_ipaddr, end1_bridge)
        self.add_bridge(end2_ipaddr, end2_bridge)

        # Add a port pair
        if __ovs['type'] == "patch":
            box1_port = end1_bridge + "_to_" + end2_bridge
            box2_port = end2_bridge + "_to_" + end1_bridge
            self.add_patch_port_pair(
                __box1_ip=end1_ipaddr,
                __box1_br=end1_bridge,
                __box1_port=box1_port,
                __box2_ip=end2_ipaddr,
                __box2_br=end2_bridge,
                __box2_port=box2_port)

        elif __ovs['type'] == "vxlan":
            box1_port = end1_name + "_to_" + end2_name
            box2_port = end2_name + "_to_" + end1_name
            end1_vtep = __ovs['end1_vtep']
            end2_vtep = __ovs['end2_vtep']
            self.add_vxlan_port_pair(
                __box1_ip=end1_ipaddr,
                __box1_vtep_ip=end2_vtep,
                __box1_br=end1_bridge,
                __box1_port=box1_port,
                __box2_ip=end2_ipaddr,
                __box2_vtep_ip=end1_vtep,
                __box2_br=end2_bridge,
                __box2_port=box2_port)

    def check_remote_ovsdb(self, __remote_ip):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:"+__remote_ip+":"+remote_port,
                   "show"]
        (returncode, cmdout, cmderr) = self._util.shell_command(command)

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
        (returncode, cmdout, cmderr) = self._util.shell_command(command)

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
        (returncode, cmdout, cmderr) = self._util.shell_command(command)
        self.logger.debug(str(returncode) + cmdout + cmderr)

        return returncode, cmdout, cmderr

    def set_patch_option(self, __box_ip, __port, __peer_port):
        remote_port = "6640"

        command = ["ovs-vsctl",
                   "--db=tcp:" + __box_ip + ":" + remote_port,
                   "set interface", __port,
                   "type=patch",
                   "options:" + "peer=" + __peer_port]
        (returncode, cmdout, cmderr) = self._util.shell_command(command)
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
        (returncode, cmdout, cmderr) = self._util.shell_command(command)
        self.logger.debug(str(returncode) + cmdout + cmderr)

        return returncode, cmdout, cmderr

    def check_box_connect(self, __remote_ip):
        command = ['ping', '-c 1', '-W 1', __remote_ip]
        (returncode, cmdout, cmderr) = self._util.shell_command(command)

        if returncode is 0:
            self.logger.error("Box is connectable: " + __remote_ip)
        elif returncode is 1:
            self.logger.error("Box is not connectable: " + __remote_ip)
        return returncode

    def config_remote_ovsdb(self, __box):
        # Need to implement
        pass

    def check_ovs_format(self, __ovs):
        # Need to implement
        pass
