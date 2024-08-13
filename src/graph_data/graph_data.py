class GraphElement:
    def __init__(self, element_id, labels=None, properties=None):
        self.id = str(element_id)  # Ensuring ID is stored as a string
        self.labels = labels if labels is not None else []
        self.properties = properties if properties is not None else {}

    def add_label(self, label):
        if label not in self.labels:
            self.labels.append(label)

    def add_property(self, key, value):
        self.properties[key] = value


class Node(GraphElement):
    def __init__(self, node_id, labels=None, properties=None):
        super().__init__(node_id, labels, properties)


class Edge(GraphElement):
    def __init__(self, edge_id, start_node_id, end_node_id, labels=None, properties=None):
        super().__init__(edge_id, labels, properties)
        self.start_node_id = str(start_node_id)
        self.end_node_id = str(end_node_id)


class GraphData:
    def __init__(self):
        self.nodes = []
        self.edges = {}

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges[edge.id] = edge

    def get_node_by_id(self, node_id):
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edge_by_id(self, edge_id):
        return self.edges.get(edge_id, None)