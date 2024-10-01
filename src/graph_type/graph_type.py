class GraphType:
    def __init__(self, config):
        self.config = config
        self.node_types = []
        self.edge_types = []

    def create_schema(self):
        schema = "CREATE GRAPH TYPE " + self.config.get("graph_type_name") + " " + self.config.get("graph_type_mode") + " { \n"

        for i, node_type in enumerate(self.node_types):
            schema += node_type.to_schema()
            if i < len(self.node_types) - 1 or len(
                    self.edge_types) > 0:
                schema += ",\n"
            else:
                schema += "\n"

        for i, edge_type in enumerate(self.edge_types):
            schema += edge_type.to_schema()
            if i < len(self.edge_types) - 1:
                schema += ",\n"
            else:
                schema += "\n"
        schema = schema + "}"

        schema_out_file = self.config.get("out_dir") + "schema.txt"
        with open(schema_out_file, 'w') as file:
            file.write(schema)

        nodes_and_edges = "NODETYPES:\n"
        for node_type in enumerate(self.node_types):
            nodes_and_edges += f"Node Type: {node_type.name}\n"
            nodes_and_edges += ", ".join([str(node) for node in node_type.nodes])
        nodes_and_edges = "EDGETYPES:\n"
        for edge_type in enumerate(self.edge_types):
            nodes_and_edges += f"Node Type: {edge_type.name}\n"
            nodes_and_edges += ", ".join([str(edge) for edge in edge_type.edges])
        nodes_edges_file = self.config.get("out_dir") + "nodes_and_edges.txt"
        with open(nodes_edges_file, 'w') as file:
            file.write(nodes_and_edges)
        return schema
