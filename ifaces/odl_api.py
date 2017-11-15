import json
import httplib2
import logging
import time
# import xml_to_dict as xmlparser
from xml.etree import cElementTree


class ODL_API:
    def __init__(self, odl_id, odl_pw, odl_ip):
        self._default_url = "http://" + odl_ip + ":8181"
        self._http_agent = httplib2.Http(".cache")
        self._http_agent.add_credentials(odl_id, odl_pw)
        self.logger = logging.getLogger("ovn.control.l2flow.odl_api")

    def create_flow(self, host_ip, bridge, table_id, inport, outport):
        # Find Bridge ID
        # Find existing Flow ID
        # If the matched Flow is not exist, calculate Flow ID one bigger than the highest flow ID
        # Get Flow list of Bridge ID & Table ID
        # Get the highest flow Id
        # Calculate new flow ID (BiggestID+1)
        # Make dictionary according to ODL flow format
        # Dump the dictionary into JSON string
        # Send HTTP request to ODL

        bridge_id = self._get_bridge_id(host_ip, bridge)

        # Find a flow which has same match rule
        flow_id = self._get_flow_id(bridge_id, table_id, inport, None)

        # Find unassigned flow_id
        if not flow_id:
            u = self._default_url + '/restconf/operational/opendaylight-inventory:nodes/node/' + bridge_id + '/table/' + table_id
            resp, content = self.get(u)
            try:
                flow_content = json.loads(content)
                flows = flow_content["flow-node-inventory:table"][0]
            except KeyError:
                return None

            flows = flows.get('flow')
            if flows:
                klist = list()
                for f in flows:
                    klist.append(f['id'])
                klist.sort()
                flow_id = str(int(klist[-1]) + 1)
            else:
                flow_id = "10"

        self.logger.debug("Create Flow. " +
                          "host_ip: " + host_ip + " bridge_id: " + bridge_id + " table_id: " + table_id +
                          "flow_id: " + flow_id + " inport: " + inport + " outport: " + outport)

        # Make json variable
        flow_dict = self._make_flow_dict(table_id, flow_id, inport, outport)
        flow_str = json.dumps(flow_dict)
        self.logger.debug("HTTP Body: " + flow_str)

        url = self._default_url + "/restconf/config/opendaylight-inventory:nodes/node/"+bridge_id+"/table/"+table_id+"/flow/"+flow_id

        self.logger.debug("HTTP URL: " + url)
        resp = self.put(url, flow_str)
        self.logger.debug("Flow Creation Response: " + str(resp))

        url = self._default_url + "/restconf/operational/opendaylight-inventory:nodes/node/"+bridge_id+"/table/"+table_id+"/flow/"+flow_id
        for i in range(1, 6):
            resp, content = self.get(url)
            self.logger.debug("Flow Creation Response: " + str(resp))
            if resp.status in ["200", "201"]:
                return True
            time.sleep(0.5)
        return False

    def delete_flow(self, host_ip, bridge, table_id, inport, outport):
        bridge_id = self._get_bridge_id(host_ip, bridge)
        flow_id = self._get_flow_id(bridge_id, table_id, inport, outport)

        if bridge_id and flow_id:
            url = self._default_url + \
                  '/restconf/config/opendaylight-inventory:nodes/node/' + bridge_id + \
                  '/table/' + table_id + \
                  '/flow/' + flow_id
            self.delete(url)
            self.logger.debug("Flow rule is deleted."
                              + "host_ip: " + host_ip + " bridge: " + bridge + " table_id: " + table_id +
                              " in-port: " + inport + " out-port: " + outport)
            return True

        else:
            self.logger.debug("Bridge ID and/or Flow ID not exists. Fail to delete the flow. "
                              + "host_ip: " + host_ip + " bridge: " + bridge + " table_id: " + table_id +
                              " in-port: " + inport + " out-port: " + outport)
            return False

    def _make_flow_dict(self, table_id, flow_id, inport, outports):
        flow_name = "t"+table_id+"f"+flow_id+"_"+str(inport)+"to"+str(outports)
        flow = dict()

        ## Flow Default Value
        flow["hard-timeout"] = "0"
        flow["idle-timeout"] = "0"
        flow["priority"] = "200"
        flow["table_id"] = table_id
        flow["id"] = flow_id
        flow["flow-name"] = flow_name

        ## Flow Match Values
        flow["match"] = self._make_flow_match(inport)

        ## Flow Instruction Values
        flow["instructions"] = self._make_flow_inst(outports)

        return {"flow": flow}

    def _make_flow_match(self, inport):
        match = dict()

        """
        ## Ethernet Match
        match["ethernet-match"] = dict()
        match["ethernet-match"]["ethernet-type"] = {"type": "2048"}
        match["ethernet-match"]["ethernet-source"] = {"address": "2048"}
        match["ethernet-match"]["ethernet-destination"] = {"address": "2048"}

        ## IPv4 Match
        match["ipv4-source"] = None
        match["ipv4-destination"] = None
        match["ip-match"] = dict()
        match["ip-match"]["ip-protocol"] = "6"

        ## Tunnel ID Match
        match["tunnel"] = {"tunnel-id": "100"}
        """
        ## Input Port
        match["in-port"] = inport

        return match

    def _make_flow_inst(self, outports):

        cnt = 0
        action_list = list()
        for pt in outports:
            action = dict()
            action["order"] = str(cnt)
            action["output-action"] = dict()
            action["output-action"]["output-node-connector"] = pt
            action["output-action"]["max-length"] = "60"
            action_list.append(action)
            cnt += 1

        inst = dict()
        inst["instruction"] = dict()
        inst["instruction"]["order"] = "0"
        inst["instruction"]["apply-actions"] = {"action": action_list}

        return inst

    def _get_flow_id(self, node_id, table_id, inport, outport):
        u = self._default_url + '/restconf/operational/opendaylight-inventory:nodes/node/' + node_id + '/table/' + table_id
        resp, content = self.get(u)

        try:
            flow_content = json.loads(content)
            flows = flow_content["flow-node-inventory:table"][0]["flow"]
        except KeyError:
            return None

        for flow in flows:
            check = False
            if inport:
                # Make variable for "Flow Match Rule"
                flow_match = flow["match"]
                given_match = dict()
                given_match["in-port"] = inport
                check = self._is_same_match(flow_match, given_match)

            if check and outport:
                # Make a variable for "Flow Instructions"
                flow_inst = flow["instructions"]["instruction"]
                given_inst = dict()
                given_inst["out-port"] = outport
                check = self._is_same_instruction(flow_inst, given_inst)

            if check == True:
                return flow['id']

    def _is_same_match(self, flow_match, given_match):
        inport = given_match["in-port"]
        if "in-port" not in flow_match.keys():
            return False
        # Check other conditions?
        return True if str(inport) == flow_match["in-port"].split(":")[2] else False

    def _is_same_instruction(self, flow_inst, given_inst):
        outport = given_inst["out-port"]
        for i in flow_inst:
            try:
                actions = i["apply-actions"]["action"]
                for a in actions:
                    if a["output-action"]["output-node-connector"] == str(outport):
                        return True
            except KeyError:
                continue
        return False

    def get_port_number(self, host_ip, port):
        p = self._get_node_connector(host_ip, port)
        if p:
            tmp = p['id'].split(":")
            return tmp[2]

    def _get_bridge_id (self, host_ip, bridge):
        b = self._get_node_connector(host_ip, bridge)
        if b:
            return b['id'].rstrip(":LOCAL")

    def _get_node_connector(self, host_ip, connector):
        node_list = self._get_nodes(host_ip)
        for n in node_list:
            con_list = n[u"node-connector"]
            for c in con_list:
                if connector == c[u"flow-node-inventory:name"]:
                    return c

    def _get_nodes(self, host_ip):
        u = self._default_url + '/restconf/operational/opendaylight-inventory:nodes/'
        resp, content = self.get(u)
        self.logger.debug("Get Nodes Content: " + content)
        nodes = json.loads(content)
        node_list = nodes['nodes']['node']
        res = list()
        for node in node_list:
            if host_ip == node[u"flow-node-inventory:ip-address"]:
                res.append(node)
        return res

    def get(self, url):
        if self._http_agent is None:
            return "Error"
        hdrs={'Content-Type': 'application/json', 'Accept': 'application/json'}
        resp, content = self._http_agent.request(uri=url, method='GET', headers=hdrs)
        return resp, content

    def put(self, url, body):
        if self._http_agent is None:
            return "Error"
        hdrs={'Content-Type': 'application/json', 'Accept': 'application/json'}
        resp, content = self._http_agent.request(uri=url, method='PUT',
                                                 headers=hdrs,
                                                 body=body)
        return resp, content

    def delete(self, url):
        if self._http_agent is None:
            return "Error"
        hdrs={'Content-Type': 'application/json', 'Accept': 'application/json'}
        resp, content = self._http_agent.request(uri=url, method='DELETE', headers=hdrs)
        return resp, content

