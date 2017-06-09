from utils import util


class OVSDB_API:
    def __init__(self):
        self._util = util.Utils()

    # Read Functions
    def read_ovs_config(self, box_ip):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "show"]
        return self._util.shell_command(command)

    def read_bridge_list(self, box_ip):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "list-br"]
        return self._util.shell_command(command)

    def read_port_list(self, box_ip, bridge):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "list-ports", bridge]
        return self._util.shell_command(command)

    def read_ovsdb_table(self, box_ip, table, name, key):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "get", table, name, key]
        return self._util.shell_command(command)

    def read_bridge_with_port(self, box_ip, port):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "list-to-br", port]
        return self._util.shell_command(command)

    # Create Functions
    def create_bridge(self, box_ip, bridge):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "add-br",
                   bridge]
        return self._util.shell_command(command)

    def create_port(self, box_ip, bridge, port):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "add-port",
                   bridge,
                   port]
        return self._util.shell_command(command)

    # Update Functions
    def update_port_type(self, box_ip, port, type):
            command = ["ovs-vsctl",
                       "--db=tcp:" + box_ip + ":6640",
                       "set", "interface", port,
                       "type=" + type]
            return self._util.shell_command(command)

    def update_port_option(self, box_ip, port, key, value):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "set", "interface", port,
                   "options:" + key + "=" + value]
        return self._util.shell_command(command)

    def update_bridge_controller(self, box_ip, bridge, controller_ip):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "set-controller",
                   bridge,
                   "tcp:" + controller_ip + ":6633"]
        return self._util.shell_command(command)


    def update_manager(self, box_ip, controller_ip):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "set-manager",
                   "tcp:"+controller_ip+":6640"]
        return self._util.shell_command(command)

    # Delete Functions
    def delete_bridge(self, box_ip, bridge):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "del-br",
                   bridge]
        return self._util.shell_command(command)

    def delete_port(self, box_ip, bridge, port):
        command = ["ovs-vsctl",
                   "--db=tcp:" + box_ip + ":6640",
                   "del-port",
                   bridge,
                   port]
        return self._util.shell_command(command)
