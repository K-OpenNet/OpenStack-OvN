from parsehelper import ParseHelper as Parser
import interfaces.ovsdb_interface_bash as iface
import threading

"""
    Instances of this class will be created for each target hosts
    The instance manages all bridge related aspects of a target host
"""


class BridgeManager:
    def __init__(self):
        pass

    def create_port(self, tgt_box_ip, tgt_ovsdb_pt, brname, pt):
        ptname = pt["name"]
        pttype = pt["type"]
        if "options" in pt:
            ptopt = pt["options"]
        else:
            ptopt = None

        optstr = ""
        iface.ovs_vsctl_add_port(tgt_box_ip, tgt_ovsdb_pt, brname, ptname)

        optstr = optstr + "type=" + pttype
        if ptopt:
            if "remote_ip" in ptopt and pttype == "vxlan" or pttype == "gre":
                optstr = optstr + " options:df_default=true options:in_key=flow optios:out_key=flow options:local_ip=" + self.tgtipaddr + " options:remote_ip=" + \
                         ptopt["remote_ip"]
            else:
                for i in ptopt.keys():
                    optstr = optstr + " options:" + i + "=" + ptopt[i]

        iface.ovs_vsctl_set_interface(tgt_box_ip, tgt_ovsdb_pt, ptname, optstr)
        return

    def manage_ports(self, tgt_box_ip, tgt_ovsdb_pt, brname, ptcfg, exptcfg=None):
        if not exptcfg:  ## if there is no ports in the box
            for pt in ptcfg:
                self.create_port(tgt_box_ip, tgt_ovsdb_pt, brname, pt)
        else:
            for pt in ptcfg:
                ptname = pt["name"]
                pttype = pt["type"]
                expt = None

                for tmp in exptcfg:
                    if tmp["Port"] != ptname:
                        continue
                    expt = tmp
                    break

                if expt:
                    ## if same port already exist
                    optstr = ""
                    if "type" not in expt or expt["type"] != pttype:
                        optstr = optstr + " type=" + expt["type"]

                    if "options" in pt:
                        if "options" not in expt:
                            for i in pt["options"].keys():
                                optstr = optstr + " options:" + i + "=" + pt["options"][i]
                        else:
                            for i in pt["options"].keys():
                                if i not in expt["options"] or expt["options"][i] != pt["options"][i]:
                                    optstr = optstr + " options:" + i + "=" + pt["options"][i]
                    iface.ovs_vsctl_set_interface(tgt_box_ip, tgt_ovsdb_pt, ptname, optstr)

                else:
                    self.create_port(tgt_box_ip, tgt_ovsdb_pt, brname, pt)
        return

    def manage_bridge(self, tgt_box_ip, tgt_ovsdb_pt, tgt_br_dict, ex_br_dicts):

        ### Parse each components from the bridge template
        if "name" not in tgt_br_dict:
            print "Bridge name have to be defined in templates"
            return
        br_name = tgt_br_dict["name"]

        if "controller" in tgt_br_dict:
            br_ctrl = tgt_br_dict["controller"]
        else:
            br_ctrl = None

        if "dpid" in tgt_br_dict:
            br_dpid = tgt_br_dict["dpid"]
        else:
            br_dpid = None

        if "ports" in tgt_br_dict:
            br_ports = tgt_br_dict["ports"]
        else:
            br_ports = []

        ### Compare template information to current OVSDB configuration

        if br_name in ex_br_dicts:
            ### It means this bridge was already created before.
            ### So comparing processes are needed
            print "Bridge " + br_name + " is already exists"
            ex_br_dict = ex_br_dicts[br_name]
            if "Controller" in ex_br_dict and br_ctrl:
                ex_br_ctrl = ex_br_dict["Controller"]
                if ex_br_ctrl != br_ctrl:
                    iface.ovs_vsctl_del_controller(tgt_box_ip, tgt_ovsdb_pt, br_name)
                    if br_ctrl: iface.ovs_vsctl_set_controller(tgt_box_ip, tgt_ovsdb_pt, br_name, br_ctrl)

            if "Port" in ex_br_dict and br_ports:
                ex_br_ports_list = ex_br_dict["Port"]
                self.manage_ports(tgt_box_ip, tgt_ovsdb_pt, br_name, br_ports, ex_br_ports_list)
        else:
            ### The Bridge is not exist.
            ### All things written in the template should be created without any comparing process
            print "Bridge " + br_name + " is not exist. it will be created"
            iface.ovs_vsctl_add_br(tgt_box_ip, tgt_ovsdb_pt, br_name)

            if br_ctrl: iface.ovs_vsctl_set_controller(tgt_box_ip, tgt_ovsdb_pt, br_name, br_ctrl)
            if br_dpid: iface.ovs_vsctl_set_dpid(tgt_box_ip, tgt_ovsdb_pt, br_name, br_dpid)
            if br_ports:
                self.manage_ports(tgt_box_ip, tgt_ovsdb_pt, br_name, br_ports)

        return

    def manage_bridges(self, tgt_box_name):

        filepath = "./templates/" + tgt_box_name + ".json"
        tgt_tmpl_json = Parser.json_load_file(filepath)
        tgt_box_dicts = Parser.json_parse_by_key(tgt_tmpl_json, "box")
        tgt_br_list = Parser.json_parse_by_key(tgt_tmpl_json, "bridges")

        tgt_box_ip = tgt_box_dicts["ipaddr"]
        tgt_ovsdb_pt = tgt_box_dicts["ovsdb_port"]

        ex_all_br_ovsdb_list = Parser.divide_str_to_list_by_keyword(iface.ovs_vsctl_show(tgt_box_ip, tgt_ovsdb_pt),
                                                                    "Bridge")

        # Remove Unrequired field in the "ovs-vsctl show" result
        # (e.g ovs_version: "2.0.2")
        unreq_key = ["ovs_version"]

        for i in ex_all_br_ovsdb_list:
            for j in i:
                if j.split()[0] in unreq_key:
                    idx = i.index(j)
                    del i[idx]

        ex_all_br_dicts = Parser.convert_ovsshow_to_json_dicts(ex_all_br_ovsdb_list)


        # Manage each bridge in the bridge list defined in box's template
        for tgt_br_dict in tgt_br_list:
            print "Bridge !!"
            print tgt_br_dict
            self.manage_bridge(tgt_box_ip, tgt_ovsdb_pt, tgt_br_dict, ex_all_br_dicts)

        return

    def do_work(self, tgtlist):
        # Make a thread for each target host
        # It makes the bridge manager treats multiple hosts at the same time.
        threads = []
        for tgtbox in tgtlist:
            th = threading.Thread(target=self.manage_bridges, args=tgtbox)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()


if __name__ == "__main__":
    tgtlist = ["ovn_test-1"]
    brmanager = BridgeManager()
    brmanager.do_work(tgtlist)
