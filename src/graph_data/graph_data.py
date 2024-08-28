from collections import defaultdict, Counter

from src.schema_inference.base_type_extractor import infer_data_type


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
        self.nodes = {}
        self.edges = {}
        self.node_property_data_types = {}
        self.edge_property_data_types = {}

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, edge):
        self.edges[edge.id] = edge

    def get_node_by_id(self, node_id):
        return self.nodes.get(node_id, None)

    def get_edge_by_id(self, edge_id):
        return self.edges.get(edge_id, None)

    def infer_property_data_types(self):
        node_property_data_type_dict = defaultdict(list)
        edge_property_data_type_dict = defaultdict(list)

        for node in self.nodes.values():
            for prop, val in node.properties.items():
                node_property_data_type_dict[prop].append(infer_data_type(val))

        for edge in self.edges.values():
            for prop, val in edge.properties.items():
                edge_property_data_type_dict[prop].append(infer_data_type(val))

        self.node_property_data_types = {
            prop: Counter(types).most_common(1)[0][0]
            for prop, types in node_property_data_type_dict.items()
        }
        self.edge_property_data_types = {
            prop: Counter(types).most_common(1)[0][0]
            for prop, types in edge_property_data_type_dict.items()
        }
