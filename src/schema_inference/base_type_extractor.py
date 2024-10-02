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


def find_most_similar_supertype(subtype, types):
    """ Find the most similar supertype for a given subtype. """
    best_similarity = -1
    best_supertype = None
    for supertype_name in subtype.supertypes:
        supertype = next((t for t in types if t.name == supertype_name), None)
        if supertype:
            similarity = subtype.jaccard_similarity(supertype)
            if similarity > best_similarity:
                best_similarity = similarity
                best_supertype = supertype
    return subtype, best_supertype

def merge(subtype, supertype, types):
    supertype.merge_with_supertype(subtype)
    types.remove(subtype)  # Remove the merged subtype from the types list
    # Update relationships in the remaining types
    for type_ in types:
        # Update supertype references
        if subtype.name in type_.supertypes:
            type_.supertypes.remove(subtype.name)
            type_.supertypes.add(supertype.name)
        # Update subtype references
        if supertype.name in type_.supertypes:
            type_.supertypes.remove(supertype.name)

        # Remove references to sub1 in all types' subtypes lists
        if subtype.name in type_.subtypes:
            type_.subtypes.remove(subtype.name)


def merge_types(config, types):
    while True:
        # Step 1: Calculate similarity between all sub/supertype pairs
        best_similarity = 0
        best_pair = None

        for type_ in types:
            best_pair = find_most_similar_supertype(type_, types)

        # Step 2: If the best similarity is below the threshold, stop
        if best_pair is None or best_similarity < config.get("label_based_merge_threshold"):
            break

        # Step 3: Merge the most similar pair
        subtype, supertype = best_pair
        merge(subtype, supertype, types)

    return types

def max_types_merge(config, types):
    max_types = config.get("max_result_types")
    while len(types) > max_types:
        merged = False  # Flag to check if any merge happens in the iteration

        # Start from the end of the types list and try to merge each type with its most similar supertype
        for type_ in reversed(types):
            if type_.supertypes:
                # Find the most similar supertype
                subtype, best_supertype = find_most_similar_supertype(type_, types)
                if best_supertype:
                    # Perform the merge
                    merge(subtype, best_supertype, types)
                    merged = True
                    break  # We can break since we modified the list and want to recheck from the end

        # If no types were merged in the previous step, stop merging
        if not merged:
            break

    while len(types) > max_types:
        # Find the most similar pair of types without supertypes
        best_similarity = -1
        best_pair = None
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                type1 = types[i]
                type2 = types[j]
                similarity = type1.jaccard_similarity(type2)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (type1, type2)

        if best_pair:
            subtype, supertype = best_pair
            merge(subtype, supertype, types)

    return types

def find_and_create_abstract_types(config, types):
    created_abstract_types = []
    supertypes_map = defaultdict(set)
    type_dict = {type_.name: type_ for type_ in types}
    for type_ in types:
        supertypes_map[type_].update(type_.get_all_supertypes(type_dict))

    # Compare each pair of types
    for i in range(len(types)):
        for j in range(i + 1, len(types)):
            type1 = types[i]
            type2 = types[j]

            if (type2 not in supertypes_map[type1] and
                    type1 not in supertypes_map[type2]):
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

    type1.supertypes.add(abstract_type.name)
    type2.supertypes.add(abstract_type.name)

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
