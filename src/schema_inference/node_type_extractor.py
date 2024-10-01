from .base_type_extractor import BaseTypeExtractor, change_references, merge_types, \
    find_and_create_abstract_types, max_types_merge
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
        types = self._initialize_types()
        self._compute_properties(types)

        if self.config.get("optional_labels"):
            if self.config.get("max_types") and len(types) > self.config.get("max_types"):
                types = max_types_merge(self.config, types)
            types = merge_types(self.config, types)

        if self.config.get("abstract_type_lookup"):
            find_and_create_abstract_types(self.config, types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _extract_property_based_types(self):
        types = self._initialize_types()
        self._compute_labels(types)

        if self.config.get("optional_properties"):
            if self.config.get("max_types") and len(types) > self.config.get("max_types"):
                types = max_types_merge(self.config, types)
            types = merge_types(self.config, types)

        if self.config.get("abstract_type_lookup"):
            find_and_create_abstract_types(self.config, types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _extract_label_property_based_types(self):
        types = self._initialize_types()

        if self.config.get("optional_labels") and self.config.get("optional_properties"):
            if self.config.get("max_types") and len(types) > self.config.get("max_types"):
                types = max_types_merge(self.config, types)
            types = merge_types(self.config, types)

        if self.config.get("abstract_type_lookup"):
            find_and_create_abstract_types(self.config, types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _initialize_types(self):
        """Initialize types based on FCA lattice."""
        approach = self.config.get("node_type_extraction")
        types = []
        num_concepts = len(self.fca_helper.node_concept_lattice)
        top_concept_id = 0
        bottom_concept_id = num_concepts - 1
        remove_top_concept = True if not self.fca_helper.node_concept_lattice[top_concept_id].intent else False
        remove_bottom_concept = True if not self.fca_helper.node_concept_lattice[bottom_concept_id].extent else False

        for concept_id, concept in enumerate(self.fca_helper.node_concept_lattice):
            if concept_id == top_concept_id and remove_top_concept:
                continue
            if concept_id == bottom_concept_id and remove_bottom_concept:
                continue
            labels, properties = self.set_lattice_intent(concept.intent, approach)
            nodes = concept.extent

            subtypes, supertypes = self.fca_helper.get_node_sub_super_concepts(concept_id)
            if remove_top_concept:
                supertypes = (x for x in supertypes if x != top_concept_id)
            if remove_bottom_concept:
                subtypes = (x for x in subtypes if x != bottom_concept_id)

            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties=properties,
                         supertypes=supertypes, subtypes=subtypes, entity="NODE")
            for node in nodes:
                type_.add_node(node)
            types.append(type_)

        change_references(types)
        return types

    def _compute_properties(self, types):
        threshold = self.config.get("property_outlier_threshold")

        for type_instance in types:
            node_ids = set(type_instance.nodes)
            property_counts = defaultdict(lambda: {'count': 0})
            total_nodes = len(node_ids)

            for node_id in node_ids:
                for prop, val in self.graph_data.nodes[node_id].properties.items():
                    property_counts[prop]['count'] += 1

            for prop, data in property_counts.items():
                data_type = self.graph_data.node_property_data_types[prop]
                if data['count'] == total_nodes:
                    type_instance.properties[prop] = data_type
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = data_type

    def _compute_labels(self, types):
        threshold = self.config.get("label_outlier_threshold")

        for type_instance in types:
            node_ids = set(type_instance.nodes)
            label_counts = defaultdict(int)
            total_nodes = len(node_ids)

            for node_id in node_ids:
                node = self.graph_data.get_node_by_id(node_id)

                for label in node.labels:
                    label_counts[label] += 1

            for label, count in label_counts.items():
                if count == total_nodes:
                    type_instance.labels.add(label)
                elif count >= threshold:
                    type_instance.optional_labels.add(label)

    def _compute_property_data_types(self, properties):
        properties_dict = {}
        for prop in properties:
            properties_dict[prop] = self.graph_data.node_property_data_types[prop]
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
            all_labels = self.graph_data.get_all_node_labels()
            for attribute in intent:
                if attribute in all_labels:
                    labels.append(attribute)
                else:
                    properties.update(attribute)
            properties = self._compute_property_data_types(properties)
        return labels, properties

