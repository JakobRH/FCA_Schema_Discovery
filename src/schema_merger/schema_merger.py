from src.graph_type.type import Type


class SchemaMerger:
    """
    Merges two schemas into a new one, which consist of node types and edge types.
    """

    def __init__(self, config):
        self.config = config
        self.type_mapping = {}

    def merge_schemas(self, original_node_types, original_edge_types, new_node_types, new_edge_types):
        """
        Merges two schemas by combining their node types and edge types, ensuring compatibility.

        @param original_node_types: List of NodeTypes of the original schema.
        @param original_edge_types: List of EdgeTypes of the original schema.
        @param new_node_types: List of NodeTypes of the new schema.
        @param new_edge_types: List of EdgeTypes of the new schema.
        @return: A merged schema containing node types and edge types.
        """
        self._propagate_supertype_features(new_node_types, new_edge_types)

        merged_node_types = self._merge_types(original_node_types, new_node_types, "NODE")

        merged_edge_types = self._merge_types(original_edge_types, new_edge_types, "EDGE")

        self.update_relations(merged_node_types)
        self.update_relations(merged_edge_types)

        self.check_and_update_supertype_relations(merged_node_types)
        self.check_and_update_supertype_relations(merged_edge_types)

        node_type_dict = {type_.name: type_ for type_ in merged_node_types}
        for type_ in merged_node_types:
            type_.remove_inherited_features(node_type_dict)

        edge_type_dict = {type_.name: type_ for type_ in merged_edge_types}
        for type_ in merged_edge_types:
            type_.remove_inherited_features(edge_type_dict)

        return merged_node_types, merged_edge_types

    def _propagate_supertype_features(self, node_types, edge_types):
        """
        Propagates supertypes features for all types in the schema.

        @param node_types: List of NodeTypes.
        @param edge_types: List of EdgeTypes.
        """
        type_dict = {type_obj.name: type_obj for type_obj in node_types + edge_types}

        for type_obj in node_types + edge_types:
            supertypes = type_obj.get_all_supertypes(type_dict)
            for supertype_name in supertypes:
                supertype = type_dict.get(supertype_name)
                if supertype:
                    type_obj.labels.update(supertype.labels)
                    type_obj.optional_labels.update(supertype.optional_labels)

                    for key, value in supertype.properties.items():
                        if key not in type_obj.properties:
                            type_obj.properties[key] = value

                    for key, value in supertype.optional_properties.items():
                        if key not in type_obj.optional_properties:
                            type_obj.optional_properties[key] = value
                    if type_obj.entity == "EDGE":
                        type_obj.start_node_types.update(supertype.start_node_types)
                        type_obj.end_node_types.update(supertype.end_node_types)

        type_dict = {type_.name: type_ for type_ in node_types}
        for edge in edge_types:
            for node_name in list(edge.start_node_types):
                subtypes = type_dict.get(node_name).get_all_subtypes(type_dict)
                edge.start_node_types.update(subtypes)
            for node_name in list(edge.end_node_types):
                subtypes = type_dict.get(node_name).get_all_subtypes(type_dict)
                edge.end_node_types.update(subtypes)

    def _merge_types(self, original_types, new_types, type_entity):
        """
        Merges two list of types into one.

        @param original_types: List of NodeTypes.
        @param new_types: List of EdgeTypes.
        @param type_entity: Either "NODE" or "EDGE".
        @return: Returns the merged list.
        """
        merged_types = []

        for o_type in original_types:
            if o_type.is_abstract:
                merged_types.append(o_type)
                self.type_mapping[o_type.name] = o_type.name
                continue
            best_match = None
            best_similarity = 0
            for n_type in new_types:
                if n_type.is_abstract:
                    continue
                similarity = o_type.jaccard_similarity(n_type)
                if similarity > self.config.get("schema_merge_threshold") and similarity > best_similarity:
                    best_match = n_type
                    best_similarity = similarity

            if best_match:
                merged_type = self._merge_two_types(o_type, best_match, type_entity)
                merged_types.append(merged_type)
                new_types.remove(best_match)
                self.type_mapping[o_type.name] = merged_type.name
                self.type_mapping[best_match.name] = merged_type.name
            else:
                merged_types.append(o_type)
                self.type_mapping[o_type.name] = o_type.name

        for n_type in new_types:
            merged_types.append(n_type)
            self.type_mapping[n_type.name] = n_type.name + "_new"
            n_type.name = n_type.name + "_new"

        return merged_types

    def _merge_two_types(self, original_type, new_type, type_entity):
        """
        Merges two types into one.

        @param original_type: Original Type.
        @param new_type: New Type.
        @param type_entity: Either "NODE" or "EDGE".
        @return: Returns the merged type.
        """
        common_labels = original_type.labels & new_type.labels
        o_type_only_labels = original_type.labels - new_type.labels
        n_type_only_labels = new_type.labels - original_type.labels

        optional_labels = set()
        optional_labels.update(original_type.optional_labels)
        optional_labels.update(new_type.optional_labels)
        optional_labels.update(o_type_only_labels)
        optional_labels.update(n_type_only_labels)

        common_properties = original_type.properties.keys() & new_type.properties.keys()
        o_type_only_properties = original_type.properties.keys() - new_type.properties.keys()
        n_type_only_properties = new_type.properties.keys() - original_type.properties.keys()

        properties = {}
        optional_properties = {}
        for key in common_properties:
            properties[key] = original_type.properties[key]
        for key in o_type_only_properties:
            optional_properties[key] = original_type.properties[key]
        for key in n_type_only_properties:
            optional_properties[key] = new_type.properties[key]
        for key in original_type.optional_properties:
            optional_properties[key] = original_type.optional_properties[key]
        for key in new_type.optional_properties:
            optional_properties[key] = new_type.optional_properties[key]

        supertypes = set()
        supertypes.update(original_type.supertypes)
        supertypes.update(new_type.supertypes)

        merged_type = Type(self.config, 0, common_labels, properties, supertypes, [], type_entity, False)
        merged_type.optional_labels = optional_labels
        merged_type.optional_properties = optional_properties
        merged_type.name = original_type.name
        merged_type.open_labels = original_type.open_labels | new_type.open_labels
        merged_type.open_properties = original_type.open_properties | new_type.open_properties

        if type_entity == "EDGE":
            merged_type.start_node_types = set()
            merged_type.start_node_types.update(original_type.start_node_types)
            merged_type.start_node_types.update(new_type.start_node_types)
            merged_type.end_node_types = set()
            merged_type.end_node_types.update(original_type.end_node_types)
            merged_type.end_node_types.update(new_type.end_node_types)

        return merged_type

    def update_relations(self, types_list):
        """
        Updates the relations of the newly merged types.

        @param types_list: List of types to update.
        """
        for type_ in types_list:
            type_.supertypes = [
                self.type_mapping.get(supertype, supertype) for supertype in type_.supertypes
            ]
            if type_.entity == "EDGE":
                type_.start_node_types = set([
                    self.type_mapping.get(start_node_type, start_node_type) for start_node_type in
                    type_.start_node_types
                ])
                type_.end_node_types = set([
                    self.type_mapping.get(end_node_type, end_node_type) for end_node_type in
                    type_.end_node_types
                ])

    def check_and_update_supertype_relations(self, types_list):
        """
        Checks and updates the supertype relations for a list of types.
        Removes a supertype from a types supertypes list if the type does not
        have all the mandatory labels and properties of the supertype.

        @param types_list: A list of Type instances to validate.
        """
        type_dict = {t.name: t for t in types_list}

        for type_ in types_list:
            valid_supertypes = set()
            for supertype_name in type_.supertypes:
                supertype = type_dict[supertype_name]

                has_all_labels = supertype.labels.issubset(type_.labels)
                has_all_optional_labels = supertype.optional_labels.issubset(type_.optional_labels)

                has_all_properties = all(
                    key in type_.properties and type_.properties[key] == value
                    for key, value in supertype.properties.items()
                )
                has_all_optional_properties = all(
                    key in type_.optional_properties and type_.optional_properties[key] == value
                    for key, value in supertype.optional_properties.items()
                )

                if has_all_labels and has_all_properties and has_all_optional_labels and has_all_optional_properties:
                    valid_supertypes.add(supertype_name)

            type_.supertypes = valid_supertypes