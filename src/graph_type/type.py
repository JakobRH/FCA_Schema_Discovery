class Type:
    def __init__(self, config, concept_id, labels, properties, supertypes, subtypes, entity, is_abstract=False):
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
        self.startpoint_types = set()
        self.endpoint_types = set()
        self.name = self._generate_name()

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, edge):
        self.edges.add(edge)

    def add_supertype(self, supertype):
        self.supertypes.add(supertype)

    def add_subtype(self, subtype):
        self.subtypes.add(subtype)

    def to_schema(self):
        if self.entity == 'NODE':
            return self._to_node_schema()
        elif self.entity == 'EDGE':
            return self._to_edge_schema()
        else:
            raise ValueError("Unsupported type kind")

    def _to_node_schema(self):
        labels_spec = f": {self._format_labels()}" if self.labels or self.optional_labels else ""
        properties_spec = f"{self._format_properties()}" if self.properties or self.optional_properties else ""
        abstract = "ABSTRACT " if self.is_abstract else ""
        open_labels = "OPEN " if self.config.get("optional_labels") else ""
        return f"CREATE NODE TYPE {abstract} ({self.name} {labels_spec} {open_labels}{properties_spec});"

    def _to_edge_schema(self):
        labels_spec = f": {self._format_labels()}" if self.labels or self.optional_labels else ""
        properties_spec = f"{self._format_properties()}" if self.properties or self.optional_properties else ""
        middle_type = f"[{self.name} {labels_spec} {properties_spec}]"
        start_type = f"({self._format_endpoints(self.startpoint_types)})"
        end_type = f"({self._format_endpoints(self.endpoint_types)})"
        abstract = "ABSTRACT " if self.is_abstract else ""
        return f"CREATE EDGE TYPE {abstract}{start_type} - {middle_type} -> {end_type};"

    def _format_labels(self):
        supertypes_and_labels = []
        supertypes_and_labels.extend(self.supertypes)
        supertypes_and_labels.extend(self.labels)
        supertypes_and_labels.extend(f"{label}?" for label in self.optional_labels)
        if not supertypes_and_labels:
            return ""
        return " & ".join(supertypes_and_labels)

    def _format_properties(self):
        properties = []
        for key, value in self.properties.items():
            properties.append(f"{key} {value}")
        for key, value in self.optional_properties.items():
            properties.append(f"OPTIONAL {key} {value}")

        include_open = self.config.get("optional_properties")
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
        if not endpoints:
            return ""
        return ":" + " | ".join(endpoints)

    def _generate_name(self):
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

    def remove_inherited_features(self, types):
        supertypes = self._get_all_supertypes({type_.name: type_ for type_ in types})
        for type_ in types:
            print(type_.name, type_.labels, type_.properties, type_.optional_labels, type_.optional_properties)
        print(self.name, self.supertypes)
        type_dict = {type_.name: type_ for type_ in types}
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
                self.startpoint_types.difference_update(supertype.startpoint_types)
                self.endpoint_types.difference_update(supertype.endpoint_types)

    def jaccard_similarity(self, other):
        # Compute Jaccard similarity for labels
        label_intersection = len(self.labels & other.labels)
        label_union = len(self.labels | other.labels)
        label_similarity = label_intersection / label_union if label_union != 0 else 0

        # Compute Jaccard similarity for optional labels
        optional_label_intersection = len(self.optional_labels & other.optional_labels)
        optional_label_union = len(self.optional_labels | other.optional_labels)
        optional_label_similarity = optional_label_intersection / optional_label_union if optional_label_union != 0 else 0

        # Compute Jaccard similarity for properties
        property_intersection = len(self.properties.keys() & other.properties.keys())
        property_union = len(self.properties.keys() | other.properties.keys())
        property_similarity = property_intersection / property_union if property_union != 0 else 0

        # Compute Jaccard similarity for optional properties
        optional_property_intersection = len(self.optional_properties.keys() & other.optional_properties.keys())
        optional_property_union = len(self.optional_properties.keys() | other.optional_properties.keys())
        optional_property_similarity = optional_property_intersection / optional_property_union if optional_property_union != 0 else 0

        # Return the average of the four similarities
        return (label_similarity + optional_label_similarity + property_similarity + optional_property_similarity) / 4

    def merge_with_supertype(self, supertype):
        # 1. Handle labels:
        # - Labels common to both stay as normal labels
        # - Labels unique to subtype or supertype become optional labels in supertype
        common_labels = self.labels & supertype.labels
        subtype_only_labels = self.labels - supertype.labels
        supertype_only_labels = supertype.labels - self.labels

        # Common labels remain as normal
        supertype.labels = common_labels

        # Unique labels from subtype become optional in supertype
        supertype.optional_labels.update(subtype_only_labels)
        supertype.optional_labels.update(supertype_only_labels)

        # 2. Handle properties:
        # - Properties common to both stay as normal properties
        # - Properties unique to subtype or supertype become optional in supertype
        common_properties = self.properties.keys() & supertype.properties.keys()
        subtype_only_properties = self.properties.keys() - supertype.properties.keys()
        supertype_only_properties = supertype.properties.keys() - self.properties.keys()

        # Common properties remain as normal
        supertype.properties = {key: self.properties[key] for key in common_properties}

        # Unique properties from subtype become optional in supertype
        for key in subtype_only_properties:
            supertype.optional_properties[key] = self.properties[key]
        for key in supertype_only_properties:
            supertype.optional_properties[key] = supertype.properties[key]

        # Update the supertype's subtypes to include the subtype's subtypes
        supertype.subtypes.update(self.subtypes)

        # Clear the subtype's subtypes after merging
        self.subtypes.clear()

    def _get_all_supertypes(self, type_dict):
        """Recursively get all transitive supertypes."""
        all_supertypes = set(self.supertypes)
        for supertype in self.supertypes:
            all_supertypes.update(type_dict.get(supertype)._get_all_supertypes(type_dict))
        return all_supertypes
