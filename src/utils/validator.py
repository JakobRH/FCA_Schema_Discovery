import json


class Validator:
    """
    Validates a graphs nodes and edges against defined node and edge types from a schema.
    Handles both mandatory and optional labels/properties, and supports open/closed label and property validation.
    """
    def __init__(self, graph_data, node_types, edge_types, config, logger):
        self.graph_data = graph_data
        self.node_types = node_types
        self.edge_types = edge_types
        self.config = config
        self.logger = logger

    def _gather_labels_and_properties(self, type_, types):
        """
        Gathers all mandatory and optional labels and properties from a given node or edge type,
        including all inherited ones from its supertypes.

        :param type_: The specific node or edge type for which we gather the attributes.
        :param types: A list of all types to resolve supertypes.
        :return: A tuple containing four sets the labels and properties.
        """
        mandatory_labels = set()
        optional_labels = set()
        mandatory_properties = set()
        optional_properties = set()

        def gather_type_info(type_obj, types_):
            nonlocal mandatory_labels, optional_labels, mandatory_properties, optional_properties
            mandatory_labels.update(type_obj.labels)
            optional_labels.update(type_obj.optional_labels)
            mandatory_properties.update(type_obj.properties)
            optional_properties.update(type_obj.optional_properties)

            for supertype_name in type_obj.supertypes:
                supertype = next((t for t in types_ if t.name == supertype_name), None)
                if supertype:
                    gather_type_info(supertype, types_)

        gather_type_info(type_, types)
        return mandatory_labels, optional_labels, mandatory_properties, optional_properties

    def _validate_node_against_type(self, node, node_type):
        """
        Validates whether a node conforms to a given node type and its supertypes.

        :param node: The node to be validated.
        :param node_type: The node type against which validation is performed.
        :return: True if the node conforms to the type, False otherwise.
        """
        mandatory_labels, optional_labels, mandatory_properties, optional_properties = self._gather_labels_and_properties(node_type, self.node_types)

        node_labels = set(node.labels)
        missing_labels = mandatory_labels - node_labels
        extra_labels = node_labels - (mandatory_labels | optional_labels)

        if missing_labels:
            return False

        if not node_type.open_labels and extra_labels:
            return False

        node_properties = set(node.properties.keys())
        missing_properties = mandatory_properties - node_properties
        extra_properties = node_properties - (mandatory_properties | optional_properties)

        if missing_properties:
            return False

        if not node_type.open_properties and extra_properties:
            return False

        for prop, value in node.properties.items():
            expected_data_type = self.graph_data.node_property_data_types.get(prop)
            if expected_data_type is None:
                continue

            actual_data_type = self.graph_data.infer_data_type(value)

            if actual_data_type != expected_data_type:
                return False

        return True

    def _validate_edge_against_type(self, edge, edge_type, valid_nodes):
        """
        Validates whether an edge conforms to a given edge type, including its labels, properties,
        and the conformity of its start and end nodes.

        :param edge: The edge to be validated.
        :param edge_type: The edge type against which validation is performed.
        :param valid_nodes: Dictionary of validated nodes to check start and end nodes.
        :return: True if the edge conforms to the type, False otherwise.
        """
        mandatory_labels, optional_labels, mandatory_properties, optional_properties = self._gather_labels_and_properties(edge_type, self.edge_types)

        edge_labels = set(edge.labels)
        missing_labels = mandatory_labels - edge_labels
        extra_labels = edge_labels - (mandatory_labels | optional_labels)

        if missing_labels:
            return False

        if not edge_type.open_labels and extra_labels:
            return False

        edge_properties = set(edge.properties.keys())
        missing_properties = mandatory_properties - edge_properties
        extra_properties = edge_properties - (mandatory_properties | optional_properties)

        if missing_properties:
            return False

        if not edge_type.open_properties and extra_properties:
            return False

        for prop, value in edge.properties.items():
            expected_data_type = self.graph_data.edge_property_data_types.get(prop)
            if expected_data_type is None:
                continue

            actual_data_type = self.graph_data.infer_data_type(value)

            if actual_data_type != expected_data_type:
                return False

        start_node = valid_nodes.get(edge.start_node_id)
        end_node = valid_nodes.get(edge.end_node_id)

        if not self._node_conforms_to_any_type(start_node, edge_type.start_node_types):
            return False

        if not self._node_conforms_to_any_type(end_node, edge_type.end_node_types):
            return False

        return True

    def _node_conforms_to_any_type(self, node, valid_type_names):
        """
        Checks whether a node conforms to any of the provided valid type names, considering supertypes.

        :param node: The node to be checked.
        :param valid_type_names: A list of valid type names the node should conform to.
        :return: True if the node conforms to any of the valid types, False otherwise.
        """
        node_type = next((t for t in self.node_types if node.id in t.nodes), None)
        if not node_type:
            return False

        def type_matches(type_obj, valid_type_names):
            if type_obj.name in valid_type_names:
                return True
            for supertype_name in type_obj.supertypes:
                supertype = next((t for t in self.node_types if t.name == supertype_name), None)
                if supertype and type_matches(supertype, valid_type_names):
                    return True
            return False

        return type_matches(node_type, valid_type_names)

    def validate_graph(self):
        """
        Validates the entire graph by checking all nodes and edges against their respective types.

        :return: True if the entire graph conforms to the schema, False otherwise.
        """
        valid_nodes = {}
        invalid_nodes = []
        invalid_edges = []

        for node_id, node in self.graph_data.nodes.items():
            node_conforms = any(self._validate_node_against_type(node, node_type)
                                for node_type in self.node_types)
            if not node_conforms:
                invalid_nodes.append({"node_id": node_id, "node_labels": node.labels, "node_properties": list(node.properties.keys())})
            valid_nodes[node_id] = node

        for edge_id, edge in self.graph_data.edges.items():
            edge_conforms = any(self._validate_edge_against_type(edge, edge_type, valid_nodes)
                                for edge_type in self.edge_types)
            if not edge_conforms:
                invalid_edges.append({"edge_id": edge_id, "edge_labels": edge.labels, "edge_properties": list(edge.properties.keys()), "edge_start_node": edge.start_node_id, "edge_end_node": edge.end_node_id})


        if invalid_nodes or invalid_edges:
            invalid_elements = {
                "invalid_nodes": invalid_nodes,
                "invalid_edges": invalid_edges
            }

            with open(self.config.get("out_dir") + 'invalid_elements.json', 'w') as file:
                json.dump(invalid_elements, file, indent=4)
            self.logger.error("Graph is not valid under the schema.\nInvalid nodes and edges saved to 'invalid_elements.json'.")
        else:
            self.logger.info("Graph is valid under the schema.")
