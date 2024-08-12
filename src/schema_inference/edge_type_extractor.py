from .base_type_extractor import BaseTypeExtractor
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
        for concept_id, concept in enumerate(self.fca_helper.edge_concept_lattice):
            if concept_id == 0 or concept_id == num_concepts - 1:
                continue  # Skip first and last concept
            labels = concept.intent
            edges = concept.extent
            subtypes, supertypes = self.fca_helper.get_edge_sub_super_concepts(concept_id)
            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties={}, supertypes=supertypes,
                         subtypes=subtypes, entity="EDGE")
            for edge in edges:
                type_.add_edge(edge)
            types.append(type_)

        top_concept_id = 0
        bottom_concept_id = num_concepts - 1
        mapping = self._conceptid_to_name_mapping(types)
        # Remove references to the top and bottom concepts in subtypes and supertypes
        for type_ in types:
            type_.subtypes = set([st for st in type_.subtypes if st != top_concept_id and st != bottom_concept_id])
            type_.supertypes = set([st for st in type_.supertypes if st != top_concept_id and st != bottom_concept_id])
            type_.subtypes = set([mapping[concept_id] for concept_id in type_.subtypes])
            type_.supertypes = set([mapping[concept_id] for concept_id in type_.supertypes])

        self._compute_properties(types)

        if self.config.get("optional_labels"):
            types = self._merge_types(types)

        for type_ in types:
            type_.remove_inherited_features(types)

        return types
