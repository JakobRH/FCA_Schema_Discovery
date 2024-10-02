import json


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

        nodes_and_edges = {
            "node_types": [],
            "edge_types": []
        }

        # Add node types and their nodes
        for node_type in self.node_types:
            nodes_and_edges["node_types"].append({
                "name": node_type.name,
                "nodes": [str(node) for node in node_type.nodes]
            })

        # Add edge types and their edges
        for edge_type in self.edge_types:
            nodes_and_edges["edge_types"].append({
                "name": edge_type.name,
                "edges": [str(edge) for edge in edge_type.edges]
            })

        # Specify the output file path
        nodes_edges_file = self.config.get("out_dir") + "nodes_and_edges.json"

        # Write the dictionary to the JSON file
        with open(nodes_edges_file, 'w') as file:
            json.dump(nodes_and_edges, file, indent=4)
        return schema
