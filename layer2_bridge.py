import logging

import ifaces.ovsdb_api as ovsdb
from utils import util
import networking_graph


class L2BridgeController:
    def __init__(self):
        self.logger = logging.getLogger("ovn.control.l2bridge")
        self._bridge_interface = ovsdb.OVSDB_API()
        self._util = util.Utils()

    def provision(self, be):
        self.logger.debug("Configure OVS, config: " + be.__str__())
        self._pre_check_before_provision()
        self._do_provision(be)

    def _pre_check_before_provision(self, be):
        try:
            self.check_template_format(be)
            self._check_connectivity(be)
        except ValueError as err:
            print err.message
        except AttributeError as err:
            print err.message

    def check_template_format(self, be):
        # Need to be implemented
        pass

    def _check_connectivity(self, be):
        ipaddr_list = self._get_ipaddr_list(be)
        self._check_ip_connectivity(ipaddr_list)
        self._check_ovsdb_connectivity(ipaddr_list)

    def _get_ipaddr_list(self, be):
        if be['type'] == ["bridge"]:
            return self._get_ipaddr_list_for_bridge(be)
        elif be['type'] in ["vxlan", "patch"]:
            return self._get_ipaddr_list_for_ports(be)

    def _get_ipaddr_list_for_bridge(self, be):
        ipaddr_list = list()
        ipaddr_list.append(be['target']['ipaddr'])
        return ipaddr_list

    def _get_ipaddr_list_for_ports(self, be):
        ipaddr_list = list()
        ipaddr_list.append(be['end1']['ipaddr'])
        ipaddr_list.append(be['end2']['ipaddr'])
        return ipaddr_list

    def _check_ip_connectivity(self, ipaddr_list):
        for ipaddr in ipaddr_list:
            returncode = self._util.check_ip_connectivity(ipaddr)
            if returncode is 0:
                self.logger.info("IP address is reachable: " + ipaddr)
            elif returncode is 1:
                raise ValueError("IP address is not reachable: " + ipaddr)

    def _check_ovsdb_connectivity(self, ipaddr, port):
        (returncode, cmdout, cmderr) = self._bridge_interface.read_ovs_config(ipaddr)
        if returncode is 0:
            self.logger.info("OVSDB is reachable: " + ipaddr)
        elif returncode is 1:
            raise ValueError("OVSDB is not reachable: " + ipaddr)

    def _do_provision(self, be):
        if be['type'] == "bridge":
            self._configure_ovs_bridges(be)
        elif be['type'] in ['vxlan', 'patch']:
            self._configure_ovs_ports(be)
        # I'll add codes to remove all bridges/ports configured from this execution

    def _configure_ovs_bridges(self, be):
        box_ipaddr = be['target']['ipaddr']
        bridge_list = self._get_bridge_list_from_bridge_element(be['target'])
        for bridge_name in bridge_list:
            self._configure_ovs_bridge(box_ipaddr, bridge_name, be['sdn_control_ipaddr'])

    def _get_bridge_list_from_bridge_element(self, be):
        if isinstance(be['bridge'], basestring):
            return [be['bridge']]
        elif isinstance(be['bridge'], list):
            return be['bridge']
        else:
            raise TypeError('"bridge" is neither string variable nor list variable')

    def _configure_ovs_bridge(self, box_ipaddr, bridge_name, sdn_control_ip):
        self._bridge_interface.create_bridge(box_ipaddr, bridge_name)
        self._bridge_interface.update_bridge_controller(box_ipaddr, bridge_name, sdn_control_ip)

    def _configure_ovs_ports(self, ovs_config):
        # Separate end1 and end2
        # Create end1 / end2 bridges
        # Add patch ports

        tmp = dict()
        end1_ipaddr = ovs_config['end1_ipaddr']
        end1_box = ovs_config['end1_box']
        end1_bridge = ovs_config['end1_bridge']
        end1_sdn = ovs_config['sdn_control_ipaddr']

        tmp['target_ipaddr'] = end1_ipaddr
        tmp['bridge'] = end1_bridge
        tmp['sdn_control_ipaddr'] = end1_sdn
        self._configure_ovs_bridges(tmp)

        end2_ipaddr = ovs_config['end2_ipaddr']
        end2_box = ovs_config['end2_box']
        end2_bridge = ovs_config['end2_bridge']
        end2_sdn = ovs_config['sdn_control_ipaddr']

        tmp['target_ipaddr'] = end1_ipaddr
        tmp['bridge'] = end1_bridge
        tmp['sdn_control_ipaddr'] = end2_sdn
        self._configure_ovs_bridges(tmp)


        # Add a bridge
        self._bridge_interface.create_bridge(end1_ipaddr, end1_bridge)
        self._bridge_interface.create_bridge(end2_ipaddr, end2_bridge)

        self._bridge_interface.update_bridge_controller(end1_ipaddr, end1_bridge, end1_sdn)
        self._bridge_interface.update_bridge_controller(end2_ipaddr, end2_bridge, end2_sdn)

        # Create Patch Port Pair
        if ovs_config['type'] == "patch":
            box1_port = str(end1_bridge).strip("br").strip("-") + "_2_" + str(end2_bridge).strip("br").strip("-")
            box2_port = str(end2_bridge).strip("br").strip("-") + "_2_" + str(end1_bridge).strip("br").strip("-")

            self._bridge_interface.create_port(end1_ipaddr, end1_bridge, box1_port)
            self._bridge_interface.update_port_type(end1_ipaddr, box1_port, "patch")
            self._bridge_interface.update_port_option(end1_ipaddr, box1_port, "peer", box2_port)

            self._bridge_interface.create_port(end2_ipaddr, end2_bridge, box2_port)
            self._bridge_interface.update_port_type(end2_ipaddr, box2_port, "patch")
            self._bridge_interface.update_port_option(end2_ipaddr, box2_port, "peer", box1_port)

        # Create VxLAN Port Pair
        elif ovs_config['type'] == "vxlan":
            box1_port = end1_box + "_to_" + end2_box
            box2_port = end2_box + "_to_" + end1_box
            end1_vtep = ovs_config['end1_vtep']
            end2_vtep = ovs_config['end2_vtep']

            self._bridge_interface.create_port(end1_ipaddr, end1_bridge, box1_port)
            self._bridge_interface.update_port_type(end1_ipaddr, box1_port, "patch")
            self._bridge_interface.update_port_option(end1_ipaddr, box1_port, "key", 33333)
            self._bridge_interface.update_port_option(end1_ipaddr, box1_port, "remote_ip", end1_vtep)

            self._bridge_interface.create_port(end2_ipaddr, end2_bridge, box2_port)
            self._bridge_interface.update_port_type(end2_ipaddr, box2_port, "patch")
            self._bridge_interface.update_port_option(end2_ipaddr, box2_port, "key", 33333)
            self._bridge_interface.update_port_option(end2_ipaddr, box2_port, "remote_ip", end2_vtep)

    def get_bridge_graph(self, box_ip):
        # ovs-vsctl list-br
        br_graph = networking_graph.BridgeGraph()

        for bridge_name in self._bridge_interface.read_bridge_list(box_ip):
            br_vertex = br_graph.add_vertex(bridge_name)

            port_list = self._bridge_interface.read_port_list(box_ip, bridge_name)
            for port_name in port_list:
                brtype = self._bridge_interface.read_ovsdb_table(box_ip, "interface", port_name, "type")

                port_opt = dict()
                port_opt["type"] = brtype
                port_opt["peer"] = None

                if brtype == "patch":
                    bropt = self._bridge_interface.read_ovsdb_table(box_ip, "interface", port_name, "options:peer")
                    peer_port = bropt.strip("\"")
                    peer_bridge = self._bridge_interface.read_bridge_with_port(box_ip, peer_port)
                    port_opt["peer"] = peer_bridge
                    br_graph.add_edge(bridge_name, peer_bridge)

                elif brtype == "vxlan":
                    bropt = self._bridge_interface.read_ovsdb_table(box_ip, "interface", port_name, "options:remote_ip")
                    peer_ip = bropt.strip("\"")
                    port_opt["peer"] = peer_ip

                br_vertex.add_port(port_name, port_opt)
                br_vertex.add_ext_port(port_name, port_opt)
        return br_graph

    def config_remote_ovsdb(self, __box):
        # Need to implement
        pass

if __name__ == "__main__":
    tmp = "br-test"
    print str(tmp).strip("br").strip("-")
