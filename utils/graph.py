# referred to website "http://www.bogotobogo.com/python/python_graph_data_structures.php"
import logging


# Exception Classes
class GraphError(Exception):
    pass


class NoVertexError(GraphError):
    def __init__(self, vertex, msg):
        self.err_vertex = vertex
        super(NoVertexError, self).__init__(msg)


class NoEdgeError(GraphError):
    def __init__(self, from_vtx, to_vtx, msg):
        self.from_vtx = from_vtx
        self.to_vtx = to_vtx
        super(NoEdgeError, self).__init__(msg)


# Vertex Classes
class BoxVertex(object):
    def __init__(self):
        self.bridges = dict()
        self.box_ip = None


class BridgeVertex(object):
    def __init__(self):
        self.ports = dict()
        self.flows = dict()


class PortVertex(object):
    def __init__(self):
        self.neighbor = list()


# Graph Class
class NetworkGraph(object):
    def __init__(self):
        self._logger = logging.getLogger("ovn.utils.NetworkGraph")
        self._box_vertices = dict()
        self._port_connections = dict()

    def add_port(self, box_name, bridge_name, port_name):
        _pt_vtx = self._get_vertex_dict(box_name, bridge_name, port_name)
        try:
            _bridge = self._get_bridge(_pt_vtx)
        except NoVertexError as ext:
            self._logger.warning(ext.message)
            _bridge = self.add_bridge(_pt_vtx)
        _port = PortVertex()
        _bridge.ports[port_name] = _port
        return _port

    def add_bridge(self, box_name, bridge_name):
        _br_vtx = self._get_vertex_dict(box_name, bridge_name)
        try:
            _box = self._get_box(_br_vtx)
        except NoVertexError as ext:
            self._logger.warning(ext.message)
            _box = self._add_box(_br_vtx)
        _bridge = BridgeVertex()
        _box.bridges[bridge_name] = _bridge
        return _bridge

    def _add_box(self, box_name):
        _box_vtx = self._get_vertex_dict(box_name)
        try:
            _box = self._get_box(_box_vtx)
        except NoVertexError as ext:
            self._logger.warning(ext.message)
            _box = BoxVertex()
            self._box_vertices[box_name] = _box
        return _box

    def _get_port(self, pt_ndic):
        _bridge = self._get_bridge(pt_ndic)
        if pt_ndic['port'] in _bridge.ports.key():
            return _bridge.ports[pt_ndic['port']]
        else:
            raise NoVertexError(pt_ndic, "Port Vertex for {} on Bridge {} in Box {} was not created"
                                .format(pt_ndic['port'], pt_ndic['bridge'], pt_ndic['box']))

    def _get_bridge(self, br_ndic):
        _box = self._get_box(br_ndic)
        if br_ndic['bridge'] in _box.bridge_vertices.keys():
            return _box.bridge_vertices[br_ndic['bridge']]
        else:
            raise NoVertexError(br_ndic, "Bridge Vertex for {} in Box {} was not created"
                                .format(br_ndic['bridge'], br_ndic['box']))

    def _get_box(self, box_ndic):
        if box_ndic['box'] in self._box_vertices.keys():
            return self._box_vertices[box_ndic['box']]
        else:
            raise NoVertexError(box_ndic, "Box Vertex for {} was not created"
                                .format(box_ndic['box']))

    def _get_vertex_dict(self, box_name, bridge_name, port_name):
        _vtx = dict()
        _vtx['box'] = box_name
        _vtx['bridge'] = bridge_name
        _vtx['port'] = port_name
        return _vtx

    def remove_port(self, box_name, bridge_name, port_name):
        _pt_ndic = self._get_vertex_dict(box_name, bridge_name, port_name)
        try:
            _bridge_vtx = self._get_bridge(_pt_ndic)
            _port_vtx = _bridge_vtx.ports.pop(port_name)
            for peer_pt_ndic in _port_vtx.neighbor:
                self.del_edge(_pt_ndic, peer_pt_ndic)
        except NoVertexError as e:
            logging.getLogger("NetworkingGraph").warning(e.msg)

    def remove_bridge(self, box_name, bridge_name):
        _br_ndic = self._get_vertex_dict(box_name, bridge_name)
        try:
            _box = self._get_box(_br_ndic)
            _box.bridge_vertices.pop(bridge_name)
        except NoVertexError as e:
            logging.getLogger("NetworkingGraph").warning(e)

    def remove_box(self, box_name):
        _box_ndic = self._get_vertex_dict(box_name)
        try:
            _box = self._get_box(_box_ndic)
            self._box_vertices.pop(_box)
        except NoVertexError as e:
            logging.getLogger("NetworkingGraph").warning(e)

    def add_edge(self, pt_ndic1, pt_ndic2):
        try:
            _port1 = self._get_port(pt_ndic1)
            _port2 = self._get_port(pt_ndic2)
            _port1.neighbor.append(pt_ndic2)
            _port2.neighbor.append(pt_ndic1)
        except NoVertexError as ext:
            self._logger.error(ext.message)

    def del_edge(self, pt_ndic1, pt_ndic2):
        try:
            _port1 = self._get_port(pt_ndic1)
            _port2 = self._get_port(pt_ndic2)
            _port1.neighbor.remove(pt_ndic2)
            _port2.neighbor.remove(pt_ndic1)
        except NoVertexError as ext:
            self._logger.error(ext.message)

if __name__ == '__main__':
    ng = NetworkGraph()
    ng.add_bridge('ovs-control1', "test-br1")
    ng.add_port('ovs-control1', 'test-br2', 'test-pt1')
    ng.add_port('ovs-control1', 'test-br2', 'test-pt2')
    ng.add_bridge('ovs-client1', "test-br3")
    ng.add_bridge('ovs-client1', "test-br4")
    ng.add_port('ovs-client1', 'test-br5', 'test-pt3')
    ng.add_edge({'box': 'ovs-control1', 'bridge': 'test-br1', 'port': 'test-pt1'},
                {'box': 'ovs-control1', 'bridge': 'test-br2', 'port': 'test-pt2'})
    # g = Graph()
    #
    # g.add_vertex('a')
    # g.add_vertex('b')
    # g.add_vertex('c')
    # g.add_vertex('d')
    # g.add_vertex('e')
    # g.add_vertex('f')
    #
    # g.add_edge('a', 'b', 7)
    # g.add_edge('a', 'c', 9)
    # g.add_edge('a', 'f', 14)
    # g.add_edge('b', 'c', 10)
    # g.add_edge('b', 'd', 15)
    # g.add_edge('c', 'd', 11)
    # g.add_edge('c', 'f', 2)
    # g.add_edge('d', 'e', 6)
    # g.add_edge('e', 'f', 9)
    #
    # for v in g:
    #     for w in v.get_connections():
    #         vid = v.get_id()
    #         wid = w.get_id()
    #         print '( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w))
    #
    # for v in g:
    #     print 'g.vert_dict[%s]=%s' %(v.get_id(), g.vert_dict[v.get_id()])