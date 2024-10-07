import json


class GraphType:
    """
    Represents a graph type schema, containing both node types and edge types.
    The schema can be generated and saved as a text file and the associated nodes/edges
    can be output to a JSON file.
    """
    def __init__(self, config):
        self.config = config
        self.node_types = []
        self.edge_types = []

    def create_schema(self):
        """
        Creates the graph schema, including both node types and edge types.
        The schema is written to a text file, and the nodes and edges are saved as a JSON file.

        :return: The generated schema as a string.
        """
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

        nodes_and_edges = {
            "node_types": [],
            "edge_types": []
        }

        for node_type in self.node_types:
            nodes_and_edges["node_types"].append({
                "name": node_type.name,
                "nodes": [str(node) for node in node_type.nodes]
            })

        for edge_type in self.edge_types:
            nodes_and_edges["edge_types"].append({
                "name": edge_type.name,
                "edges": [str(edge) for edge in edge_type.edges]
            })

        nodes_edges_file = self.config.get("out_dir") + "nodes_and_edges.json"

        with open(nodes_edges_file, 'w') as file:
            json.dump(nodes_and_edges, file, indent=4)
        return schema
