from abc import ABC, abstractmethod
from neo4j.time import Date, Time, DateTime, Duration
from neo4j.spatial import Point
def infer_data_type( value):
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

def change_references(types):
    mapping = conceptid_to_name_mapping(types)
    for type_ in types:
        type_.subtypes = set([mapping[concept_id] for concept_id in type_.subtypes])
        type_.supertypes = set([mapping[concept_id] for concept_id in type_.supertypes])

def conceptid_to_name_mapping( types):
    return {type_.concept_id: type_.name for type_ in types}

def merge_types(config, types):
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
        if best_pair is None or best_similarity < config.get("label_based_merge_threshold"):
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

class BaseTypeExtractor(ABC):
    def __init__(self, config, fca_helper, graph_data, graph_type):
        self.config = config
        self.fca_helper = fca_helper
        self.graph_data = graph_data
        self.graph_type = graph_type

    @abstractmethod
    def extract_types(self):
        pass
