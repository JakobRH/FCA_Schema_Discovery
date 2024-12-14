import re

from src.graph_type.type import Type


class SchemaParser:
    """
    Parses a simplified version of the PG Schema and creates types instances.
    """
    def __init__(self, config, schema_text):
        self.config = config
        self.schema_text = schema_text
        self.node_types = {}
        self.edge_types = {}

    def parse_schema(self):
        """
        Parses the schema text to extract node and edge type definitions.

        :raises ValueError: If the schema format is invalid.
        """
        schema_body = self.schema_text.strip()
        graph_type_match = re.match(r"CREATE GRAPH TYPE\s+(\w+)\s*(LOOSE|STRICT)?\s*{", schema_body)
        if not graph_type_match:
            raise ValueError("Invalid schema format. Wrong Graph Type Definition.")

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
        """
        Checks if a definition corresponds to a node type.

        :param definition: A string representing a schema definition.
        :return: True if the definition is for a node type, False otherwise.
        """
        node_pattern = r'^(ABSTRACT\s+)?\(\s*([A-Za-z0-9_]+)\s*:\s*[A-Za-z0-9_&?\sOPEN]*\s*(\{.*?\})?\s*\)$'
        return re.match(node_pattern, definition) is not None

    def _is_edge_type_definition(self, definition):
        """
       Checks if a definition corresponds to an edge type.

       :param definition: A string representing a schema definition.
       :return: True if the definition is for an edge type, False otherwise.
       """
        edge_pattern = r'^(ABSTRACT\s+)?\(\s*:.*?\)\s*-\[.*?\]\s*->\(\s*:.*?\)\s*$'
        return re.match(edge_pattern, definition) is not None

    def _parse_node_type(self, definition):
        """
        Parses a node type definition and extracts its name, labels, supertypes, and properties.

        :param definition: A string representing a node type definition.
        :raises ValueError: If the node type definition format is invalid.
        """
        is_abstract = definition.startswith("ABSTRACT")
        if is_abstract:
            definition = definition[len("ABSTRACT"):].strip()

        node_pattern = r'\(\s*([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_&?\sOPEN]*)\s*(\{.*?\})?\s*\)'
        match = re.match(node_pattern, definition)
        if not match:
            raise ValueError(f"Invalid node type definition: {definition}")

        node_type_name, label_supertype_part, properties_str = match.groups()
        supertypes, labels = self._parse_supertypes_and_labels(label_supertype_part)
        properties = self._parse_properties(properties_str)

        self.node_types[node_type_name] = {
            'abstract': is_abstract,
            'supertypes': supertypes,
            'labels': labels['mandatory'],
            'optional_labels': labels['optional'],
            'open_labels': labels['open'],
            'properties': properties['mandatory'],
            'optional_properties': properties['optional'],
            'open_properties': properties['open']
        }

    def _parse_edge_type(self, definition):
        """
        Parses an edge type definition and extracts its name, labels, supertypes, start/end node types, and properties.

        :param definition: A string representing an edge type definition.
        :raises ValueError: If the edge type definition format is invalid.
        """
        is_abstract = definition.startswith("ABSTRACT")
        if is_abstract:
            definition = definition[len("ABSTRACT"):].strip()

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
            'abstract': is_abstract,
            'start_node_types': [s.strip() for s in start_node_types],
            'end_node_types': [e.strip() for e in end_node_types],
            'supertypes': supertypes,
            'labels': labels['mandatory'],
            'optional_labels': labels['optional'],
            'open_labels': labels['open'],
            'properties': properties['mandatory'],
            'optional_properties': properties['optional'],
            'open_properties': properties['open']
        }

    def _parse_supertypes_and_labels(self, part):
        """
        Parses a string to extract supertypes, mandatory labels, and optional labels.

        :param part: A string containing the supertypes and labels.
        :return: A tuple (supertypes, labels) where labels is a dictionary with 'mandatory' and 'optional' keys.
        """
        supertypes = []
        labels = {'mandatory': [], 'optional': [], 'open': False}

        if "OPEN" in part:
            labels['open'] = True
            part = part.replace("OPEN", "").strip()

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
        """
        Parses the properties string and separates mandatory and optional properties.

        :param properties_str: A string containing the properties defined in a node or edge.
        :return: A dictionary with 'mandatory' and 'optional' keys, each containing properties.
        """
        properties = {'mandatory': {}, 'optional': {}, 'open': False}

        if "OPEN" in properties_str:
            properties['open'] = True

        if properties_str:
            properties_str = properties_str.replace(", OPEN", "").strip('{} ')
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
        """
        Resolves inherited properties and labels for node and edge types based on their supertypes.
        """
        for node_type_name in self.node_types:
            self._resolve_node_type(node_type_name)

        for edge_type_name in self.edge_types:
            self._resolve_edge_type(edge_type_name)

    def _resolve_node_type(self, node_type_name):
        """
        Recursively resolves the inheritance for a node type, consolidating properties and labels
        from its supertypes. The method ensures that the node type includes all the
        mandatory and optional properties/labels inherited from its supertypes.

        @param node_type_name: Name of the Node Type.
        @:return Dict containing the optional and mandatory labels and properties of the supertypes.
        """
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
        """
        Recursively resolves the inheritance for an edge type, consolidating properties and labels
        from its supertypes. The method ensures that the edge type includes all the
        mandatory and optional properties/labels inherited from its supertypes.

        @param edge_type_name: Name of the Edge Type.
        @:return Dict containing the optional and mandatory labels and properties of the supertypes.
        """
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

    def get_node_types(self):
        """
        Returns the parsed node types as Type objects.

        @:return Parsed node types as Type objects.
        """
        types = []
        for node_type_name, node_type_def in self.node_types.items():
            type_ = Type(self.config, 0, node_type_def.get("labels", []), node_type_def.get("properties", {}), node_type_def.get("supertypes", []),[], "NODE", node_type_def["abstract"])
            type_.optional_labels = set(node_type_def.get("optional_labels", []))
            type_.optional_properties = node_type_def.get("optional_properties", [])
            type_.name = node_type_name
            type_.open_labels = node_type_def["open_labels"]
            type_.open_properties = node_type_def["open_properties"]
            types.append(type_)
        return types

    def get_edge_types(self):
        """
        Returns the parsed node types as Type objects.

        @:return Parsed node types as Type objects.
        """
        types = []
        for edge_type_name, edge_type_def in self.edge_types.items():
            type_ = Type(self.config, 0, edge_type_def.get("labels", []), edge_type_def.get("properties", {}), edge_type_def.get("supertypes", []),[], "NODE", edge_type_def["abstract"])
            type_.optional_labels = set(edge_type_def.get("optional_labels", []))
            type_.optional_properties = edge_type_def.get("optional_properties", [])
            type_.start_node_types = set(edge_type_def.get("start_node_types", []))
            type_.end_node_types = set(edge_type_def.get("end_node_types", []))
            type_.name = edge_type_name
            type_.open_labels = edge_type_def["open_labels"]
            type_.open_properties = edge_type_def["open_properties"]
            types.append(type_)
        return types
