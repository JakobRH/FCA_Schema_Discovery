class SchemaCreator:
    def __init__(self, node_types, edge_types):
        self.node_types = node_types
        self.edge_types = edge_types

    def create_schema(self):
        schema = {
            "node_types": [node_type.to_schema_part() for node_type in self.node_types],
            "edge_types": [edge_type.to_schema_part() for edge_type in self.edge_types]
        }
        return schema

    def save_schema(self, filepath):
        schema = self.create_schema()
        with open(filepath, 'w') as file:
            json.dump(schema, file, indent=4)
