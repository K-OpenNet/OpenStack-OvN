import logging
import subprocess
import shlex


class L2FlowController:
    def __init__(self):
        self._sdn_ipaddr = None
        self.logger = None
        self.initialize_logger()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def initialize_setting(self, __sdn_ip):
        self._sdn_ipaddr = __sdn_ip

    def parse_flow_config(self, flow_config):
        # Need to parse host_ip, bridge, table_id, inport, outport
        # host_ip <- filled by "ovn.py"


        self.logger.debug("Parse Networking Template for OVS, config: " + flow_config.__str__())

        try:
            # Split box and bridge
            end1 = flow_config['end1'].split('.')
            end2 = flow_config['end2'].split('.')

            flow_config['end1_name'] = end1[0]
            flow_config['end1_bridge'] = end1[1]

            flow_config['end2_name'] = end2[0]
            flow_config['end2_bridge'] = end2[1]

            return flow_config

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None
        pass

    def config_l2flow(self, flow_config):
        pass

    def set_patch_flow(self):
        # Get DPIDs of bridge1 and bridge 2
        # Get port numbers of port1 and port2
        # check intent is exists
        # create point to point intent for two ports
        pass

    def set_vxlan_flow(self):
        pass

    def get_bridge_dpid(self, __box_ip, __bridge):
        remote_port = "6640"
        command = ["ovs-vsctl",
                   "--db=tcp:" + __box_ip + ":" + remote_port,
                   "get bridge", __bridge, "datapath-id"]
        (returncode, cmdout, cmderr) = self.shell_command(command)

        return "of:"+cmdout

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


