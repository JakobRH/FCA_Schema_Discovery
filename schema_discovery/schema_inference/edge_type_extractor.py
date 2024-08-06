from .base_type_extractor import BaseTypeExtractor
from .type import Type

class EdgeTypeExtractor(BaseTypeExtractor):
    def extract_types(self):
        approach = self.config['edge_type_extraction']['approach']
        # Define approaches for edge type extraction
        # For now, we'll just implement a placeholder method
        if approach == 'simple':
            return self._extract_simple_edge_types()
        else:
            raise ValueError("Unsupported edge type extraction approach")

    def _extract_simple_edge_types(self):
        types = []
        for concept in self.concept_lattice:
            labels = concept.intent
            edges = concept.extent
            type_ = Type(name="EdgeType_" + str(len(types)), labels=labels, properties={})
            for edge in edges:
                type_.add_edge(edge)
            types.append(type_)
        self._determine_hierarchy(types)
        return types
