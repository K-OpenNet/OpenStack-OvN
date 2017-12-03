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
        self._pre_check_before_provision(be)
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
        self.logger.debug("Check template format: {}".format(elem))
        if elem['type'] == "bridge":
            self._check_bridge_template_format(elem)
        elif elem['type'] == "port":
            self._check_normal_port_template_format(elem)
        elif elem['type'] == "vxlan":
            self._check_vxlan_port_template_format(elem)
        elif elem['type'] == "patch":
            self._check_patch_port_template_format(elem)
        else:
            raise ValueError("Type " + elem['type'] + " is not supported")

    def _check_bridge_template_format(self, elem):
        self._check_exist_target_elem_in(elem.keys())
        self._check_keys_in_list(["box", "bridge"], elem['target'].keys())
        self._check_exist_not_required_keys(["end1", "end2"], elem.keys())

    def _check_normal_port_template_format(self, elem):
        self._check_exist_target_elem_in(elem.keys())
        self._check_keys_in_list(["box", "bridge", "port"], elem['target'].keys())
        self._check_exist_not_required_keys(["end1", "end2"], elem.keys())

    def _check_vxlan_port_template_format(self, elem):
        self._check_keys_in_list(["end1", "end2"], elem.keys())
        self._check_keys_in_list(["box", "bridge"], elem['end1'].keys())
        self._check_keys_in_list(["box", "bridge"], elem['end2'].keys())
        if elem['end1']['box'] == elem['end2']['box']:
            raise ValueError("VXLAN port pair should be configured at different boxes")
        self._check_exist_not_required_keys(["target"], elem.keys())

    def _check_patch_port_template_format(self, elem):
        self._check_keys_in_list(["end1", "end2"], elem.keys())
        self._check_keys_in_list(["box", "bridge"], elem['end1'].keys())
        self._check_keys_in_list(["box", "bridge"], elem['end2'].keys())
        if elem['end1']['box'] != elem['end2']['box']:
            raise ValueError("Patch port pair have to be configured in same box")
        elif elem['end1']['bridge'] == elem['end2']['bridge']:
            raise ValueError("Patch port pair have to be configured at two different bridges")
        self._check_exist_not_required_keys(["target"], elem.keys())

    def _check_exist_target_elem_in(self, elem_keys):
        self._check_keys_in_list(["target"], elem_keys)

    def _check_keys_in_list(self, keys, key_list):
        for k in keys:
            if k not in key_list:
                raise ValueError()

    def _check_exist_not_required_keys(self, not_req_keys, elem_keys):
        for k in not_req_keys:
            if k in elem_keys:
                self.logger.warn("Key " + k +" is not required!")

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

    def _check_ovsdb_connectivity(self, ipaddr_list):
        for ipaddr in ipaddr_list:
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
            raise TypeError("Type " + elem['type'] + "is not supported by OvN")
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
        box_ip = self._get_box_ipaddr_from(pe['target'])
        bridge = self._get_bridge_from(pe['target'])
        pt_name = self._get_port_from(pe['target'])
        self._create_port(box_ip, bridge, pt_name)

    def _add_patch_port_pair(self, pe):
        self._add_patch_port(pe['end1'], pe['end2'])
        self._add_patch_port(pe['end2'], pe['end1'])

    def _add_patch_port(self, from_end, to_end):
        pt_name = self._create_port_name("patch", from_end, to_end)
        peer_pt_name = self._create_port_name("patch", to_end, from_end)
        box_ip = self._get_box_ipaddr_from(from_end)
        bridge = self._get_bridge_from(from_end)

        self._create_port(box_ip, bridge, pt_name)
        self._bridge_interface.update_port_type(box_ip, pt_name, "patch")
        self._bridge_interface.update_port_option(box_ip, pt_name, "peer", peer_pt_name)

    def _add_vxlan_port_pair(self, pe):
        self._add_vxlan_port(pe['end1'], pe['end2'])
        self._add_vxlan_port(pe['end2'], pe['end1'])

    def _add_vxlan_port(self, from_end, to_end, vxlan_opt=None):
        pt_name = self._create_port_name("vxlan", from_end, to_end)
        box_ip = self._get_box_ipaddr_from(from_end)
        bridge = self._get_bridge_from(from_end)
        peer_ip = self._get_box_ipaddr_from(to_end)

        self._create_port(box_ip, bridge, pt_name)
        self._bridge_interface.update_port_type(box_ip, pt_name, "vxlan")
        self._bridge_interface.update_port_option(box_ip, pt_name, "key", str(33333))
        self._bridge_interface.update_port_option(box_ip, pt_name, "remote_ip", peer_ip)


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

    def config_remote_ovsdb(self, _box):
        # Need to implement
        pass

    def _get_box_ipaddr_from(self, end):
        return end['ipaddr']

    def _get_bridge_from(self, end):
        return end['bridge']

    def _get_port_from(self, end):
        return end['port']

    def _get_sdn_control_ipaddr(self, end):
        return end['sdn_control_ipaddr']

    def get_bridge_graph(self, box_info):
        # ovs-vsctl list-br
        # Create bridge vertices
        # Add ports in each bridge vertices
        # Add edges between two ports
        br_graph = networking_graph.BridgeGraph()
        for box in box_info:
            self._get_brgraph_of_box(box['ipaddr'])

    def _get_brgraph_of_box(self, box_ip):
        br_graph = networking_graph.BridgeGraph()
        br_in_box = self._bridge_interface.read_bridge_list(box_ip)
        for br in br_in_box:

            pass

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

    def unprovision(self, e):
        e_type = e['type']
        if e_type == 'bridge':
            self._delete_bridge(e)
        elif e_type == 'port':
            self._delete_normal_port(e)
        elif e_type == 'vxlan':
            self._delete_vxlan_port_pair(e)
        elif e_type == 'patch':
            self._delete_patch_port_pair(e)
        else:
            raise TypeError("Type "+ e_type + " is not supported by OvN")

    def _delete_bridge(self, be):
        box_ipaddr = self._get_box_ipaddr_from(be['target'])
        bridge_name = self._get_bridge_from(be['target'])
        self._bridge_interface.delete_bridge(box_ipaddr, bridge_name)

    def _delete_normal_port(self, pe):
        box_ip = self._get_box_ipaddr_from(pe['target'])
        bridge = self._get_bridge_from(pe['target'])
        pt_name = self._get_port_from(pe['target'])
        self._bridge_interface.delete_port(box_ip, bridge, pt_name)

    def _delete_vxlan_port_pair(self, pe):
        self._delete_patch_port(pe['end1'], pe['end2'])
        self._delete_patch_port(pe['end2'], pe['end1'])

    def _delet_vxlan_port(self, from_end, to_end):
        pt_name = self._create_port_name("patch", from_end, to_end)
        box_ip = self._get_box_ipaddr_from(from_end)
        bridge = self._get_bridge_from(from_end)
        self._bridge_interface.delete_port(box_ip, bridge, pt_name)

    def _delete_patch_port_pair(self, pe):
        self._delete_patch_port(pe['end1'], pe['end2'])
        self._delete_patch_port(pe['end2'], pe['end1'])

    def _delete_patch_port(self, from_end, to_end):
        pt_name = self._create_port_name("patch", from_end, to_end)
        box_ip = self._get_box_ipaddr_from(from_end)
        bridge = self._get_bridge_from(from_end)
        self._bridge_interface.delete_port(box_ip, bridge, pt_name)

if __name__ == "__main__":
    tmp = "br-test"
    print(str(tmp).strip("br").strip("-"))
