from .base_type_extractor import BaseTypeExtractor
from .type import Type
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
        for concept_id, concept in enumerate(self.fca_helper.node_concept_lattice):
            if concept_id == 0 or concept_id == num_concepts - 1:
                continue  # Skip first and last concept
            labels = concept.intent
            nodes = concept.extent
            subtypes, supertypes = self.fca_helper.get_sub_super_concepts(concept_id)
            type_ = Type(concept_id=concept_id, labels=labels, properties={}, supertypes=supertypes, subtypes=subtypes)
            for node in nodes:
                type_.add_node(node)
            types.append(type_)

        top_concept_id = 0
        bottom_concept_id = num_concepts - 1
        # Remove references to the top and bottom concepts in subtypes and supertypes
        for type_ in types:
            type_.subtypes = [st for st in type_.subtypes if st != top_concept_id and st != bottom_concept_id]
            type_.supertypes = [st for st in type_.supertypes if st != top_concept_id and st != bottom_concept_id]
        for typex in types:
            print(typex.name, typex.subtypes, typex.supertypes,typex.labels)
        # self._determine_hierarchy(types)
        return types


    def _extract_property_based_types(self):
        types = []
        return types

    def _extract_label_property_based_types(self):
        types = []
        return types

