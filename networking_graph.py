from utils.graph import Vertex, Graph


class BridgeVertex(Vertex):
    def __init__(self, bridge_name):
        Vertex.__init__(bridge_name)
        self.ports = dict()
        self.flows = dict()
        self.ext_ports = dict()

    def add_port(self, port_name, port_opt):
        if port_name not in self.get_ports():
            self.ports[port_name] = port_opt

    def add_flow(self, flow_name, flow_opt):
        if flow_name not in self.get_flows():
            self.flows[flow_name] = flow_opt

    def add_ext_port(self, ext_port_name, ext_port_opt):
        if ext_port_name not in self.get_ext_ports():
            self.ext_ports[ext_port_name] = ext_port_opt

    def get_ports(self):
        return self.ports.keys()

    def get_flows(self):
        return self.flows.keys()

    def get_ext_ports(self):
        return self.ext_ports.keys()


class BridgeGraph(Graph):
    def __init__(self):
        Graph.__init__()

    def add_vertex(self, node):
        self.num_vertices += 1
        new_vertex = BridgeVertex(node)
        self.vert_dict[node] = new_vertex
        return new_vertex

class BoxVertex(Vertex):
    pass

class BoxGraph(Graph):
    pass