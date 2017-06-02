import logging
import util
import ifaces.ovsdb_api as ovsdb


class L2BridgeController:
    def __init__(self):
        self.logger = logging.getLogger("ovn.control.l2bridge")
        self._bridge = ovsdb.OVSDB_API()
        self._util = util.Utils()

    def parse_template(self, ovs_config):
        self.logger.debug("Parse Networking Template for OVS, config: " + ovs_config.__str__())

        try:
            # Split box and bridge
            end1 = ovs_config['end1'].split('.')
            end2 = ovs_config['end2'].split('.')

            ovs_config['end1_box'] = end1[0]
            ovs_config['end1_bridge'] = end1[1]

            ovs_config['end2_box'] = end2[0]
            ovs_config['end2_bridge'] = end2[1]

            return ovs_config

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

    def config_l2bridge(self, ovs_config):
        self.logger.debug("Configure OVS, config: " + ovs_config.__str__())

        # Need to add codes to check valid OVS configuration format
        self.check_ovs_format(ovs_config)
        self.check_connectivity(ovs_config)

        if ovs_config['type'] == "bridge":
            self.configure_ovs_bridges(ovs_config)

        elif ovs_config['type'] in ['vxlan','patch']:
            self.configure_ovs_ports(ovs_config)

    def configure_ovs_bridges(self, ovs_config):
        if isinstance(ovs_config['bridge'], basestring):
            brlist = [ovs_config['bridge']]
        elif isinstance(ovs_config['bridge'], list):
            brlist = ovs_config['bridge']
        else:
            return TypeError

        for bridge in brlist:
            self._bridge.create_bridge(ovs_config['target_ipaddr'], bridge)
            self._bridge.update_bridge_controller(ovs_config['target_ipaddr'], bridge, ovs_config['sdn_control_ipaddr'])

    def configure_ovs_ports(self, ovs_config):
        try:
            # Split box and bridge
            tmp = dict()
            end1_ipaddr = ovs_config['end1_ipaddr']
            end1_box = ovs_config['end1_box']
            end1_bridge = ovs_config['end1_bridge']
            end1_sdn = ovs_config['sdn_control_ipaddr']

            tmp['target_ipaddr'] = end1_ipaddr
            tmp['bridge'] = end1_bridge
            tmp['sdn_control_ipaddr'] = end1_sdn
            self.configure_ovs_bridges(tmp)

            end2_ipaddr = ovs_config['end2_ipaddr']
            end2_box = ovs_config['end2_box']
            end2_bridge = ovs_config['end2_bridge']
            end2_sdn = ovs_config['sdn_control_ipaddr']

            tmp['target_ipaddr'] = end1_ipaddr
            tmp['bridge'] = end1_bridge
            tmp['sdn_control_ipaddr'] = end2_sdn
            self.configure_ovs_bridges(tmp)

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

        # Add a bridge
        self._bridge.create_bridge(end1_ipaddr, end1_bridge)
        self._bridge.create_bridge(end2_ipaddr, end2_bridge)

        self._bridge.update_bridge_controller(end1_ipaddr, end1_bridge, end1_sdn)
        self._bridge.update_bridge_controller(end2_ipaddr, end2_bridge, end2_sdn)

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
            box1_port = end1_box + "_to_" + end2_box
            box2_port = end2_box + "_to_" + end1_box
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

    def check_connectivity(self, ovs_config):
        ipaddr_list = list()
        if ovs_config['type'] == ["bridge"]:
            ipaddr_list.append(ovs_config['target_ipaddr'])
        elif ovs_config['type'] in ["vxlan", "patch"]:
            ipaddr_list.append(ovs_config['end1_ipaddr'])
            ipaddr_list.append(ovs_config['end2_ipaddr'])

        for ipaddr in ipaddr_list:
            returncode = self._util.check_box_connect(ipaddr)
            if returncode is 0:
                self.logger.info("Box is reachable: " + ipaddr)
            elif returncode is 1:
                self.logger.warn("Box is not reachable: " + ipaddr)
                return

            (returncode, cmdout, cmderr) = self._bridge.read_ovs_config(ipaddr)
            if returncode is 0:
                self.logger.info("OVSDB is connectable: " + ipaddr)
            elif returncode is 1:
                self.logger.warn("OVSDB is not connectable: " + ipaddr)
                return

    def config_remote_ovsdb(self, __box):
        # Need to implement
        pass

    def check_ovs_format(self, __ovs):
        # Need to implement
        pass

if __name__ == "__main__":
    tmp = "br-test"
    print str(tmp).strip("br").strip("-")
