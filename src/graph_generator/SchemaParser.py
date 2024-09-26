import re

class SchemaParser:
    def __init__(self, schema_text):
        self.schema_text = schema_text
        self.node_types = {}
        self.edge_types = {}

    def parse_schema(self):
        schema_body = self.schema_text.strip()
        graph_type_match = re.match(r"CREATE GRAPH TYPE\s+(\w+)\s*{", schema_body)
        if not graph_type_match:
            raise ValueError("Invalid schema format. Missing 'CREATE GRAPH TYPE'.")
        graph_type_name = graph_type_match.group(1)

        type_definitions = re.search(r"{(.*)}", schema_body, re.DOTALL).group(1).strip()
        type_definitions_list = re.split(r',\s*(?![^{}]*\})', type_definitions)

        for definition in type_definitions_list:
            definition = definition.strip()

            if self._is_node_type_definition(definition):
                self._parse_node_type(definition)
            elif self._is_edge_type_definition(definition):
                self._parse_edge_type(definition)
            else:
                raise ValueError(f"Invalid type definition: {definition}")

        self._resolve_supertypes()

    def _is_node_type_definition(self, definition):
        return definition.startswith("(") and not "-[" in definition

    def _is_edge_type_definition(self, definition):
        return "-[" in definition and "]->" in definition

    def _parse_node_type(self, definition):
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
                component = component.strip()
                if '?' in component:
                    labels['optional'].append(component.strip('?'))
                else:
                    if component in self.node_types or component in self.edge_types:
                        supertypes.append(component)
                    else:
                        labels['mandatory'].append(component)
        else:
            part = part.strip()
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

    def _resolve_supertypes(self):
        # Resolve supertypes for node types
        for node_type_name in self.node_types:
            self._resolve_node_type(node_type_name)

        # Resolve supertypes for edge types
        for edge_type_name in self.edge_types:
            self._resolve_edge_type(edge_type_name)

    def _resolve_node_type(self, node_type_name):
        node_type = self.node_types[node_type_name]
        supertypes = node_type['supertypes']
        inherited_labels = set(node_type['labels'])
        inherited_optional_labels = set(node_type['optional_labels'])
        inherited_properties = dict(node_type['properties'])
        inherited_optional_properties = dict(node_type['optional_properties'])

        for supertype in supertypes:
            if supertype in self.node_types:
                resolved_supertype = self._resolve_node_type(supertype)
                inherited_labels.update(resolved_supertype['labels'])
                inherited_optional_labels.update(resolved_supertype['optional_labels'])
                inherited_properties.update(resolved_supertype['properties'])
                inherited_optional_properties.update(resolved_supertype['optional_properties'])

        node_type['labels'] = list(inherited_labels)
        node_type['optional_labels'] = list(inherited_optional_labels)
        node_type['properties'] = inherited_properties
        node_type['optional_properties'] = inherited_optional_properties

        return {
            'labels': inherited_labels,
            'optional_labels': inherited_optional_labels,
            'properties': inherited_properties,
            'optional_properties': inherited_optional_properties
        }

    def _resolve_edge_type(self, edge_type_name):
        edge_type = self.edge_types[edge_type_name]
        supertypes = edge_type['supertypes']
        inherited_labels = set(edge_type['labels'])
        inherited_optional_labels = set(edge_type['optional_labels'])
        inherited_properties = dict(edge_type['properties'])
        inherited_optional_properties = dict(edge_type['optional_properties'])

        for supertype in supertypes:
            if supertype in self.edge_types:
                resolved_supertype = self._resolve_edge_type(supertype)
                inherited_labels.update(resolved_supertype['labels'])
                inherited_optional_labels.update(resolved_supertype['optional_labels'])
                inherited_properties.update(resolved_supertype['properties'])
                inherited_optional_properties.update(resolved_supertype['optional_properties'])

        edge_type['labels'] = list(inherited_labels)
        edge_type['optional_labels'] = list(inherited_optional_labels)
        edge_type['properties'] = inherited_properties
        edge_type['optional_properties'] = inherited_optional_properties

        return {
            'labels': inherited_labels,
            'optional_labels': inherited_optional_labels,
            'properties': inherited_properties,
            'optional_properties': inherited_optional_properties
        }

