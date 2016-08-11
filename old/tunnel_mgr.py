import threading
from parsehelper import ParseHelper as Parser
from interfaces import ovsdb_interface_bash as iface
from util_mdls import ping_checker


class TunnelManager:
    def __init__(self):
        pass

    def prepare_tunnel_manager(self, tgt_list):
        self.tnl_pair_lists = []
        self.scan_tunnels(self, tgt_list)
        return

    def scan_tunnels(self, tgt_list):
        for tgt_box in tgt_list:
            try:
                file_path = "./templates/" + tgt_box + ".json"
                tgt_tmpl_json = Parser.json_load_file(file_path)
                tgt_tnls_json = tgt_tmpl_json["tunnels"]

            except IOError as e:
                print e
                continue

            except ValueError as e:
                print e
                continue

            for tgt_tnl_json in tgt_tnls_json:
                peer_box_name = tgt_tnl_json["peer_box"]

                peer_box_json = {}
                for i in tgt_list:
                    if i == peer_box_name:
                        peer_file_path = "./templates/" + peer_box_name + ".json"
                        try:
                            peer_tmpl_json = Parser.json_load_file(peer_file_path)
                            peer_tnls_json = peer_tmpl_json["tunnels"]
                            break
                        except IOError as e:
                            print e
                            continue
                        except ValueError as e:
                            print e
                            continue

                if peer_tnls_json is None: continue

                peer_tnl_json = {}
                for tmp_tnl_json in peer_tnls_json:
                    try:

                        if tmp_tnl_json["peer_box"] == tgt_tnl_json["name"] and \
                                        tmp_tnl_json["options"]["local_ip"] == tgt_tnl_json["options"]["remote_ip"] and \
                                        tmp_tnl_json["options"]["remote_ip"] == tgt_tnl_json["options"]["local_ip"]:
                            peer_tnl_json = tmp_tnl_json
                            break
                        else:
                            continue

                    except ValueError as e:
                        print e
                        continue
                if peer_tnl_json is None: continue

                tnl_pair_list = []
                for tnl_pair in self.tnl_pair_lists:
                    if (tnl_pair[0]["name"] == tgt_tnl_json["name"] and tnl_pair[1]["name"] == peer_tnl_json["name"]) or \
                            (tnl_pair[1]["name"] == tgt_tnl_json["name"] and tnl_pair[0]["name"] == peer_tnl_json[
                                "name"]):
                        tnl_pair_list = tnl_pair
                        break

                if tnl_pair_list is not None:
                    continue

                tgt_tnl_json["boxname"] = tgt_tmpl_json["box"]["hostname"]
                peer_tnl_json["boxname"] = peer_tmpl_json["box"]["hostname"]
                tnl_pair_list.append(tgt_tnl_json)
                tnl_pair_list.append(peer_tnl_json)
                self.tnl_pair_lists.append(tnl_pair_list)

    def manage_tunnel(self, tgt_tnl_dict, ex_br_dicts):

        print tgt_tnl_dict

        try:
            tnl_br_name = tgt_tnl_dict["bridge"]
            ex_br_dict = ex_br_dicts[tnl_br_name]
        except ValueError as e:
            print e
            return

        if "Ports" in ex_br_dict:
            ex_pt_list_in_br = ex_br_dict["Ports"]
        else:
            ex_pt_list_in_br = []

        ex_pt_dict = {}
        for ex_pt in ex_pt_list_in_br:
            if "Port" in ex_pt:
                if tgt_tnl_dict["name"] == ex_pt["Port"]:
                    ex_pt_dict = ex_pt
                    break
                else:
                    continue

        if ex_pt_dict is not None:
            optstr = ""
            if "type" not in ex_pt_dict["type"] or ex_pt_dict["type"] != tgt_tnl_dict["name"]:
                optstr = optstr + " type=" + ex_pt_dict["type"]
            if "options" in tgt_tnl_dict:
                if "options" in ex_pt_dict:
                    for i in tgt_tnl_dict["options"].keys():
                        optstr = optstr + " options:" + i + "=" + tgt_tnl_dict["options"][i]
                else:
                    for i in tgt_tnl_dict["options"].keys():
                        if i not in ex_pt_dict["options"] or ex_pt_dict["options"][i] != tgt_tnl_dict["options"][i]:
                            optstr = optstr + " options:" + i + "=" + tgt_tnl_dict["options"][i]
                    iface.ovs_vsctl_set_interface(self.tgt_box_ip, self.tgt_box_pt, tgt_tnl_dict["name"])

    def manage_tunnel_pair(self, tnl_pair_list):
        # self.prepare_tunnel_manager(tgtname)

        tnl_end1_dict = tnl_pair_list[0]
        tnl_end2_dict = tnl_pair_list[1]

        try:
            end1_filepath = "./templates/" + tnl_end1_dict["boxname"] + ".json"
            end2_filepath = "./templates/" + tnl_end2_dict["boxname"] + ".json"

            # end1_json = parser.json_load_file(end1_filepath)
            # end2_json = parser.json_load_file(end2_filepath)

            end1_box_dict = (Parser.json_load_file(end1_filepath))["box"]
            end2_box_dict = (Parser.json_load_file(end2_filepath))["box"]

            end1_box_ip = end1_box_dict["ipaddr"]
            end2_box_ip = end2_box_dict["ipaddr"]

            end1_box_pt = end1_box_dict["ovsdb_port"]
            end2_box_pt = end2_box_dict["ovsdb_port"]

            end1_all_br_ovsdb_list = Parser.divide_str_to_list_by_keyword(
                iface.ovs_vsctl_show(end1_box_ip, end1_box_pt), "bridge")
            end2_all_br_ovsdb_list = Parser.divide_str_to_list_by_keyword(
                iface.ovs_vsctl_show(end2_box_ip, end2_box_pt), "bridge")

            end1_all_br_dicts = Parser.convert_ovsshow_to_json_dicts(end1_all_br_ovsdb_list)
            end2_all_br_dicts = Parser.convert_ovsshow_to_json_dicts(end2_all_br_ovsdb_list)

            self.manage_tunnel(tnl_end1_dict, end1_all_br_dicts)
            self.manage_tunnel(tnl_end2_dict, end2_all_br_dicts)

            check1 = PingChecker.is_pingable_tunnel(end1_box_ip, tnl_end1_dict["bridge"],
                                                    tnl_end1_dict["options"]["remote_ip"], end1_box_dict["user"])
            check2 = PingChecker.is_pingable_tunnel(end2_box_ip, tnl_end2_dict["bridge"],
                                                    tnl_end2_dict["options"]["remote_ip"], end2_box_dict["user"])

        except IOError as e:
            print e
            return

        except ValueError as e:
            print e
            return

        return

    def do_work(self, tgt_list):
        self.prepare_tunnel_manager(tgt_list)

        threads = []
        for tnl_pair_list in self.tnl_pair_lists:
            th = threading.Thread(target=self.manage_tunnel_pair, args=tnl_pair_list)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        return


if __name__ == "__main__":
    tgtlist = ["ovn_test-1"]
    manager = TunnelManager()
    manager.do_work(tgtlist)
