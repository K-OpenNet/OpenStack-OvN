import logging

import layer2_bridge
import layer2_flow
from utils import util


class OvN:
    def __init__(self):
        self.logger = None
        self.initialize_logger()

        self._ovn_setting = None
        self._net_template = None
        self._boxes_info = None

        self._sdn_controller = None
        self._util = util.Utils()

        self._bridge_graphs = dict()
        self._interconnect_list = list()

        self._bridge_module = None
        self._flow_module = None


    def initialize_logger(self):
        self.logger = logging.getLogger("ovn")
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        self.logger.addHandler(sh)

    def start(self):
        self.load_files()
        self.create_modules()
        self.get_current_configuration()
        self.provision_with_modules()

    def load_files(self):
        try:
            self.load_ovn_setting()
            self.load_network_template()
            self.load_boxes_setting()
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

    def load_ovn_setting(self):
        self._ovn_setting = self._util.parse_yaml_file("setting.yaml")

    def load_network_template(self):
        self._net_template = self._util.parse_yaml_file(self._ovn_setting['networking_template'])

    def load_boxes_setting(self):
        self._boxes_info = self._util.parse_yaml_file(self._ovn_setting['box_information'])

    def create_modules(self):
        self.create_bridge_module()
        self.create_flow_module()

    def create_bridge_module(self):
        self._bridge_module = layer2_bridge.L2BridgeController()

    def create_flow_module(self):
        self._flow_module = layer2_flow.L2FlowController(self._ovn_setting['sdn_controller'])

    def get_current_configuration(self):
        for box in self._boxes_info:
            br_graph = self._bridge_module.get_bridge_graph(box["ipaddr"])
            self._bridge_graphs[box["hostname"]] = br_graph
        # Create site graph (VXLAN Tunnels)

    def provision_with_modules(self):
        for e in self._net_template:
            t = e['type']
            if t in ['bridge']:
                self.provision_bridge(e)
            elif t in ['patch', 'vxlan']:
                self.provision_port(e)
            elif t in ['flow']:
                self.provision_flow(e)
            else:
                self.logger.error("Type " + e['type'] + " is not supported")

    # Provision Bridge
    def provision_bridge(self, be):
        self.logger.debug("Provision() - Configure OVS Bridges, config: " + be.__str__())
        self.add_box_info_to_bridge_element(be)
        self._bridge_module.provision(be)

    def add_box_info_to_bridge_element(self, be):
        self.create_bridge_target_box_dict(be)
        self.set_sdn_control_ipaddr_to_element(be)

    def create_bridge_target_box_dict(self, be):
        target_dict = dict()
        target_dict['box'] = be['target']
        target_dict['bridge'] = be['bridge']
        target_dict['ipaddr'] = self.get_box_ipaddr(be['target'])
        be['target'] = target_dict

    # Provision Ports
    def provision_port(self, pe):
        self.logger.debug("Provision() - Configure OVS Ports, config: " + pe.__str__())
        self.add_box_info_to_port_element(pe)
        self._bridge_module.provision(pe)

    def add_box_info_to_port_element(self, pe):
        self.set_separated_box_bridge_names_in_port_element(pe)
        self.set_boxes_ipaddr_to_port_element(pe)
        self.set_sdn_control_ipaddr_to_element(pe)

    def set_separated_box_bridge_names_in_port_element(self, pe):
        pe['end1'] = self.get_separated_box_bridge_name(pe['end1'])
        pe['end2'] = self.get_separated_box_bridge_name(pe['end2'])

    def set_boxes_ipaddr_to_port_element(self, pe):
        pe['end1'] = self.get_box_bridge_name_with_box_ipaddr(pe['end1'])
        pe['end2'] = self.get_box_bridge_name_with_box_ipaddr(pe['end2'])

    # Provision Flow
    def provision_flow(self, fe):
        self.logger.info("Provision() - Configure L2 Flow for OVS, config: " + fe.__str__())
        self.add_box_info_to_flow_element(fe)
        self._flow_module.config_l2flow(fe)

    def add_box_info_to_flow_element(self, fe):
        self.set_separated_box_bridge_names_in_flow_element(fe)
        self.set_boxes_ipaddr_to_flow_element(fe)
        self.set_sdn_control_ipaddr_to_element(fe)
        pass

    def set_separated_box_bridge_names_in_flow_element(self, fe):
        fe['target'] = self.get_separated_box_bridge_name(fe['target'])
        fe['end1'] = self.get_separated_box_bridge_name(fe['end1'])
        fe['end2'] = self.get_separated_box_bridge_name(fe['end2'])

    def set_boxes_ipaddr_to_flow_element(self, fe):
        fe['target'] = self.get_box_bridge_name_with_box_ipaddr(fe['target'])
        fe['end1'] = self.get_box_bridge_name_with_box_ipaddr(fe['end1'])
        fe['end2'] = self.get_box_bridge_name_with_box_ipaddr(fe['end2'])

    # Shared by Provisioning Methods
    def get_separated_box_bridge_name(self, str):
        l = str.split('.')
        return {"box": l[0], "bridge": l[1]}

    def set_sdn_control_ipaddr_to_element(self, e):
        e['sdn_control_ipaddr'] = self._sdn_controller['ipaddr']

    def get_box_bridge_name_with_box_ipaddr(self, e):
        boxname = e['box']
        e['ipaddr'] = self.get_box_ipaddr(boxname)
        return e

    def get_box_ipaddr(self, boxname):
        box_info = self.get_box_info(boxname)
        return box_info['ipaddr']

    def get_box_info(self, boxname):
        for box_info in self._boxes_info:
            if box_info['hostname'] == boxname:
                self.logger.debug("get_box(): " + box_info.__str__())
                return box_info

        self.logger.error("In " + self._ovn_setting['box_config_file'] +
                          ", Box is not defined: " + boxname)
        return None


if __name__ == "__main__":
    ovn = OvN()
    ovn.start()
