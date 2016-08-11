import json
import sys

sys.path.append("./interfaces")
import ovsdb_interface_bash as ovsdb_if


class ParseHelper:
    def __init__(self):
        pass

    @staticmethod
    def json_load_file(filepath):
        f = open(filepath, 'r')
        json_str = json.loads(f.read())
        f.close
        return json_str

    @staticmethod
    def json_parse_by_key(json_str, key):
        return json_str[key]

    @staticmethod
    def json_parse_by_idx(json_str, idx):
        return json_str[int(idx)]

    @staticmethod
    def text_load_file(filepath):
        f = open(filepath, 'r')
        txt_str = f.read()
        f.close
        return txt_str

    @staticmethod
    def divide_str_to_list_by_keyword(info_str, keyword):
        # This method divides multiple lines into the parts covered by passed keyword
        # In this method, unrequired characters like :, ", ' will be removed

        info_lines = info_str.splitlines()
        info_lines = map(str.strip, info_lines)
        info_lines = [i.replace('"', '').replace(':', '') for i in info_lines]

        parsed_list = []

        list_idx = 0
        start_idx = -1
        end_idx = -1

        for line in info_lines:
            if keyword in line:
                if start_idx == -1:
                    start_idx = list_idx
                else:
                    end_idx = list_idx
                    parsed_list.append(info_lines[start_idx: end_idx])
                    start_idx = list_idx
                    end_idx = -1

            list_idx += 1

        if start_idx != -1:
            end_idx = list_idx
            parsed_list.append(info_lines[start_idx: end_idx])

        return parsed_list

    @staticmethod
    def convert_ovsshow_to_json(brcfg):
        brlist = []  # contain all information in the bridge
        ptlist = []  # contain all ports information
        tmplist = []
        brdict = {}

        for i in brcfg:
            if str.split(i)[0] == "Port":
                if tmplist:  # Already a port is being treated
                    ptlist.append(dict(tmplist))
                    tmplist = []

                ## Port "ptname" => (Port, ptname)
                tmplist.append(tuple(str.split(i)))

            ## Interface, Type, Options information belongs to Port Infromation
            elif str.split(i)[0] == "Interface":
                continue
            elif str.split(i)[0] == "type":
                tmplist.append(tuple(str.split(i)))
            elif str.split(i)[0] == "options":
                k = "options"

                tmp = i.replace('{', '').replace('}', '').replace('=', ' ').split(' ')[1:]

                tmpd = {}
                tmpk = ""
                for j in tmp:
                    if tmpk == "":
                        tmpk = j
                    else:
                        tmpd[tmpk] = j
                        tmpk = ""
                tmpt = (k, tmpd)
                print tmpt
                tmplist.append(tmpt)
            # brdict[k] = tmpd

            else:  ## If the line represents Bridge info
                tmp = str.split(i)
                ikey = tmp[0]
                ival = tmp[1]
                brdict[ikey] = ival
                tmp = []

        if tmplist:
            ptlist.append(dict(tmplist))

        brdict["Ports"] = ptlist
        print "\n\n\n brdict"
        print brdict
        print "\n\n\n"
        return brdict

    @staticmethod
    def convert_ovsshow_to_json_dicts(ovs_list):
        resdict = {}
        for i in ovs_list:
            ### Convert ovs bridge infomation to json format one by one
            tmp = ParseHelper.convert_ovsshow_to_json(i)
            resdict[tmp['Bridge']] = tmp
        ### resdict is a list containing some bridges' dictionary
        return resdict


if __name__ == "__main__":
    filepath = "./templates/ovn_test-1.jso"
    json_str = ParseHelper.json_load_file(filepath)
    site_json = json_str["site"]
    bridge_json = json_str["bridges"]
    if "test" not in json_str: print "hello"
    if "name" in bridge_json[0]:
        print "Exists"
    else:
        print "Not exists"

    exbrstr = ovsdb_if.ovs_vsctl_show("10.0.200.8", "4455")
    exbrlist = ParseHelper.divide_str_to_list_by_keyword(exbrstr, "Bridge")
    exbrdict = ParseHelper.convert_ovsshow_to_json_dicts(exbrlist)

    print exbrdict
