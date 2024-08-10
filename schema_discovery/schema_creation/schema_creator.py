class SchemaCreator:
    def __init__(self, config, node_types, edge_types):
        self.config = config
        self.node_types = node_types
        self.edge_types = edge_types

    def create_schema(self):
        schema = "CREATE GRAPH TYPE " + self.config.get("graph_type_name") + " " + self.config.get("graph_type_mode") + " { \n"
        for node_type in self.node_types:
            schema = schema + node_type.to_schema("NODE") + "\n"
        schema = schema + "}"
        return schema

    def save_schema(self, filepath):
        schema = self.create_schema()
        with open(filepath, 'w') as file:
            file.write(schema)
