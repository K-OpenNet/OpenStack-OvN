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
        except AttributeError as exc:
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

    def parse_networking_template(self):
        for elem in self._net_template:
            self._make_networking_element(elem)

    def _make_networking_element(self, elem):
        elem_keys = elem.keys()
        for k in elem_keys:
            if k == "type":
                pass
            elif k in ["target", "end1", "end2"]:
                elem[k] = self.get_elem_dict_from(elem[k])
                elem[k]["ipaddr"] = self.get_box_ipaddr(elem[k]["box"])
                elem[k]["sdn_control_ipaddr"] = self.get_sdn_control_ipaddr()
            elif k == "opt":
                pass

    def provision_with_modules(self):
        for e in self._net_template:
            t = e['type']
            if t in ['bridge', 'port', 'patch', 'vxlan']:
                self.provision_bridge(e)
            elif t in ['flow']:
                self.provision_flow(e)
            else:
                self.logger.error("Type " + e['type'] + " is not supported")

    # Provision Bridge
    def provision_bridge(self, be):
        self.logger.debug("Provision() - Configure OVS Bridges, config: " + be.__str__())
        self._bridge_module.provision(be)

    # Provision Flow
    def provision_flow(self, fe):
        self.logger.info("Provision() - Configure L2 Flow for OVS, config: " + fe.__str__())
        #self._flow_module.provision(fe)

    # Shared by Provisioning Methods
    def get_elem_dict_from(self, e):
        e_dict = dict()
        l = e.split('.')
        for i in l.__len__:
            if i == 0:
                e_dict["box"] = l[i]
            elif i == 1:
                e_dict["bridge"] = l[i]
            elif i == 2:
                e_dict["port"] = l[i]
            else:
                pass
        return e_dict

    def get_sdn_control_ipaddr(self):
        return self._sdn_controller['ipaddr']

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

if __name__ == "__main__":
    ovn = OvN()
    ovn.start()
