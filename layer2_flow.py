import logging
import subprocess
import shlex
import ifaces.odl_api as odl
from ifaces.odl_api import ODL_API


class L2FlowController:
    def __init__(self, sdn_controller):
        self.logger = logging.getLogger("ovn.control.l2flow")
        self._sdn = sdn_controller
        self._flow_api = odl.ODL_API(self._sdn['id'], self._sdn['pw'], self._sdn['ipaddr'])

    def parse_template(self, flow_config):
        # Need to parse host_ip, bridge, table_id, inport, outport
        # host_ip <- filled by "ovn.py"
        self.logger.debug("Parse Networking Template for OVS, config: " + flow_config.__str__())

        try:
            # Split box and bridge
            tmp = flow_config['target'].split('.')
            flow_config['target_box'] = tmp[0]
            flow_config['target_bridge'] = tmp[1]

            tmp = flow_config['end1'].split('.')
            flow_config['end1_box'] = tmp[0]
            flow_config['end1_bridge'] = tmp[1]

            tmp = flow_config['end2'].split('.')
            flow_config['end2_box'] = tmp[0]
            flow_config['end2_bridge'] = tmp[1]

        except AttributeError, exc:
            self.logger.error(exc.message)
            return None

        return flow_config

    def config_l2flow(self, flow_config):
        self.logger.debug("config_l2flow() configure OpenFlow rule using SDN Controller. Parsed Template: " + flow_config.__str__())

        if flow_config['end1_box'] == flow_config['end2_box']: # Two bridges are inside the target box
            inport_name = str(flow_config['target_bridge']).strip("br").strip("-") + "_2_" + str(flow_config['end1_bridge']).strip("br").strip("-")
            outport_name = str(flow_config['target_bridge']).strip("br").strip("-") + "_2_" + str(flow_config['end2_bridge']).strip("br").strip("-")

        else:   # End2 bridge is in another box
            inport_name = str(flow_config['target_bridge']) + "_2_" + str(flow_config['end1_box'])
            outport_name = str(flow_config['target']) + "_2_" + str(flow_config['end2_box'])

        self.logger.debug("config_l2flow() target_bridge: " + flow_config['target_bridge'] + " from_port: " + inport_name + " to_port: " + outport_name)
        inport = self._flow_api.get_port_number(flow_config['target_ipaddr'], inport_name)
        outport = self._flow_api.get_port_number(flow_config['target_ipaddr'], outport_name)

        self.logger.debug("inport: "+inport + " outport: " + outport)
        self._flow_api.create_flow(flow_config['target_ipaddr'], flow_config['target_bridge'], "2", inport, outport)
        return

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


