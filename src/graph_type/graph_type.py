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

        out_file = self.config.get("out_dir") + "schema.txt"
        with open(out_file, 'w') as file:
            file.write(schema)
        return schema
