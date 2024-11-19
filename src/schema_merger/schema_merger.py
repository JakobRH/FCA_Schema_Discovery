class SchemaMerger:

    def __init__(self, config):
        self.config = config
        self.type_mapping = {}  # Maps old type names to merged types

    def merge_schemas(self, schema1, schema2):
        merged_schema = {"node_types": [], "edge_types": []}

        # Merge node types
        self.type_mapping = {}
        merged_node_types = self.merge_types(
            schema1["node_types"], schema2["node_types"], type_key="node_types"
        )
        merged_schema["node_types"] = merged_node_types

        # Merge edge types
        merged_edge_types = self.merge_types(
            schema1["edge_types"], schema2["edge_types"], type_key="edge_types"
        )
        merged_schema["edge_types"] = merged_edge_types

        # Update supertype and subtype relationships
        self.update_supertype_subtype_relations(merged_schema["node_types"])

        return merged_schema

    def merge_types(self, types1, types2, type_key):
        merged_types = []
        visited = set()

        # Merge similar types
        for type1 in types1:
            best_match = None
            best_similarity = 0
            for type2 in types2:
                if type2["name"] in visited:
                    continue
                similarity = self.calculate_similarity(type1, type2)
                if similarity > self.similarity_threshold and similarity > best_similarity:
                    best_match = type2
                    best_similarity = similarity

            if best_match:
                merged_type = self.merge_two_types(type1, best_match, type_key)
                merged_types.append(merged_type)
                visited.add(best_match["name"])
                self.type_mapping[type1["name"]] = merged_type["name"]
                self.type_mapping[best_match["name"]] = merged_type["name"]
            else:
                # No match found, add the type as is
                merged_types.append(type1)
                self.type_mapping[type1["name"]] = type1["name"]

        # Add remaining unmatched types from types2
        for type2 in types2:
            if type2["name"] not in visited:
                merged_types.append(type2)
                self.type_mapping[type2["name"]] = type2["name"]

        return merged_types

    def merge_two_types(self, type1, type2, type_key):
        # Merge properties
        all_properties = {**type1["properties"], **type2["properties"]}
        all_optional_properties = {
            **type1.get("optional_properties", {}),
            **type2.get("optional_properties", {}),
        }

        # Merge labels
        all_labels = type1["labels"] | type2["labels"]

        # Merge supertypes and subtypes
        all_supertypes = list(set(type1.get("supertypes", []) + type2.get("supertypes", [])))
        all_subtypes = list(set(type1.get("subtypes", []) + type2.get("subtypes", [])))

        # Create merged type
        merged_type = {
            "name": f"Merged{type1['name']}_{type2['name']}",
            "labels": all_labels,
            "properties": all_properties,
            "optional_properties": all_optional_properties,
            "supertypes": all_supertypes,
            "subtypes": all_subtypes,
        }
        return merged_type

    def update_supertype_subtype_relations(self, node_types):
        # Update relationships using the type mapping
        for node_type in node_types:
            node_type["supertypes"] = [
                self.type_mapping.get(supertype, supertype) for supertype in node_type.get("supertypes", [])
            ]
            node_type["subtypes"] = [
                self.type_mapping.get(subtype, subtype) for subtype in node_type.get("subtypes", [])
            ]

        # Validate supertypes and resolve conflicts
        for node_type in node_types:
            for supertype in node_type.get("supertypes", []):
                supertype_obj = next((t for t in node_types if t["name"] == supertype), None)
                if supertype_obj:
                    self.ensure_subtype_compliance(node_type, supertype_obj)

    def ensure_subtype_compliance(self, subtype, supertype):
        # Check that subtype properties and labels are consistent with supertype
        super_properties = set(supertype["properties"].keys())
        sub_properties = set(subtype["properties"].keys())
        if not super_properties.issubset(sub_properties):
            raise ValueError(
                f"Subtype {subtype['name']} is missing mandatory properties of supertype {supertype['name']}"
            )

        super_labels = supertype["labels"]
        sub_labels = subtype["labels"]
        if not super_labels.issubset(sub_labels):
            raise ValueError(
                f"Subtype {subtype['name']} is missing mandatory labels of supertype {supertype['name']}"
            )

    def calculate_similarity(self, type1, type2):
        # Calculate similarity between two types
        label_similarity = self.jaccard_similarity(type1["labels"], type2["labels"])
        property_similarity = self.jaccard_similarity(
            set(type1["properties"].keys()), set(type2["properties"].keys())
        )
        return 0.5 * label_similarity + 0.5 * property_similarity

    def jaccard_similarity(self, set1, set2):
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0
