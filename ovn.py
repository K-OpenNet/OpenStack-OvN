import logging
import yaml
import subprocess
import shlex
import os

import layer2_bridge
import layer2_flow


class OvN:
    def __init__(self):
        self._setting = None
        self.logger = None

        self._bridge_control = None
        self._flow_control = None

        self.initialize_controller()
        self.initialize_logger()

    def initialize_controller(self):
        self._bridge_control = layer2_bridge.L2BridgeController()
        self._flow_control = layer2_flow.L2FlowController()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def yaml_parser(self, __file):
        """ Parse the data from YAML template. """
        with open(__file, 'r') as stream:
            try:
                file_str = stream.read()
                yaml.load(file_str)
            except yaml.YAMLError, exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    self.logger.error(("YAML Format Error: " + __file
                                       + " (Position: line %s, column %s)" %
                                       (mark.line + 1, mark.column + 1)))
                    return None
        self.logger.info("Parse YAML from the file " + __file)
        return yaml.load(file_str)

    def start(self):
        self._setting = self.yaml_parser("setting.yaml")
        if not self._setting:
            exit(1)

        try:
            net_template = self.yaml_parser(
                self._setting['networking_template_file'])
        except AttributeError, exc:
            self.logger.error(exc.message)
            exit(1)

        for net in net_template:
            if net['type'] in ['patch', 'vxlan']:
                self.config_ovs(net)

    def config_ovs(self, __ovs):
        self.logger.debug("Configure OVS, config: " + __ovs.__str__())

        # Need to add codes to check valid OVS configuration format
        self.check_ovs_format()

        try:
            # Split box and bridge
            end1 = __ovs['end1'].split('.')
            end2 = __ovs['end2'].split('.')

            end1_name = end1[0]
            end2_name = end2[0]

            end1_bridge = end1[1]
            end2_bridge = end2[1]

            # Load box configuration
            box1 = self.get_box(end1_name)
            box2 = self.get_box(end2_name)

            # Check Box connectivity
            if self.check_box_connect(box1['ipaddr']) is 1 \
                    or self.check_box_connect(box2['ipaddr']) is 1:
                return None

            if self._bridge_control.check_remote_ovsdb(box1['ipaddr']) is 1:
                self.config_remote_ovsdb(box1)
                return None

            if self._bridge_control.check_remote_ovsdb(box2['ipaddr']) is 1:
                self.config_remote_ovsdb(box2)
                return None

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

        # Add a bridge
        self._bridge_control.add_bridge(box1['ipaddr'], end1_bridge)
        self._bridge_control.add_bridge(box2['ipaddr'], end2_bridge)

        # Add a port pair
        if __ovs['type'] == "patch":
            box1_port = end1_bridge + "_to_" + end2_bridge
            box2_port = end2_bridge + "_to_" + end1_bridge
            self._bridge_control.add_patch_port_pair(
                                                    __box1_ip=box1['ipaddr'],
                                                    __box1_br=end1_bridge,
                                                    __box1_port=box1_port,
                                                    __box2_ip=box2['ipaddr'],
                                                    __box2_br=end2_bridge,
                                                    __box2_port=box2_port)
        elif __ovs['type'] == "vxlan":
            box1_port = end1_name + "_to_" + end2_name
            box2_port = end2_name + "_to_" + end1_name
            self._bridge_control.add_vxlan_port_pair(
                                            __box1_ip=box1['ipaddr'],
                                            __box1_vtep_ip=box1['vtep_ipaddr'],
                                            __box1_br=end1_bridge,
                                            __box1_port=box1_port,
                                            __box2_ip=box2['ipaddr'],
                                            __box2_vtep_ip=box2['vtep_ipaddr'],
                                            __box2_br=end2_bridge,
                                            __box2_port=box2_port)

    def configure_l2flow(self, __ovs):
        self.logger.debug("Configure L2 Flow for OVS, config: "
                          + __ovs.__str__())


    def check_ovs_format(self, __ovs):
        # Need to implement
        pass

    def check_box_connect(self, __remote_ip):
        command = ['ping', '-c 1', '-W 1', __remote_ip]
        (returncode, cmdout, cmderr) = self.shell_command(command)

        if returncode is 0:
            self.logger.error("Box is connectable: " + __remote_ip)
        elif returncode is 1:
            self.logger.error("Box is not connectable: " + __remote_ip)

        return returncode

    def config_remote_ovsdb(self, __box):
        # Need to implement
        pass

    def get_box(self, __hostname):
        try:
            box_config = self.yaml_parser(self._setting['box_config_file'])
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

    def shell_command(self, __cmd):
        self.logger.debug("Shell command: " + __cmd.__str__())
        if isinstance(__cmd, basestring):
            subproc = subprocess.Popen(shlex.split(__cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
        elif isinstance(__cmd, dict):
            subproc = subprocess.Popen(__cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        (cmdout, cmderr) = subproc.communicate()
        return subproc.returncode, cmdout, cmderr


if __name__ == "__main__":
    ovn = OvN()
    ovn.start()