import logging
import layer2_bridge
import layer2_flow
import util


class OvN:
    def __init__(self):
        self._setting = None
        self._net_template = None
        self._box_config = None
        self._sdn_controller = None
        self.logger = None
        self._util = util.Utils()

        self._bridge_control = None
        self._flow_control = None

        self.initialize_logger()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        if len(self.logger.handlers):
            self.logger.setLevel(logging.DEBUG)
            fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(fm)
            self.logger.addHandler(ch)

    def start(self):
        # Load OvN Setting File
        self._setting = self._util.yaml_parser("setting.yaml")

        if not self._setting:
            exit(1)

        # Load Networking Template File
        try:
            self._net_template = self._util.yaml_parser(self._setting['networking_template_file'])
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

        # Load Box Configuration File
        try:
            self._box_config = self._util.yaml_parser(self._setting['box_config_file'])
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

        self._sdn_controller = self._setting['sdn_controller']

        self.prepare_controllers()
        self.provision()

    def prepare_controllers(self):
        self._bridge_control = layer2_bridge.L2BridgeController()
        self._flow_control = layer2_flow.L2FlowController(self._sdn_controller)

    def provision(self):
        # Parsing Template to Graph (Need to Add)

        for net in self._net_template:
            if net['type'] in ['bridge']:
                self.logger.debug("Provision() - Configure OVS Bridges, config: " + net.__str__())
                ovs_config = net

                # Fill Box specific information (Controllers can't access to box information)
                box_config = self.get_box_config(ovs_config['target'])
                if not box_config:
                    self.logger.warn("provision(), there is no box with the name " + ovs_config['target'])
                    continue
                ovs_config['target_ipaddr'] = box_config['ipaddr']
                ovs_config['sdn_control_ipaddr'] = self._sdn_controller['ipaddr']

                # Trigger configuration
                self._bridge_control.config_l2bridge(ovs_config)

            elif net['type'] in ['patch', 'vxlan']:
                self.logger.debug("Provision() - Configure OVS Ports, config: " + net.__str__())
                # Parsing Template via controller
                ovs_config = self._bridge_control.parse_template(net)

                # Fill Box specific information (Controllers can't access to box information)
                box1_config = self.get_box_config(ovs_config['end1_box'])
                box2_config = self.get_box_config(ovs_config['end2_box'])
                if not box1_config or not box2_config:
                    self.logger.warn("provision(), there is no box with the name " + ovs_config['target'])
                    continue
                ovs_config['end1_ipaddr'] = box1_config['ipaddr']
                ovs_config['end2_ipaddr'] = box2_config['ipaddr']
                ovs_config['sdn_control_ipaddr'] = self._sdn_controller['ipaddr']

                # Trigger configuration
                self._bridge_control.config_l2bridge(ovs_config)

            elif net['type'] == "flow":
                self.logger.info("Provision() - Configure L2 Flow for OVS, config: " + net.__str__())
                # Parsing Template via controller
                flow_config = self._flow_control.parse_template(net)

                # Fill Box specific information (Controllers can't access to box information)
                target_box_config = self.get_box_config(flow_config['target_box'])
                flow_config['target_ipaddr'] = target_box_config['ipaddr']

                # Trigger configuration
                self._flow_control.config_l2flow(flow_config)

    def get_box_config(self, hostname):
        for box in self._box_config:
            if box['hostname'] == hostname:
                self.logger.debug("get_box(): \n" + box.__str__())
                return box

        self.logger.error("In " + self._setting['box_config_file'] +
                          ", Box is not defined: " + hostname)
        return None

if __name__ == "__main__":
    ovn = OvN()
    ovn.start()
