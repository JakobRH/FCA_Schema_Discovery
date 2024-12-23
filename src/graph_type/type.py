class Type:
    """
    Represents a Type instance with the provided configuration, labels, properties, and relationships
    to other types (supertypes, subtypes). It also gathers information about whether the type is abstract or concrete,
    and whether it represents a 'NODE' or 'EDGE'.
    """
    def __init__(self, config, concept_id, labels, properties, supertypes, subtypes, entity, is_abstract=False):
        """
        Initializes a Type instance.

        @param config: A dictionary containing configuration settings for the type.
        @param concept_id: A unique identifier for this type instance.
        @param labels: A list of labels associated with this type.
        @param properties: A dictionary of properties associated with the type.
        @param supertypes: A list of supertypes that this type inherits from.
        @param subtypes: A list of subtypes that inherit from this type.
        @param entity: The type of entity, either 'NODE' or 'EDGE'.
        @param is_abstract: A boolean flag indicating if the type is abstract (default is False).
        """
        self.config = config
        self.concept_id = concept_id
        self.labels = set(labels)
        self.optional_labels = set()
        self.properties = properties
        self.optional_properties = {}
        self.nodes = set()
        self.edges = set()
        self.supertypes = set(supertypes)
        self.subtypes = set(subtypes)
        self.is_abstract = is_abstract
        self.entity = entity
        self.start_node_types = set()
        self.end_node_types = set()
        self.name = self._generate_name()
        self.open_labels = False
        self.open_properties = False

    def add_node(self, node):
        """
        Adds a node to the set of nodes belonging to this type.

        @param node: The node to add to the type.
        """
        self.nodes.add(node)

    def add_edge(self, edge):
        """
        Adds an edge to the set of edges belonging to this type.

        @param edge: The edge to add to the type.
        """
        self.edges.add(edge)

    def add_supertype(self, supertype):
        """
        Adds a supertype to this type's set of supertypes.

        @param supertype: The supertype to add to the type.
        """
        self.supertypes.add(supertype)

    def add_subtype(self, subtype):
        """
        Adds a subtype to this type's set of subtypes.

        @param subtype: The supertype to add to the type.
        """
        self.subtypes.add(subtype)

    def to_schema(self):
        """
        Generates a schema representation of the type based on its entity type.

        @return: A string representing the type schema.
        @raises: ValueError if the entity is not 'NODE' or 'EDGE'.
        """
        if self.entity == 'NODE':
            return self._to_node_schema()
        elif self.entity == 'EDGE':
            return self._to_edge_schema()
        else:
            raise ValueError("Unsupported type kind")

    def _to_node_schema(self):
        """
        Constructs and returns the schema for a node type.
        Combines labels, properties, and other optional characteristics.

        @return: A string representing the node schema, including labels and properties.
        """
        labels_spec = f": {self._format_labels()}" if self.labels or self.optional_labels or self.supertypes else ":"
        properties_spec = f" {self._format_properties()}" if self.properties or self.optional_properties else ""
        abstract = "ABSTRACT " if self.is_abstract else ""
        open_labels = " OPEN" if self.open_labels else ""
        return f"{abstract}({self.name}{labels_spec}{open_labels}{properties_spec})"

    def _to_edge_schema(self):
        """
        Constructs and returns the schema for an edge type.
        Combines labels, properties, and defines start and end points.

        @return: A string representing the edge schema, including start and endpoint types and properties.
        """
        labels_spec = f": {self._format_labels()}" if self.labels or self.optional_labels or self.supertypes else ":"
        properties_spec = f"{self._format_properties()}" if self.properties or self.optional_properties else ""
        open_labels = " OPEN" if self.open_labels else ""
        middle_type = f"[{self.name} {labels_spec}{open_labels} {properties_spec}]"
        start_type = f"({self._format_endpoints(self.start_node_types)})"
        end_type = f"({self._format_endpoints(self.end_node_types)})"
        abstract = "ABSTRACT " if self.is_abstract else ""
        return f"{abstract}{start_type} - {middle_type} -> {end_type}"

    def _format_labels(self):
        """
        Formats the labels and supertypes for schema representation.

        @return: A string of labels and supertypes or an empty string if none are present.
        """
        supertypes_and_labels = []
        supertypes_and_labels.extend(self.supertypes)
        supertypes_and_labels.extend(self.labels)
        supertypes_and_labels.extend(f"{label}?" for label in self.optional_labels)
        if not supertypes_and_labels:
            return ""
        return " & ".join(supertypes_and_labels)

    def _format_properties(self):
        """
        Formats the properties for schema representation.

        @return: A string representing the properties of the type.
        """
        properties = []
        for key, value in self.properties.items():
            properties.append(f"{key} {value}")
        for key, value in self.optional_properties.items():
            properties.append(f"OPTIONAL {key} {value}")

        include_open = self.open_properties
        properties_str = ", ".join(properties)

        if properties_str or include_open:
            if include_open and properties_str:
                properties_str += ", OPEN"
            elif include_open:
                properties_str = "OPEN"
            return f"{{{properties_str}}}"
        else:
            return "{}"

    def _format_endpoints(self, endpoints):
        """
        Formats the endpoints for schema representation.

        @param endpoints: A set of endpoint types.
        @return: A string of endpoint types or an empty string if none exist.
        """
        if not endpoints:
            return ""
        return ":" + "|".join(endpoints)

    def _generate_name(self):
        """
        Generates the name of the type based on its entity and whether it's abstract.

        @return: A string representing the name of the type.
        """
        if self.is_abstract:
            name = "Abstract"
            if self.entity == "NODE":
                name += "NodeType" + "+".join(self.subtypes)
            if self.entity == "EDGE":
                name += "EdgeType" + "+".join(self.subtypes)
            return name
        if self.entity == "NODE":
            return "NodeType" + str(self.concept_id)
        if self.entity == "EDGE":
            return "EdgeType" + str(self.concept_id)
        return ""

    def jaccard_similarity(self, other):
        """
       Computes the Jaccard similarity between this type and another type.

       @param other: The other Type instance to compare against.
       @return: A float representing the average Jaccard similarity over labels, optional labels, properties, and optional properties.
       """
        similarities = []
        total_elements = 0

        label_count = len(self.labels | other.labels)
        if label_count > 0:
            label_intersection = len(self.labels & other.labels)
            label_similarity = label_intersection / label_count
            similarities.append(label_similarity * label_count)
            total_elements += label_count

        optional_label_count = len(self.optional_labels | other.optional_labels)
        if optional_label_count > 0:
            optional_label_intersection = len(self.optional_labels & other.optional_labels)
            optional_label_similarity = optional_label_intersection / optional_label_count
            similarities.append(optional_label_similarity * optional_label_count)
            total_elements += optional_label_count

        property_count = len(self.properties.keys() | other.properties.keys())
        if property_count > 0:
            property_intersection = len(self.properties.keys() & other.properties.keys())
            property_similarity = property_intersection / property_count
            similarities.append(property_similarity * property_count)
            total_elements += property_count

        optional_property_count = len(self.optional_properties.keys() | other.optional_properties.keys())
        if optional_property_count > 0:
            optional_property_intersection = len(self.optional_properties.keys() & other.optional_properties.keys())
            optional_property_similarity = optional_property_intersection / optional_property_count
            similarities.append(optional_property_similarity * optional_property_count)
            total_elements += optional_property_count

        if total_elements == 0:
            return 0

        return sum(similarities) / total_elements

    def merge_into_other_type(self, other_type):
        """
        Merges the current type into another type, adjusting labels, properties, and other features.

        @param other_type: The target Type instance that will absorb the current types features.
        """
        common_labels = self.labels & other_type.labels
        subtype_only_labels = self.labels - other_type.labels
        supertype_only_labels = other_type.labels - self.labels

        other_type.labels = common_labels

        other_type.optional_labels.update(subtype_only_labels)
        other_type.optional_labels.update(supertype_only_labels)
        other_type.optional_labels.update(self.optional_labels)

        common_properties = self.properties.keys() & other_type.properties.keys()
        subtype_only_properties = self.properties.keys() - other_type.properties.keys()
        supertype_only_properties = other_type.properties.keys() - self.properties.keys()

        for key in subtype_only_properties:
            other_type.optional_properties[key] = self.properties[key]
        for key in supertype_only_properties:
            other_type.optional_properties[key] = other_type.properties[key]
        for key in self.optional_properties:
            other_type.optional_properties[key] = self.optional_properties[key]

        other_type.properties = {key: self.properties[key] for key in common_properties}

        other_type.nodes.update(self.nodes)
        other_type.edges.update(self.edges)

        if self.entity == "EDGE":
            other_type.start_node_types.update(self.start_node_types)
            other_type.end_node_types.update(self.end_node_types)

        other_type.subtypes.update(self.subtypes)

        self.subtypes.clear()

    def remove_inherited_features(self, type_dict):
        """
        Removes the features that are already present in supertypes.

        @param type_dict: A dict of types to look up the type instances.
        """
        supertypes = self.get_all_supertypes(type_dict)
        for supertype_name in supertypes:
            supertype = type_dict.get(supertype_name)
            self.labels.difference_update(supertype.labels)
            self.optional_labels.difference_update(supertype.labels)
            self.supertypes.difference_update(supertype.supertypes)
            for key in list(self.properties.keys()):
                if key in supertype.properties:
                    del self.properties[key]
            for key in list(self.optional_properties.keys()):
                if key in supertype.optional_properties:
                    del self.optional_properties[key]
            if self.entity == "EDGE":
                self.start_node_types.difference_update(supertype.start_node_types)
                self.end_node_types.difference_update(supertype.end_node_types)

    def get_all_supertypes(self, type_dict):
        """
        Recursively get all transitive supertypes.

        @param type_dict: A dict of types to look up the type instances.
        """
        all_supertypes = set(self.supertypes)
        for supertype in self.supertypes:
            all_supertypes.update(type_dict.get(supertype).get_all_supertypes(type_dict))
        return all_supertypes

    def get_all_subtypes(self, type_dict):
        """
        Recursively get all transitive subtypes.

        @param type_dict: A dict of types to look up the type instances.
        """
        all_subtypes = set(self.subtypes)
        for subtype in self.subtypes:
            all_subtypes.update(type_dict.get(subtype).get_all_subtypes(type_dict))
        return all_subtypes