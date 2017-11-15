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
            print(err.message)
        except AttributeError as err:
            print(err.message)

    def check_template_format(self, elem):
        # Need to be implemented
        # bridge / port type check
        # Check Common Error
        # Check Type Specific Error
        elem_keys = elem.keys()
        if elem['type'] == "bridge:":
            if "target" not in elem_keys:
                raise ValueError("Bridge element have to contain \"target: box.bridge\"")
            else:
                target_keys = elem['target'].keys()
                if "box" not in target_keys or "bridge" not in target_keys:
                    raise ValueError("Bridge element have to contain \"target: box.bridge\"")
            if "end1" in elem_keys or "end2" in elem_keys:
                self.logger.warning("Bridge element doesn't require end1/end2. Those are ignored")

        elif elem['type'] == "port":
            if "target" not in elem_keys:
                raise ValueError("Normal port element have to contain \"target: box.bridge.port\"")
            else:
                target_keys = elem['target'].keys()
                if "box" not in target_keys or "bridge" not in target_keys \
                        or "port" not in target_keys:
                    raise ValueError("Normal port element have to contain \"target: box.bridge.port\"")
            if "end1" in elem_keys or "end2" in elem_keys:
                self.logger.warning("Normal port element doesn't require end1/end2. Those are ignored")

        elif elem['type'] == "vxlan":
            # Field Check
            # Two endpoints of vxlan port pair should be located in different hosts
            if "end1" not in elem_keys or "end2" not in elem_keys:
                raise ValueError("VXLAN port element have to contain \"end1: box.bridge\" / \"end2: box.bridge\"")
            else:
                end_keys = elem['end1'].keys()
                if "box" not in end_keys or "bridge" not in end_keys:
                    raise ValueError("VXLAN port element have to contain \"end1: box.bridge\"")
                end_keys = elem['end2'].keys()
                if "box" not in end_keys or "bridge" not in end_keys:
                    raise ValueError("VXLAN port element have to contain \"end2: box.bridge\"")

                if elem['end1']['box'] is elem['end2']['box']:
                    raise ValueError("VXLAN port pair should be configured at different boxes")

            if "target" in elem_keys:
                self.logger.warning("VXLAN port element doesn't require contain target. Those are ignored")

        elif elem['type'] == "patch":
            if "end1" not in elem_keys or "end2" not in elem_keys:
                raise ValueError("VXLAN port element have to contain \"end1: box.bridge\" / \"end2: box.bridge\"")
            else:
                end_keys = elem['end1'].keys()
                if "box" not in end_keys or "bridge" not in end_keys:
                    raise ValueError("Patch port element have to contain \"end1: box.bridge\"")
                end_keys = elem['end2'].keys()
                if "box" not in end_keys or "bridge" not in end_keys:
                    raise ValueError("Patch port element have to contain \"end2: box.bridge\"")

                if elem['end1']['box'] is not elem['end2']['box']:
                    raise ValueError("Patch port pair have to be configured in same box")
                elif elem['end1']['box'] is elem['end2']['box']:
                    raise ValueError("Patch port pair have to be configured at two different bridges")

            if "target" in elem_keys:
                self.logger.warning("Patch port element doesn't require contain target. Those are ignored")
        else:
            raise ValueError("Type " + elem['type'] + " is not supported")

    def _check_connectivity(self, be):
        ipaddr_list = self._get_ipaddr_list(be)
        self._check_ip_connectivity(ipaddr_list)
        self._check_ovsdb_connectivity(ipaddr_list)

    def _get_ipaddr_list(self, be):
        ipaddr_list = list()
        be_keys = be.keys()
        for k in be_keys:
            if k in ["target", "end1", "end2"]:
                ipaddr_list.append(self._get_box_ipaddr_from(be[k]))
        return ipaddr_list

    def _check_ip_connectivity(self, ipaddr_list):
        for ipaddr in ipaddr_list:
            returncode = self._util.check_ip_connectivity(ipaddr)
            if returncode is 0:
                self.logger.info("IP address is reachable: " + ipaddr)
            elif returncode is 1:
                raise ValueError("IP address is not reachable: " + ipaddr)

    def _check_ovsdb_connectivity(self, ipaddr):
        (returncode, cmdout, cmderr) = self._bridge_interface.read_ovs_config(ipaddr)
        if returncode is 0:
            self.logger.info("OVSDB is reachable: " + ipaddr)
        elif returncode is 1:
            raise ValueError("OVSDB is not reachable: " + ipaddr)

    def _do_provision(self, elem):
        try:
            if elem['type'] == "bridge":
                self._add_new_bridge(elem)
            elif elem['type'] == "port":
                self._add_normal_port(elem)
            elif elem['type'] == "patch":
                self._add_patch_port_pair(elem)
            elif elem['type'] == "vxlan":
                self._add_vxlan_port_pair(elem)
        except ValueError as e:
            self.logger.error(e.args)
            # finally:
            # I'll add codes to remove all bridges/ports configured from this execution

    def _add_new_bridge(self, be):
        box_ipaddr = self._get_box_ipaddr_from(be['target'])
        bridge_name = self._get_bridge_from(be['target'])
        sdn_control_ipaddr = self._get_sdn_control_ipaddr(be['target'])
        self._bridge_interface.create_bridge(box_ipaddr, bridge_name)
        self._bridge_interface.update_bridge_controller(box_ipaddr, bridge_name, sdn_control_ipaddr)

    def _add_normal_port(self, pe):
        # Validate the given element can be configurable
        box_ip = self._get_box_ipaddr_from(pe['end1'])
        bridge = self._get_bridge_from(pe['end1'])
        pt_name = self._get_port_from(pe['end1'])
        self._create_port(box_ip, bridge, pt_name)

    def _add_vxlan_port_pair(self, pe):
        self._add_vxlan_port(pe['end1'], pe['end2'])
        self._add_vxlan_port(pe['end2'], pe['end1'])

    def _add_vxlan_port(self, from_pt, to_pt, vxlan_opt=None):
        pt_name = self._create_port_name("vxlan", from_pt, to_pt)
        box_ip = self._get_box_ipaddr_from(from_pt)
        bridge = self._get_bridge_from(from_pt['bridge'])
        peer_ip = self._get_box_ipaddr_from(to_pt)

        self._create_port(box_ip, bridge, pt_name)
        self._bridge_interface.update_port_type(box_ip, pt_name, "vxlan")
        self._bridge_interface.update_port_option(box_ip, pt_name, "key", 33333)
        self._bridge_interface.update_port_option(box_ip, pt_name, "remote_ip", peer_ip)

    def _add_patch_port_pair(self, pe):
        self._add_patch_port(pe['end1'], pe['end2'])
        self._add_patch_port(pe['end2'], pe['end1'])

    def _add_patch_port(self, from_pt, to_pt):
        pt_name = self._create_port_name("patch", from_pt, to_pt)
        peer_pt_name = self._create_port_name("patch", to_pt, from_pt)
        box_ip = self._get_box_ipaddr_from(from_pt)
        bridge = self._get_bridge_from(from_pt['bridge'])

        self._create_port(box_ip, bridge, pt_name)
        self._bridge_interface.update_port_type(box_ip, pt_name, "patch")
        self._bridge_interface.update_port_option(box_ip, pt_name, "peer", peer_pt_name)

    def _create_port_name(self, type, from_end, to_end):
        port_name = str()
        if type == "patch":
            port_name = str(from_end["bridge"]).strip("br").strip("-") + "_2_" \
                        + str(to_end["bridge"]).strip("br").strip("-")
        elif type == "vxlan":
            port_name = str(from_end["box"]) + "_2_" + str(to_end["box"])
        return port_name

    def _create_port(self, box_ip, bridge, port_name):
        self._create_bridge_if_not_exist(box_ip, bridge)
        self._bridge_interface.create_port(box_ip, bridge, port_name)

    def _create_bridge_if_not_exist(self, box_ip, bridge):
        br_list = self._bridge_interface.read_bridge_list(box_ip)
        if bridge not in br_list:
            self.logger.info("Bridge " + bridge + " is not existed in " + box_ip +
                             ". The bridge will be created")
            self._bridge_interface.create_bridge(box_ip, bridge)

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

    def _get_box_ipaddr_from(self, element):
        return element['ipaddr']

    def _get_bridge_from(self, element):
        return element['bridge']

    def _get_port_from(self, element):
        return element['port']

    def _get_sdn_control_ipaddr(self, element):
        return element['sdn_control_ipaddr']


if __name__ == "__main__":
    tmp = "br-test"
    print(str(tmp).strip("br").strip("-"))