#     def put_test(self):
#         h = httplib2.Http(".cache")
#         h.add_credentials("admin", "admin")
#         u = 'http://10.246.67.127:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:59420899366725/table/1/flow/10'
#
#         btemp = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
# <flow xmlns="urn:opendaylight:flow:inventory">
#    <strict>false</strict>
#    <instructions>
#        <instruction>
#            <order>0</order>
#            <apply-actions>
#               <action>
#                  <push-vlan-action>
#                      <ethernet-type>33024</ethernet-type>
#                  </push-vlan-action>
#                  <order>0</order>
#               </action>
#                <action>
#                    <set-field>
#                        <vlan-match>
#                             <vlan-id>
#                                 <vlan-id>79</vlan-id>
#                                 <vlan-id-present>true</vlan-id-present>
#                             </vlan-id>
#                        </vlan-match>
#                    </set-field>
#                    <order>1</order>
#                </action>
#                <action>
#                    <output-action>
#                        <output-node-connector>5</output-node-connector>
#                    </output-action>
#                    <order>2</order>
#                </action>
#            </apply-actions>
#        </instruction>
#    </instructions>
#    <table_id>0</table_id>
#    <id>31</id>
#    <match>
#        <ethernet-match>
#            <ethernet-type>
#                <type>2048</type>
#            </ethernet-type>
#            <ethernet-destination>
#                <address>FF:FF:29:01:19:61</address>
#            </ethernet-destination>
#            <ethernet-source>
#                <address>00:00:00:11:23:AE</address>
#            </ethernet-source>sdn_controller:
#        </ethernet-match>
#      <in-port>1</in-port>
#    </match>
#    <flow-name>vlan_flow</flow-name>
#    <priority>2</priority>
# </flow>
#         """
#
#         root = cElementTree.XML(btemp)
#         xmldict = xmlparser.etree_to_dict(root)
#         print (json.dumps(xmldict))

if __name__ == "__main__":
    odl_id = "admin"
    odl_pw = "admin"
    odl_ip = "10.246.67.127"

    odl_api = ODL_API(odl_id, odl_pw, odl_ip)
    odl_api.delete_flow("10.246.67.241", "br-test2", "1", "2", "4")
