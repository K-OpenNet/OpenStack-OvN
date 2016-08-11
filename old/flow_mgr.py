import threading
from parsehelper import ParseHelper as Parser


class FlowManager:
    def __init__(self):
        pass

    def manage_flow(self, tgt_flow):
        pass

    def manage_flows(self, tgt_box_name):
        filepath = "./templates/" + tgt_box_name + ".json"
        tgt_tmpl_json = Parser.json_load_file(filepath)
        tgt_box_dict = Parser.json_parse_by_key(tgt_tmpl_json, "box")
        tgt_bridge_list = Parser.json_parse_by_key(tgt_tmpl_json, "bridge")
        tgt_flow_list = Parser.json_parse_by_key(tgt_tmpl_json, "flows")

        tgt_box_ip = tgt_box_dict["ipaddr"]
        tgt_ovsdb_pt = tgt_box_dict["ovsdb_port"]

        for tgt_flow_dict in tgt_flow_list:
            tgt_br_name = tgt_flow_dict["bridge"]

            tgt_bridge_dict = None
            for br in tgt_bridge_list:
                if br["name"] == tgt_br_name:
                    tgt_bridge_dict = br
                    break

            if tgt_bridge_dict is None:
                print "Failed: The bridge " + tgt_br_name + " is not exist."
                print "Failed: Therefore the flow " + tgt_flow_dict["name"] + " can't be created"
                continue

            tgt_ctrl = tgt_bridge_dict ["Controller"]

            if self.is_flow_exists(tgt_flow_dict, tgt_ctrl):
                pass
            self.manage_flow(tgt_flow_dict)


        return

    def do_work(self, tgt_list):
        threads = []
        for tgt_box in tgt_list:
            th = threading.Thread(target=self.manage_flows, args=tgt_box)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

if __name__ == "__main__":
    print "Execute Flow Manager"
