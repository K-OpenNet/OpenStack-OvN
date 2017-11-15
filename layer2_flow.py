import logging
import ifaces.odl_api as odl

class L2FlowController:
    def __init__(self, sdn_controller):
        self.logger = logging.getLogger("ovn.control.l2flow")
        self._sdn = sdn_controller
        self._flow_api = odl.ODL_API(self._sdn['id'], self._sdn['pw'], self._sdn['ipaddr'])

    def provision(self, fe):
        # List all required procedure to configure L2 flows
        # Check connectivity to SDN Controller
        # Need to find "box_ip" "bridge" / "table_id" "inport" "outport"
        # Get inport from port
        # Get outport from port
        # Create OpenFlow rule
        pass

    def config_l2flow(self, flow_config):
        self.logger.debug("config_l2flow() configure OpenFlow rule using SDN Controller. Parsed Template: "
                          + flow_config.__str__())

        if flow_config['end1_box'] == flow_config['end2_box']: # Two bridges are inside the target box
            inport_name = str(flow_config['target_bridge']).strip("br").strip("-") + "_2_" \
                          + str(flow_config['end1_bridge']).strip("br").strip("-")
            outport_name = str(flow_config['target_bridge']).strip("br").strip("-") + "_2_" \
                           + str(flow_config['end2_bridge']).strip("br").strip("-")

        else:   # End2 bridge is in another box
            inport_name = str(flow_config['target_bridge']) + "_2_" + str(flow_config['end1_box'])
            outport_name = str(flow_config['target']) + "_2_" + str(flow_config['end2_box'])

        self.logger.debug("config_l2flow() target_bridge: " + flow_config['target_bridge'] +
                          " from_port: " + inport_name +
                          " to_port: " + outport_name)
        inport = self._flow_api.get_port_number(flow_config['target_ipaddr'], inport_name)
        outport = self._flow_api.get_port_number(flow_config['target_ipaddr'], outport_name)

        self.logger.debug("inport: "+inport + " outport: " + outport)

        # Currently We use Table #1. When we add multi-tenant support, table_id has to be set according to a tenant.
        return self._flow_api.create_flow(flow_config['target_ipaddr'], flow_config['target_bridge'],
                                          "1", inport, outport)