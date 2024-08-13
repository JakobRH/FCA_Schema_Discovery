from .base_type_extractor import BaseTypeExtractor, infer_data_type, change_references, merge_types
from src.graph_type.type import Type
from collections import defaultdict, Counter


class NodeTypeExtractor(BaseTypeExtractor):
    def extract_types(self):
        approach = self.config.get("node_type_extraction")
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
        num_concepts = len(self.fca_helper.node_concept_lattice)
        top_concept_id = 0
        bottom_concept_id = num_concepts - 1

        for concept_id, concept in enumerate(self.fca_helper.node_concept_lattice):
            if concept_id == 0 or concept_id == num_concepts - 1:
                continue  # Skip first and last concept
            labels = concept.intent
            nodes = concept.extent

            subtypes, supertypes = self.fca_helper.get_node_sub_super_concepts(concept_id)
            filtered_supertypes = (x for x in supertypes if x != top_concept_id)
            filtered_subtypes = (x for x in subtypes if x != bottom_concept_id)

            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties={}, supertypes=filtered_supertypes, subtypes=filtered_subtypes, entity="NODE")
            for node in nodes:
                type_.add_node(node)
            types.append(type_)

        change_references(types)

        self._compute_properties(types)

        if self.config.get("optional_labels"):
            types = merge_types(self.config, types)

        for type_ in types:
            type_.remove_inherited_features(types)

        return types



    def _extract_property_based_types(self):
        types = []
        return types

    def _extract_label_property_based_types(self):
        types = []
        return types

    def _compute_properties(self, types):
        threshold = self.config.get("property_outlier_threshold")
        node_property_map = {}

        for node in self.graph_data.nodes:
            node_id = node.id
            node_property_map[node_id] = node.properties

        for type_instance in types:
            node_ids = set(type_instance.nodes)
            property_counts = defaultdict(lambda: {'count': 0, 'types': []})
            total_nodes = len(node_ids)

            for node_id in node_ids:
                if node_id in node_property_map:
                    for prop, val in node_property_map[node_id].items():
                        property_counts[prop]['count'] += 1
                        property_counts[prop]['types'].append(infer_data_type(val))

            for prop, data in property_counts.items():
                if data['count'] == total_nodes:
                    type_instance.properties[prop] = Counter(data['types']).most_common(1)[0][0]
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = Counter(data['types']).most_common(1)[0][0]
