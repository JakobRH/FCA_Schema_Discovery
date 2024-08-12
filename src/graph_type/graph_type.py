class GraphType:
    def __init__(self, config):
        self.config = config
        self.node_types = []
        self.node_types = []

    def create_schema(self):
        schema = "CREATE GRAPH TYPE " + self.config.get("graph_type_name") + " " + self.config.get("graph_type_mode") + " { \n"
        for node_type in self.node_types:
            schema = schema + node_type.to_schema() + "\n"
        schema = schema + "}"

        out_file = self.config.get("out_dir") + "schema.txt"
        with open(out_file, 'w') as file:
            file.write(schema)
        return schema
