class Validator:
    def __init__(self, graph_data, node_types, edge_types, config):
        self.graph_data = graph_data
        self.node_types = node_types
        self.edge_types = edge_types
        self.config = config
        self.open_labels = config.get("open_labels")
        self.open_properties = config.get("open_properties")

    def gather_labels_and_properties(self, type_, types):
        """ Gathers all mandatory and optional labels/properties from the node type and its supertypes. """
        mandatory_labels = set()
        optional_labels = set()
        mandatory_properties = set()
        optional_properties = set()

        # Transitive gathering of labels and properties from the node type and its supertypes
        def gather_type_info(type_obj, types_):
            nonlocal mandatory_labels, optional_labels, mandatory_properties, optional_properties
            mandatory_labels.update(type_obj.labels)
            optional_labels.update(type_obj.optional_labels)
            mandatory_properties.update(type_obj.properties)
            optional_properties.update(type_obj.optional_properties)

            # Gather recursively for supertypes
            for supertype_name in type_obj.supertypes:
                supertype = next((t for t in types_ if t.name == supertype_name), None)
                if supertype:
                    gather_type_info(supertype, types_)

        gather_type_info(type_, types)
        return mandatory_labels, optional_labels, mandatory_properties, optional_properties

    def validate_node_against_type(self, node, node_type):
        """ Validates if a node conforms to a given node type and its supertypes. """
        mandatory_labels, optional_labels, mandatory_properties, optional_properties = self.gather_labels_and_properties(node_type, self.node_types)

        # Check labels
        node_labels = set(node.labels)
        missing_labels = mandatory_labels - node_labels
        extra_labels = node_labels - (mandatory_labels | optional_labels)

        if missing_labels:
            return False  # Node is missing mandatory labels

        if not self.open_labels and extra_labels:
            return False  # Node has extra labels not allowed

        # Check properties
        node_properties = set(node.properties.keys())
        missing_properties = mandatory_properties - node_properties
        extra_properties = node_properties - (mandatory_properties | optional_properties)

        if missing_properties:
            return False  # Node is missing mandatory properties

        if not self.open_properties and extra_properties:
            return False  # Node has extra properties not allowed

        return True  # Node conforms to this type

    def validate_edge_against_type(self, edge, edge_type, valid_nodes):
        """ Validates if an edge conforms to a given edge type, including start/end nodes. """
        mandatory_labels, optional_labels, mandatory_properties, optional_properties = self.gather_labels_and_properties(edge_type, self.edge_types)

        # Check edge labels
        edge_labels = set(edge.labels)
        missing_labels = mandatory_labels - edge_labels
        extra_labels = edge_labels - (mandatory_labels | optional_labels)

        if missing_labels:
            return False  # Edge is missing mandatory labels

        if not self.open_labels and extra_labels:
            return False  # Edge has extra labels not allowed

        # Check edge properties
        edge_properties = set(edge.properties.keys())
        missing_properties = mandatory_properties - edge_properties
        extra_properties = edge_properties - (mandatory_properties | optional_properties)

        if missing_properties:
            return False  # Edge is missing mandatory properties

        if not self.open_properties and extra_properties:
            return False  # Edge has extra properties not allowed

        # Check if the start and end nodes conform to the correct node types
        start_node = valid_nodes.get(edge.start_node_id)
        end_node = valid_nodes.get(edge.end_node_id)

        if not self.node_conforms_to_any_type(start_node, edge_type.startpoint_types):
            return False  # Start node doesn't conform to any valid start node types

        if not self.node_conforms_to_any_type(end_node, edge_type.endpoint_types):
            return False  # End node doesn't conform to any valid end node types

        return True  # Edge conforms to this type

    def node_conforms_to_any_type(self, node, valid_type_names):
        """ Check if a node conforms to any of the types in valid_type_names, or their supertypes. """
        node_type = next((t for t in self.node_types if node.id in t.nodes), None)
        if not node_type:
            return False

        # Check if the node_type or any of its supertypes match valid_type_names
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
        """ Validate the entire graph by checking all nodes and edges. """
        valid_nodes = {}

        # Validate all nodes
        for node_id, node in self.graph_data.nodes.items():
            node_conforms = any(self.validate_node_against_type(node, node_type)
                                for node_type in self.node_types)
            if not node_conforms:
                print(f"Node {node_id} does not conform to any node type.")
                return False
            valid_nodes[node_id] = node

        # Validate all edges
        for edge_id, edge in self.graph_data.edges.items():
            edge_conforms = any(self.validate_edge_against_type(edge, edge_type, valid_nodes)
                                for edge_type in self.edge_types)
            if not edge_conforms:
                print(f"Edge {edge_id} does not conform to any edge type.")
                return False

        print("Graph is valid under the schema.")
        return True
