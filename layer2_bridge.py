import logging
import util
import ifaces.ovsdb_api as ovsdb


class L2BridgeController:
    def __init__(self):
        self.logger = None
        self.initialize_logger()
        self._bridge = ovsdb.OVSDB_API()
        self._util = util.Utils()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def parse_ovs(self, ovs_config):
        self.logger.debug("Parse Networking Template for OVS, config: " + ovs_config.__str__())

        try:
            # Split box and bridge
            end1 = ovs_config['end1'].split('.')
            end2 = ovs_config['end2'].split('.')

            ovs_config['end1_name'] = end1[0]
            ovs_config['end1_bridge'] = end1[1]

            ovs_config['end2_name'] = end2[0]
            ovs_config['end2_bridge'] = end2[1]

            return ovs_config

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

    def config_ovs(self, ovs_config):
        self.logger.debug("Configure OVS, config: " + ovs_config.__str__())

        # Need to add codes to check valid OVS configuration format
        self.check_ovs_format(ovs_config)

        try:
            # Split box and bridge
            end1_ipaddr = ovs_config['end1_ipaddr']
            end1_name = ovs_config['end1_name']
            end1_bridge = ovs_config['end1_bridge']

            end2_ipaddr = ovs_config['end2_ipaddr']
            end2_name = ovs_config['end2_name']
            end2_bridge = ovs_config['end2_bridge']

            # Check Box connectivity
            if self._util.check_box_connect(end1_ipaddr) is 1 \
                    or self._util.check_box_connect(end2_ipaddr) is 1:
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
        self._bridge.create_bridge(end1_ipaddr, end1_bridge)
        self._bridge.create_bridge(end2_ipaddr, end2_bridge)

        self._bridge.update_bridge_controller(end1_ipaddr, end1_bridge, "10.246.67.127")
        self._bridge.update_bridge_controller(end2_ipaddr, end2_bridge, "10.246.67.127")

        # Create Patch Port Pair
        if ovs_config['type'] == "patch":
            box1_port = str(end1_bridge).strip("br").strip("-") + "_2_" + str(end2_bridge).strip("br").strip("-")
            box2_port = str(end2_bridge).strip("br").strip("-") + "_2_" + str(end1_bridge).strip("br").strip("-")

            self._bridge.create_port(end1_ipaddr, end1_bridge, box1_port)
            self._bridge.update_port_type(end1_ipaddr, box1_port, "patch")
            self._bridge.update_port_option(end1_ipaddr, box1_port, "peer", box2_port)

            self._bridge.create_port(end2_ipaddr, end2_bridge, box2_port)
            self._bridge.update_port_type(end2_ipaddr, box2_port, "patch")
            self._bridge.update_port_option(end2_ipaddr, box2_port, "peer", box1_port)

        # Create VxLAN Port Pair
        elif ovs_config['type'] == "vxlan":
            box1_port = end1_name + "_to_" + end2_name
            box2_port = end2_name + "_to_" + end1_name
            end1_vtep = ovs_config['end1_vtep']
            end2_vtep = ovs_config['end2_vtep']

            self._bridge.create_port(end1_ipaddr, end1_bridge, box1_port)
            self._bridge.update_port_type(end1_ipaddr, box1_port, "patch")
            self._bridge.update_port_option(end1_ipaddr, box1_port, "key", 33333)
            self._bridge.update_port_option(end1_ipaddr, box1_port, "remote_ip", end1_vtep)

            self._bridge.create_port(end2_ipaddr, end2_bridge, box2_port)
            self._bridge.update_port_type(end2_ipaddr, box2_port, "patch")
            self._bridge.update_port_option(end2_ipaddr, box2_port, "key", 33333)
            self._bridge.update_port_option(end2_ipaddr, box2_port, "remote_ip", end2_vtep)

    def check_remote_ovsdb(self, __remote_ip):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:"+__remote_ip+":"+remote_port,
                   "show"]
        (returncode, cmdout, cmderr) = self._util.shell_command(command)

        if returncode is 0:
            self.logger.info("OVSDB is connectable: " + __remote_ip)
        elif returncode is 1:
            self.logger.warn("OVSDB is not connectable: " + __remote_ip)

        return returncode, cmdout, cmderr

    def config_remote_ovsdb(self, __box):
        # Need to implement
        pass

    def check_ovs_format(self, __ovs):
        # Need to implement
        pass

if __name__ == "__main__":
    tmp = "br-test"
    print str(tmp).strip("br").strip("-")
