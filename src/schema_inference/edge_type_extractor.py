from collections import defaultdict, Counter

from .base_type_extractor import BaseTypeExtractor, change_references, infer_data_type, merge_types, \
    find_and_create_abstract_types
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
        types = []
        num_concepts = len(self.fca_helper.edge_concept_lattice)
        top_concept_id = 0
        bottom_concept_id = num_concepts - 1

        for concept_id, concept in enumerate(self.fca_helper.edge_concept_lattice):
            if concept_id == 0 or concept_id == num_concepts - 1:
                continue  # Skip first and last concept
            labels = concept.intent
            edges = concept.extent
            subtypes, supertypes = self.fca_helper.get_edge_sub_super_concepts(concept_id)
            filtered_supertypes = (x for x in supertypes if x != top_concept_id)
            filtered_subtypes = (x for x in subtypes if x != bottom_concept_id)
            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties={}, supertypes=filtered_supertypes,
                         subtypes=filtered_subtypes, entity="EDGE")
            for edge in edges:
                type_.add_edge(edge)
            types.append(type_)

        change_references(types)

        self._compute_properties(types)

        if self.config.get("optional_labels"):
            types = merge_types(self.config, types)

        self._compute_endpoints(types)

        for type_ in types:
            type_.remove_inherited_features(types)

        return types

    def _compute_properties(self, types):
        threshold = self.config.get("property_outlier_threshold")
        edge_property_map = {}

        for edge_id, edge in self.graph_data.edges.items():
            edge_property_map[edge_id] = edge.properties

        for type_instance in types:
            edge_ids = set(type_instance.edges)
            property_counts = defaultdict(lambda: {'count': 0, 'types': []})
            total_nodes = len(edge_ids)

            for edge_id in edge_ids:
                if edge_id in edge_property_map:
                    for prop, val in edge_property_map[edge_id].items():
                        property_counts[prop]['count'] += 1
                        property_counts[prop]['types'].append(infer_data_type(val))

            for prop, data in property_counts.items():
                if data['count'] == total_nodes:
                    type_instance.properties[prop] = Counter(data['types']).most_common(1)[0][0]
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = Counter(data['types']).most_common(1)[0][0]

    def _compute_endpoints(self, edge_types):
        threshold = self.config.get("endpoint_outlier_threshold")
        # Step 1: Create a mapping from node IDs to their types
        node_id_to_type = {}
        for node_type in self.graph_type.node_types:
            for node_id in node_type.nodes:
                node_id_to_type[node_id] = node_type.name

        # Step 2: Initialize structures to hold the start and end point types
        edge_type_to_startpoint_types = defaultdict(Counter)
        edge_type_to_endpoint_types = defaultdict(Counter)

        # Step 3: Iterate over each edge type and its corresponding edges
        for edge_type in edge_types:
            for edge_id in edge_type.edges:
                edge = self.graph_data.get_edge_by_id(edge_id)
                start_node_type = node_id_to_type.get(edge.start_node_id)
                end_node_type = node_id_to_type.get(edge.end_node_id)

                if start_node_type:
                    edge_type_to_startpoint_types[edge_type.name][start_node_type] += 1
                if end_node_type:
                    edge_type_to_endpoint_types[edge_type.name][end_node_type] += 1

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

    def _extract_property_based_types(self):
        pass

    def _extract_label_property_based_types(self):
        pass