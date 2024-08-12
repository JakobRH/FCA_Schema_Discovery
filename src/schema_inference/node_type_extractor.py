from .base_type_extractor import BaseTypeExtractor
from src.graph_type.type import Type
from collections import defaultdict, Counter
from neo4j.time import Date, Time, DateTime, Duration
from neo4j.spatial import Point


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

        self._change_references(types)

        self._compute_properties(types)

        if self.config.get("optional_labels"):
            types = self._merge_types(types)

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
                        property_counts[prop]['types'].append(self._infer_data_type(val))

            for prop, data in property_counts.items():
                if data['count'] == total_nodes:
                    type_instance.properties[prop] = Counter(data['types']).most_common(1)[0][0]
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = Counter(data['types']).most_common(1)[0][0]

    def _infer_data_type(self, value):
        if isinstance(value, str):
            return "STRING"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "FLOAT"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, list):
            return "LIST"
        elif isinstance(value, dict):
            return "MAP"
        elif isinstance(value, Date):
            return "DATE"
        elif isinstance(value, Time):
            return "TIME"
        elif isinstance(value, DateTime):
            return "DATETIME"
        elif isinstance(value, Duration):
            return "DURATION"
        elif isinstance(value, Point):
            return "POINT"
        else:
            return "UNKNOWN"

    def _merge_types(self, types):
        while True:
            # Step 1: Calculate similarity between all sub/supertype pairs
            best_similarity = 0
            best_pair = None

            for type_ in types:
                for supertype_name in type_.supertypes:
                    supertype = next((t for t in types if t.name == supertype_name), None)
                    if supertype:
                        similarity = type_.jaccard_similarity(supertype)
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_pair = (type_, supertype)

            # Step 2: If the best similarity is below the threshold, stop
            if best_pair is None or best_similarity < self.config.get("label_based_merge_threshold"):
                break

            # Step 3: Merge the most similar pair
            subtype, supertype = best_pair
            subtype.merge_with_supertype(supertype)

            # Step 4: Update relationships
            types.remove(subtype)

            for type_ in types:
                # Update all references to sub1 in other types' supertypes lists
                if subtype.name in type_.supertypes:
                    type_.supertypes.remove(subtype.name)
                    type_.supertypes.add(supertype.name)

                # Remove references to sub2 in all types' supertypes lists
                if supertype.name in type_.supertypes:
                    type_.supertypes.remove(supertype.name)

                # Remove references to sub1 in all types' subtypes lists
                if subtype.name in type_.subtypes:
                    type_.subtypes.remove(subtype.name)

        return types

    def _change_references(self, types):
        mapping = self._conceptid_to_name_mapping(types)
        for type_ in types:
            type_.subtypes = set([mapping[concept_id] for concept_id in type_.subtypes])
            type_.supertypes = set([mapping[concept_id] for concept_id in type_.supertypes])

    def _conceptid_to_name_mapping(self, types):
        return {type_.concept_id: type_.name for type_ in types}
