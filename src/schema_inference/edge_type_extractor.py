from collections import defaultdict, Counter

from .base_type_extractor import BaseTypeExtractor, change_references, merge_types
from src.graph_type.type import Type

class EdgeTypeExtractor(BaseTypeExtractor):
    def extract_types(self):
        approach = self.config.get("edge_type_extraction")
        if approach == 'label_based':
            return self._extract_label_based_types()
        elif approach == 'property_based':
            return self._extract_property_based_types()
        elif approach == 'label_property_based':
            return self._extract_label_property_based_types()
        else:
            raise ValueError("Unsupported node type extraction approach")

    def _extract_label_based_types(self):
        types = self._initialize_types()

        self._compute_properties(types)

        if self.config.get("optional_labels"):
            types = merge_types(self.config, types)

        self._compute_endpoints(types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _extract_property_based_types(self):
        types = self._initialize_types()

        self._compute_labels(types)

        if self.config.get("optional_properties"):
            types = merge_types(self.config, types)

        self._compute_endpoints(types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _extract_label_property_based_types(self):
        types = self._initialize_types()

        if self.config.get("optional_labels") and self.config.get("optional_properties"):
            types = merge_types(self.config, types)

        self._compute_endpoints(types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _initialize_types(self):
        """Initialize types based on FCA lattice."""
        approach = self.config.get("edge_type_extraction")
        types = []
        num_concepts = len(self.fca_helper.edge_concept_lattice)
        top_concept_id = 0
        bottom_concept_id = num_concepts - 1 if num_concepts != 2 else 0  # special case when only 2 concepts
        remove_top_concept = True if not self.fca_helper.edge_concept_lattice[top_concept_id].intent else False
        remove_bottom_concept = True if not self.fca_helper.edge_concept_lattice[bottom_concept_id].extent else False

        for concept_id, concept in enumerate(self.fca_helper.edge_concept_lattice):
            if concept_id == top_concept_id and remove_top_concept:
                continue
            if concept_id == bottom_concept_id and remove_bottom_concept:
                continue

            labels, properties = self.set_lattice_intent(concept.intent, approach)
            edges = concept.extent

            subtypes, supertypes = self.fca_helper.get_edge_sub_super_concepts(concept_id)
            if remove_top_concept:
                supertypes = (x for x in supertypes if x != top_concept_id)
            if remove_bottom_concept:
                subtypes = (x for x in subtypes if x != bottom_concept_id)

            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties=properties,
                         supertypes=supertypes, subtypes=subtypes, entity="EDGE")
            for edge in edges:
                type_.add_edge(edge)
            types.append(type_)

        change_references(types)
        return types

    def _compute_properties(self, types):
        threshold = self.config.get("property_outlier_threshold")

        for type_instance in types:
            edge_ids = set(type_instance.edges)
            property_counts = defaultdict(lambda: {'count': 0})
            total_nodes = len(edge_ids)

            for edge_id in edge_ids:
                for prop, val in self.graph_data.edges[edge_id].properties.items():
                    property_counts[prop]['count'] += 1

            for prop, data in property_counts.items():
                data_type = self.graph_data.edge_property_data_types[prop]
                if data['count'] == total_nodes:
                    type_instance.properties[prop] = data_type
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = data_type

    def _compute_endpoints(self, edge_types):
        threshold = self.config.get("endpoint_outlier_threshold")
        # Step 1: Create a mapping from node IDs to their types
        node_id_to_types = defaultdict(set)
        for node_type in self.graph_type.node_types:
            for node_id in node_type.nodes:
                node_id_to_types[node_id].add(node_type.name)

        # Step 2: Initialize structures to hold the start and end point types
        edge_type_to_startpoint_types = defaultdict(Counter)
        edge_type_to_endpoint_types = defaultdict(Counter)

        # Step 3: Iterate over each edge type and its corresponding edges
        for edge_type in edge_types:
            for edge_id in edge_type.edges:
                edge = self.graph_data.get_edge_by_id(edge_id)
                start_node_types = node_id_to_types.get(edge.start_node_id)
                end_node_types = node_id_to_types.get(edge.end_node_id)

                if start_node_types:
                    for type_ in start_node_types:
                        edge_type_to_startpoint_types[edge_type.name][type_] += 1
                if end_node_types:
                    for type_ in end_node_types:
                        edge_type_to_endpoint_types[edge_type.name][type_] += 1

        # Step 4: Assign the most frequent node types to the edge types based on the threshold
        for edge_type in edge_types:
            startpoint_candidates = edge_type_to_startpoint_types[edge_type.name]
            endpoint_candidates = edge_type_to_endpoint_types[edge_type.name]

            edge_type.startpoint_types = set(
                [node_type for node_type, count in startpoint_candidates.items() if count >= threshold]
            )

            edge_type.endpoint_types = set(
                [node_type for node_type, count in endpoint_candidates.items() if count >= threshold]
            )

            # Remove subtypes in presence of supertypes
            self._filter_subtypes(edge_type.startpoint_types, self.graph_type.node_types)
            self._filter_subtypes(edge_type.endpoint_types, self.graph_type.node_types)

    def _filter_subtypes(self, point_types, node_types):
        to_remove = set()

        for node_type in point_types:
            # Check if any ancestor of the current node_type exists in point_types
            ancestors = self._get_all_ancestors(node_type, node_types)
            if any(ancestor in point_types for ancestor in ancestors):
                to_remove.add(node_type)

        point_types.difference_update(to_remove)

    def _get_all_ancestors(self, node_type, node_types):
        """ Recursively find all ancestors of a given node type in the node_types list. """
        ancestors = set()
        direct_supertypes = {nt.name for nt in node_types if node_type in nt.subtypes}

        for supertype in direct_supertypes:
            ancestors.add(supertype)
            ancestors.update(self._get_all_ancestors(supertype, node_types))

        return ancestors

    def _compute_labels(self, types):
        threshold = self.config.get("label_outlier_threshold")

        for type_instance in types:
            edge_ids = set(type_instance.edges)
            label_counts = defaultdict(int)
            total_nodes = len(edge_ids)

            for edge_id in edge_ids:
                edge = self.graph_data.get_edge_by_id(edge_id)

                for label in edge.labels:
                    label_counts[label] += 1

            for label, count in label_counts.items():
                if count == total_nodes:
                    type_instance.labels.add(label)
                elif count >= threshold:
                    type_instance.optional_labels.add(label)

    def _compute_property_data_types(self, properties):
        properties_dict = {}
        for prop in properties:
            properties_dict[prop] = self.graph_data.edge_property_data_types[prop]
        return properties_dict

    def set_lattice_intent(self, intent, approach):
        labels = []
        properties = []

        if approach == "label_based":
            labels = intent
            properties = {}
        if approach == "property_based":
            properties = self._compute_property_data_types(intent)
        if approach == "label_property_based":
            all_labels = self.graph_data.get_all_edge_labels()
            for attribute in intent:
                if attribute in all_labels:
                    labels.append(attribute)
                else:
                    properties.append(attribute)
            properties = self._compute_property_data_types(properties)
        return labels, properties

