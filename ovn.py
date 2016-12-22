import logging
import layer2_bridge
import layer2_flow
import util


class OvN:
    def __init__(self):
        self._setting = None
        self.logger = None
        self._util = None

        self._bridge_control = None
        self._flow_control = None

        self.initialize_controller()
        self.initialize_logger()

    def initialize_controller(self):
        self._bridge_control = layer2_bridge.L2BridgeController()
        self._flow_control = layer2_flow.L2FlowController()
        self._util = util.Utils()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def start(self):
        net_template = None
        self._setting = self._util.yaml_parser("setting.yaml")
        if not self._setting:
            exit(1)

        try:
            net_template = self.util.yaml_parser(self._setting['networking_template_file'])
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

        for net in net_template:
            if net['type'] in ['patch', 'vxlan']:
                parse_net = self._bridge_control.parse_ovs(net)
                box1 = self.get_box(parse_net['end1_hostname'])
                box2 = self.get_box(parse_net['end2_hostname'])
                parse_net['end1_ipaddr'] = box1['ipaddr']
                parse_net['end2_ipaddr'] = box2['ipaddr']
                self._bridge_control.config_ovs(parse_net)

    def configure_l2flow(self, __ovs):
        self.logger.debug("Configure L2 Flow for OVS, config: "
                          + __ovs.__str__())

    def get_box(self, __hostname):
        box_config = None
        try:
            box_config = self._util.yaml_parser(self._setting['box_config_file'])
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

        for box in box_config:
            if box['hostname'] == __hostname:
                return box

        self.logger.error("In " + self._setting['box_config_file'] +
                          "Box is not defined: " +
                          __hostname)
        return None

if __name__ == "__main__":
    ovn = OvN()
    ovn.start()
