from abc import ABC, abstractmethod
from collections import defaultdict

from neo4j.time import Date, Time, DateTime, Duration
from neo4j.spatial import Point

from src.graph_type.type import Type


def infer_data_type(value):
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


def conceptid_to_name_mapping(types):
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

        print("SUBTYPE: " + subtype.name, subtype.labels, subtype.properties)
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


def find_and_create_abstract_types(config, types):
    created_abstract_types = []

    # Compare each pair of types
    for i in range(len(types)):
        for j in range(i + 1, len(types)):
            type1 = types[i]
            type2 = types[j]

            # Calculate similarity
            similarity = type1.jaccard_similarity(type2)

            # If similarity is above the threshold, create an abstract type
            if similarity >= config.get("abstract_type_threshold"):
                abstract_type = _create_abstract_type(config, type1, type2)
                created_abstract_types.append(abstract_type)

    types.extend(created_abstract_types)


def _create_abstract_type(config, type1, type2):

    # Gather all unique labels and properties from both types
    shared_labels = type1.labels.intersection(type2.labels)
    shared_optional_labels = type1.optional_labels.intersection(type2.optional_labels)
    shared_properties = {k: v for k, v in type1.properties.items() if
                         k in type2.properties and type2.properties[k] == v}
    shared_optional_properties = {k: v for k, v in type1.optional_properties.items() if
                                  k in type2.optional_properties and type2.optional_properties[k] == v}

    abstract_type = Type(
        config=config,
        concept_id=0,
        labels=list(shared_labels),
        properties=shared_properties,
        supertypes=set(),
        subtypes={type1.name, type2.name},
        entity=type1.entity,
        is_abstract=True
    )
    abstract_type.optional_labels = shared_optional_labels
    abstract_type.optional_properties = shared_optional_properties

    type1.supertypes.add(abstract_type.concept_id)
    type2.supertypes.add(abstract_type.concept_id)

    type1.labels.difference_update(shared_labels)
    type2.labels.difference_update(shared_labels)

    type1.optional_labels.difference_update(shared_optional_labels)
    type2.optional_labels.difference_update(shared_optional_labels)

    type1.properties = {k: v for k, v in type1.properties.items() if k not in shared_properties}
    type2.properties = {k: v for k, v in type2.properties.items() if k not in shared_properties}

    type1.optional_properties = {k: v for k, v in type1.optional_properties.items() if
                                 k not in shared_optional_properties}
    type2.optional_properties = {k: v for k, v in type2.optional_properties.items() if
                                 k not in shared_optional_properties}

    return abstract_type

class BaseTypeExtractor(ABC):
    def __init__(self, config, fca_helper, graph_data, graph_type):
        self.config = config
        self.fca_helper = fca_helper
        self.graph_data = graph_data
        self.graph_type = graph_type

    @abstractmethod
    def extract_types(self):
        pass
