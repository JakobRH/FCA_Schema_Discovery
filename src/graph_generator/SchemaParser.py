import re

class SchemaParser:
    def __init__(self, schema_text):
        self.schema_text = schema_text
        self.node_types = {}
        self.edge_types = {}

    def parse_schema(self):
        # Clean the schema text
        schema_body = self.schema_text.strip()

        # Extract the graph type name
        graph_type_match = re.match(r"CREATE GRAPH TYPE\s+(\w+)\s*{", schema_body)
        if not graph_type_match:
            raise ValueError("Invalid schema format. Missing 'CREATE GRAPH TYPE'.")
        graph_type_name = graph_type_match.group(1)

        # Extract the definitions inside the curly braces
        type_definitions = re.search(r"{(.*)}", schema_body, re.DOTALL).group(1).strip()

        # Split definitions by commas while ignoring commas within braces or brackets
        type_definitions_list = re.split(r',\s*(?![^{}]*\})', type_definitions)

        for definition in type_definitions_list:
            definition = definition.strip()

            if self._is_node_type_definition(definition):  # Node type
                self._parse_node_type(definition)
            elif self._is_edge_type_definition(definition):  # Edge type
                self._parse_edge_type(definition)
            else:
                raise ValueError(f"Invalid type definition: {definition}")

    def _is_node_type_definition(self, definition):
        return definition.startswith("(") and not "-[" in definition

    def _is_edge_type_definition(self, definition):
        return "-[" in definition and "]->" in definition

    def _parse_node_type(self, definition):
        # Node type regex
        node_pattern = r'\(\s*([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_&?\s]*)\s*(\{.*?\})?\s*\)'
        match = re.match(node_pattern, definition)
        if not match:
            raise ValueError(f"Invalid node type definition: {definition}")

        node_type_name, label_supertype_part, properties_str = match.groups()

        supertypes, labels = self._parse_supertypes_and_labels(label_supertype_part)
        properties = self._parse_properties(properties_str)

        self.node_types[node_type_name] = {
            'supertypes': supertypes,
            'labels': labels['mandatory'],
            'optional_labels': labels['optional'],
            'properties': properties['mandatory'],
            'optional_properties': properties['optional']
        }

    def _parse_edge_type(self, definition):
        # Edge type regex
        edge_pattern = r'\(\s*:([A-Za-z0-9_|\s]*)\)\s*-\[(\w+)\s*:\s*([A-Za-z0-9_&?\s]*)\s*(\{.*?\})?\s*\]->\(\s*:([A-Za-z0-9_|\s]*)\)\s*'
        match = re.match(edge_pattern, definition)
        if not match:
            raise ValueError(f"Invalid edge type definition: {definition}")

        start_node_types, edge_type_name, label_supertype_part, properties_str, end_node_types = match.groups()

        start_node_types = start_node_types.split('|') if start_node_types else []
        end_node_types = end_node_types.split('|') if end_node_types else []

        supertypes, labels = self._parse_supertypes_and_labels(label_supertype_part)
        properties = self._parse_properties(properties_str)

        self.edge_types[edge_type_name] = {
            'start_node_types': [s.strip() for s in start_node_types],
            'end_node_types': [e.strip() for e in end_node_types],
            'supertypes': supertypes,
            'labels': labels['mandatory'],
            'optional_labels': labels['optional'],
            'properties': properties['mandatory'],
            'optional_properties': properties['optional']
        }

    def _parse_supertypes_and_labels(self, part):
        supertypes = []
        labels = {'mandatory': [], 'optional': []}

        if '&' in part:
            components = [comp.strip() for comp in part.split('&')]
            for component in components:
                if '?' in component:
                    labels['optional'].append(component.strip('?'))
                else:
                    if component in self.node_types or component in self.edge_types:
                        supertypes.append(component)
                    else:
                        labels['mandatory'].append(component)
        else:
            if '?' in part:
                labels['optional'].append(part.strip('?'))
            else:
                if part in self.node_types or part in self.edge_types:
                    supertypes.append(part)
                else:
                    labels['mandatory'].append(part)

        return supertypes, labels

    def _parse_properties(self, properties_str):
        properties = {'mandatory': {}, 'optional': {}}
        if properties_str:
            properties_str = properties_str.strip('{} ')
            for prop in properties_str.split(','):
                prop = prop.strip()
                if prop.startswith('OPTIONAL'):
                    _, key, prop_type = prop.split()
                    properties['optional'][key] = prop_type
                else:
                    key, prop_type = prop.split()
                    properties['mandatory'][key] = prop_type
        return properties

# Example usage
schema_text = """
CREATE GRAPH TYPE FraudGraphType {
  (PersonType: Person {name STRING, OPTIONAL birthday DATE}),
  (CustomerType: PersonType & Customer & Gender? {c_id INT32}),
  (AccountType: Account {acct_id INT32}),
  (:PersonType|CustomerType)-[OwnsAccountType: owns & posses {since DATE, OPTIONAL amount DOUBLE}]->(:AccountType)
}
"""

parser = SchemaParser(schema_text)
parser.parse_schema()

print("Node Types:")
for node_type_name, node_type_info in parser.node_types.items():
    print(f"{node_type_name}: {node_type_info}")

print("\nEdge Types:")
for edge_type_name, edge_type_info in parser.edge_types.items():
    print(f"{edge_type_name}: {edge_type_info}")