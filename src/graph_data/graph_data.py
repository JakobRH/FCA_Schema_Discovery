from collections import defaultdict, Counter

from neo4j._spatial import Point
from neo4j.time import Date, Time, DateTime, Duration


class GraphElement:
    """
    Represents a general element in a graph (can be a node or an edge).
    Holds an ID, a list of labels, and a dictionary of properties.
    """
    def __init__(self, element_id, labels=None, properties=None):
        self.id = str(element_id)
        self.labels = labels if labels is not None else []
        self.properties = properties if properties is not None else {}

    def add_label(self, label):
        """
        Adds a label to the element if it doesnt already exist.

        :param label: The label to be added to the element.
        """
        if label not in self.labels:
            self.labels.append(label)

    def add_property(self, key, value):
        """
       Adds or updates a property for the element.

       :param key: The property name.
       :param value: The value to be associated with the property.
       """
        self.properties[key] = value


class Node(GraphElement):
    """
    Represents a node in a graph.
    """
    def __init__(self, node_id, labels=None, properties=None):
        super().__init__(node_id, labels, properties)


class Edge(GraphElement):
    """
   Represents an edge in a graph. Inherits from GraphElement and adds start and end node IDs.
   """
    def __init__(self, edge_id, start_node_id, end_node_id, labels=None, properties=None):
        super().__init__(edge_id, labels, properties)
        self.start_node_id = str(start_node_id)
        self.end_node_id = str(end_node_id)


class GraphData:
    """
    Represents the entire graph, storing both nodes and edges.
    Provides methods to add nodes/edges, retrieve them by ID, and infer property data types.
    """
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.node_property_data_types = {}
        self.edge_property_data_types = {}

    def add_node(self, node):
        """
       Adds a node to the graph.

       :param node: The Node object to be added.
       """
        self.nodes[node.id] = node

    def add_edge(self, edge):
        """
       Adds an edge to the graph.

       :param edge: The Edge object to be added.
       """
        self.edges[edge.id] = edge

    def get_node_by_id(self, node_id):
        """
        Retrieves a node by its ID.

        :param node_id: The ID of the node to retrieve.
        :return: The Node object.
        """
        return self.nodes.get(node_id)

    def get_edge_by_id(self, edge_id):
        """
        Retrieves an edge by its ID.

        :param edge_id: The ID of the edge to retrieve.
        :return: The Edge object.
        """
        return self.edges.get(edge_id)

    def infer_property_data_types(self):
        """
        Infers the most common data type for each property across all nodes and edges.
        """
        node_property_data_type_dict = defaultdict(list)
        edge_property_data_type_dict = defaultdict(list)

        for node in self.nodes.values():
            for prop, val in node.properties.items():
                node_property_data_type_dict[prop].append(self.infer_data_type(val))

        for edge in self.edges.values():
            for prop, val in edge.properties.items():
                edge_property_data_type_dict[prop].append(self.infer_data_type(val))

        self.node_property_data_types = {
            prop: Counter(types).most_common(1)[0][0]
            for prop, types in node_property_data_type_dict.items()
        }
        self.edge_property_data_types = {
            prop: Counter(types).most_common(1)[0][0]
            for prop, types in edge_property_data_type_dict.items()
        }

    def get_all_node_labels(self):
        """
       Retrieves all unique labels from nodes in the graph.

       :return: A set of unique labels across all nodes.
       """
        unique_labels = set()
        for node in self.nodes.values():
            unique_labels.update(node.labels)
        return unique_labels

    def get_all_edge_labels(self):
        """
        Retrieves all unique labels from edges in the graph.

        :return: A set of unique labels across all edges.
        """
        unique_labels = set()
        for edge in self.edges.values():
            unique_labels.update(edge.labels)
        return unique_labels

    def get_all_node_properties(self):
        """
       Retrieves all unique property keys from nodes in the graph.

       :return: A set of unique property keys across all nodes.
       """
        unique_properties = set()
        for node in self.nodes.values():
            unique_properties.update(node.properties.keys())
        return unique_properties

    def get_all_edge_properties(self):
        """
        Retrieves all unique property keys from edges in the graph.

        :return: A set of unique property keys across all edges.
        """
        unique_properties = set()
        for edge in self.edges.values():
            unique_properties.update(edge.properties.keys())
        return unique_properties

    def infer_data_type(self, value):
        """
        Infers the data type of a given value based on its Python/Neo4j type.

        @param value: The value whose data type needs to be inferred.
        @return: The inferred data type as a string.
        """
        if isinstance(value, str):
            return "STRING"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "FLOAT"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, list):
            return "LIST"
        elif isinstance(value, dict):
            return "MAP"
        elif isinstance(value, Date):
            return "DATE"
        elif isinstance(value, Time):
            return "TIME"
        elif isinstance(value, DateTime):
            return "DATETIME"
        elif isinstance(value, Duration):
            return "DURATION"
        elif isinstance(value, Point):
            return "POINT"
        else:
            return "UNKNOWN"

    def is_top_concept_necessary(self, approach, entity):
        """
        Checks if there are nodes/edges that have no labels/properties, dependent on the approach and entity.
        If there exist nodes/edges with no properties/labels than the top concept is necessary.

        @param approach: Extraction approach used.
        @param entity: Either NODE or EDGE.
        @return: True if top concept is necessary, False otherwise.
        """
        if entity == "NODE":
            if approach == "label_based":
                for node in self.nodes.values():
                    if len(node.labels) == 0:
                        return True
            if approach == "property_based":
                for node in self.nodes.values():
                    if len(node.properties) == 0:
                        return True
            if approach == "label_property_based":
                for node in self.nodes.values():
                    if len(node.labels) == 0 and len(node.properties) == 0:
                        return True
        if entity == "EDGE":
            if approach == "label_based":
                for edge in self.edges.values():
                    if len(edge.labels) == 0:
                        return True
            if approach == "property_based":
                for edge in self.edges.values():
                    if len(edge.properties) == 0:
                        return True
            if approach == "label_property_based":
                for edge in self.edges.values():
                    if len(edge.labels) == 0 and len(edge.properties) == 0:
                        return True
        return False
