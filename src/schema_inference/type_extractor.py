from collections import defaultdict, Counter

from src.graph_type.type import Type


class TypeExtractor:
    """
    Extracts the type information based on the concept lattices of ndoes and edges.
    """
    def __init__(self, config, fca_helper, graph_data, graph_type, extraction_mode):
        """
        Initializes the TypeExtractor with the provided configuration, helper classes, and graph data.
        This class is responsible for extracting types (either NODE or EDGE) from a graph.

        @param config: A dictionary containing configuration settings for the extraction process.
        @param fca_helper: A helper object used for working with formal concept analysis (FCA).
        @param graph_data: The data structure representing the graph from which types will be extracted.
        @param graph_type: The type of the graph (e.g., directed, undirected, etc.).
        @param extraction_mode: A string indicating whether to extract 'NODE' or 'EDGE' types.
        """
        self.config = config
        self.fca_helper = fca_helper
        self.graph_data = graph_data
        self.graph_type = graph_type
        self.extraction_mode = extraction_mode

    def extract_types(self):
        """
        Extracts types based on the extraction mode and configuration settings. The method follows different
        strategies (label-based, property-based, etc.) depending on the configuration, and handles optional labels,
        properties, abstract type lookups, and endpoint computation for edges.

        @return: A list of extracted Type objects.
        """
        if self.extraction_mode == "NODE":
            approach = self.config.get("node_type_extraction")
        if self.extraction_mode == "EDGE":
            approach = self.config.get("edge_type_extraction")

        types = self._initialize_types(approach)
        self._remove_elements_in_subtypes(types)

        if approach == "label_based":
            self._compute_properties(types)
        if approach == "property_based":
            self._compute_labels(types)

        if (approach == "label_based" and self.config.get("optional_labels")) or \
                (approach == "property_based" and self.config.get("optional_properties")) or \
                (approach == "label_property_based"and self.config.get("optional_properties") and
                 self.config.get("optional_labels")):
            types = self._merge_types(types)
            if (self.config.get("max_types") and len(types) > self.config.get("max_node_types") and
                self.extraction_mode == "NODE") \
                    or (self.config.get("max_types") and len(types) > self.config.get("max_edge_types")
                        and self.extraction_mode == "EDGE"):
                types = self._max_types_merge(types)

        if self.config.get("abstract_type_lookup") and self.extraction_mode == "NODE":
            self._find_and_create_abstract_types(types)

        if self.extraction_mode == "EDGE":
            self._compute_endpoints(types)

        if self.config.get("remove_inherited_features"):
            type_dict = {type_.name: type_ for type_ in types}
            for type_ in types:
                type_.remove_inherited_features(type_dict)

        return types

    def _initialize_types(self, approach):
        """
        Initializes the types based on the concept lattice and the selected approach.

        @param approach: The approach used for initializing types.
        @return: A list of initialized Type objects.
                """
        if self.extraction_mode == "NODE":
            lattice = self.fca_helper.node_concept_lattice
        if self.extraction_mode == "EDGE":
            lattice = self.fca_helper.edge_concept_lattice

        types = []

        num_concepts = len(lattice)
        top_concept_id = 0
        bottom_concept_id = num_concepts - 1

        remove_top_concept = True if not lattice[top_concept_id].intent and not self.graph_data.is_top_concept_necessary(approach, self.extraction_mode) else False
        remove_bottom_concept = True if not lattice[bottom_concept_id].extent else False

        for concept_id, concept in enumerate(lattice):
            if concept_id == top_concept_id and remove_top_concept:
                continue
            if concept_id == bottom_concept_id and remove_bottom_concept:
                continue

            labels, properties = self._set_lattice_intent(concept.intent, approach)
            elements = concept.extent
            if self.extraction_mode == "NODE":
                subtypes, supertypes = self.fca_helper.get_node_sub_super_concepts(concept_id)
            if self.extraction_mode == "EDGE":
                subtypes, supertypes = self.fca_helper.get_edge_sub_super_concepts(concept_id)

            if remove_top_concept:
                supertypes = (x for x in supertypes if x != top_concept_id)
            if remove_bottom_concept:
                subtypes = (x for x in subtypes if x != bottom_concept_id)

            type_ = Type(self.config, concept_id=concept_id, labels=labels, properties=properties,
                         supertypes=supertypes, subtypes=subtypes, entity=self.extraction_mode)
            for element in elements:
                if self.extraction_mode == "NODE":
                    type_.add_node(element)
                if self.extraction_mode == "EDGE":
                    type_.add_edge(element)
            types.append(type_)
        self._change_references(types)
        return types

    def _change_references(self, types):
        """
        Updates the references between types by changing subtype and supertype references to use names instead of concept IDs.

        @param types: A list of Type objects to update their references.
        """
        mapping = self._conceptid_to_name_mapping(types)
        for type_ in types:
            type_.subtypes = set([mapping[concept_id] for concept_id in type_.subtypes])
            type_.supertypes = set([mapping[concept_id] for concept_id in type_.supertypes])

    def _conceptid_to_name_mapping(self, types):
        """
       Creates a mapping from concept IDs to type names for a given list of types.

       @param types: A list of Type objects.
       @return: A dict mapping concept IDs to type names.
       """
        return {type_.concept_id: type_.name for type_ in types}

    def _compute_property_data_types(self, properties):
        """
        Computes the data types for a given set of properties.
        It retrieves the corresponding property data types from the graph data.

        @param properties: A set or list of property names whose data types are to be computed.
        @return: A dictionary mapping property names to their corresponding data types.
        """
        properties_dict = {}
        for prop in properties:
            if self.extraction_mode == "NODE":
                properties_dict[prop] = self.graph_data.node_property_data_types[prop]
            if self.extraction_mode == "EDGE":
                properties_dict[prop] = self.graph_data.edge_property_data_types[prop]

        return properties_dict

    def _set_lattice_intent(self, intent, approach):
        """
        Sets the lattice intent by extracting labels or properties from the given intent based on the extraction approach.

        @param intent: The intent (attributes) from the concept lattice, which could be either labels or properties.
        @param approach: The extraction approach, one of 'label_based', 'property_based', or 'label_property_based'.
        @return: A tuple containing a list of labels and a dictionary of properties.
        """
        labels = []
        properties = []

        if approach == "label_based":
            labels = intent
            properties = {}
        if approach == "property_based":
            properties = self._compute_property_data_types(intent)
        if approach == "label_property_based":
            if self.extraction_mode == "NODE":
                all_labels = self.graph_data.get_all_node_labels()
            if self.extraction_mode == "EDGE":
                all_labels = self.graph_data.get_all_edge_labels()
            for attribute in intent:
                if attribute in all_labels:
                    labels.append(attribute)
                else:
                    properties.append(attribute)
            properties = self._compute_property_data_types(properties)
        return labels, properties

    def _remove_elements_in_subtypes(self, types):
        """
        Removes nodes or edges from a type if they are present in one of its subtypes.
        Operates recursively based on the type's subtype hierarchy.

        @param types: Types List.
        @return Updated Types List.
        """
        type_dict = {type_obj.name: type_obj for type_obj in types}
        for type_obj in types:
            if self.extraction_mode == 'NODE':
                all_subtypes = self._get_all_subtypes(type_obj, type_dict)
                for subtype in all_subtypes:
                    type_obj.nodes.difference_update(type_dict[subtype].nodes)

            elif self == self.extraction_mode == 'EDGE':
                all_subtypes = self._get_all_subtypes(type_obj, type_dict)

                for subtype in all_subtypes:
                    type_obj.edges.difference_update(type_dict[subtype].edges)

    def _get_all_subtypes(self, type_obj, type_dict):
        """
        Recursively retrieves all transitive subtypes for a given Type instance.

        @param type_obj: The Type instance for which to find subtypes.
        @param type_dict: A dictionary mapping type names to Type instances.
        @return: A set of all subtypes.
        """
        all_subtypes = set(type_obj.subtypes)
        for subtype_name in type_obj.subtypes:
            if subtype_name in type_dict:
                subtype = type_dict[subtype_name]
                all_subtypes.update(self._get_all_subtypes(subtype, type_dict))
        return all_subtypes

    def _compute_properties(self, types):
        """
        Computes the properties for each type instance, determining both mandatory and optional properties.
        If the property appears for all elements in the type, it is considered mandatory. If it appears
        for a percentage of elements above a certain threshold, it is marked as optional.

        @param types: A list of Type objects for which the properties are computed.
        """
        threshold = self.config.get("property_outlier_threshold")

        for type_instance in types:
            if self.extraction_mode == "NODE":
                element_ids = set(type_instance.nodes)
            if self.extraction_mode == "EDGE":
                element_ids = set(type_instance.edges)

            property_counts = defaultdict(lambda: {'count': 0})
            total_elements = len(element_ids)

            for element_id in element_ids:
                if self.extraction_mode == "NODE":
                    for prop, val in self.graph_data.nodes[element_id].properties.items():
                        property_counts[prop]['count'] += 1
                if self.extraction_mode == "EDGE":
                    for prop, val in self.graph_data.edges[element_id].properties.items():
                        property_counts[prop]['count'] += 1


            for prop, data in property_counts.items():
                if self.extraction_mode == "NODE":
                    data_type = self.graph_data.node_property_data_types[prop]
                if self.extraction_mode == "EDGE":
                    data_type = self.graph_data.edge_property_data_types[prop]

                if data['count'] == total_elements:
                    type_instance.properties[prop] = data_type
                elif data['count'] >= threshold:
                    type_instance.optional_properties[prop] = data_type

    def _compute_labels(self, types):
        """
        Computes the labels for each type instance, determining both mandatory and optional labels.
        If the label is present for all elements in the type, it is considered mandatory.
        If the label appears for a percentage of elements above a certain threshold, it is marked as optional.

        @param types: A list of Type objects for which the labels are computed.
        """
        threshold = self.config.get("label_outlier_threshold")

        for type_instance in types:
            if self.extraction_mode == "NODE":
                element_ids = set(type_instance.nodes)
            if self.extraction_mode == "EDGE":
                element_ids = set(type_instance.edges)
            label_counts = defaultdict(int)
            total_nodes = len(element_ids)

            for element_id in element_ids:
                if self.extraction_mode == "NODE":
                    element = self.graph_data.get_node_by_id(element_id)
                if self.extraction_mode == "EDGE":
                    element = self.graph_data.get_edge_by_id(element_id)

                for label in element.labels:
                    label_counts[label] += 1

            for label, count in label_counts.items():
                if count == total_nodes:
                    type_instance.labels.add(label)
                elif count >= threshold:
                    type_instance.optional_labels.add(label)

    def _find_most_similar_supertype(self, subtype, types):
        """
        Finds the most similar supertype for a given subtype using Jaccard similarity.

        @param subtype: The subtype for which the closest supertype is being searched.
        @param types: A list of all available types to search for potential supertypes.
        @return: The most similar supertype to the provided subtype.
        """
        best_similarity = -1
        best_supertype = None
        for supertype_name in subtype.supertypes:
            supertype = next((t for t in types if t.name == supertype_name), None)
            if supertype:
                similarity = subtype.jaccard_similarity(supertype)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_supertype = supertype
        return best_supertype

    def _merge_with_supertype(self, subtype, supertype, types):
        """
       Merges a subtype into its supertype and updates relationships in the types list.

       @param subtype: The type to be merged into the supertype.
       @param supertype: The supertype into which the subtype is being merged.
       @param types: A list of all available types, which will be updated during merging.
       """
        subtype.merge_into_other_type(supertype)
        types.remove(subtype)
        for type_ in types:
            if subtype.name in type_.supertypes:
                type_.supertypes.remove(subtype.name)
                type_.supertypes.add(supertype.name)
            if supertype.name in type_.supertypes:
                type_.supertypes.remove(supertype.name)
            if subtype.name in type_.subtypes:
                type_.subtypes.remove(subtype.name)

    def _merge_types(self, types):
        """
        Recursively looks for the most similar super/subtype relation in the types list. Merges until a pair
        of subtype and supertype is found where the similarity is not greater than the specified threshold for merging.

        @param types: A list of all types to be merged.
        @return: A list of merged types.
        """
        while True:
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

            if best_pair is None or best_similarity < self.config.get("merge_threshold"):
                break

            subtype, supertype = best_pair

            self._merge_with_supertype(subtype, supertype, types)

        return types

    def _find_most_similar_pair(self, types):
        """
        Finds the two most similar types based on Jaccard similarity.

        @param types: A list of all available types to compare.
        @return: A tuple containing the two most similar types.
        """
        best_similarity = -1
        best_pair = (None, None)
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                similarity = types[i].jaccard_similarity(types[j])
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (types[i], types[j])
        return best_pair

    def _max_types_merge(self, types):
        """
        Merges types until the number of types is reduced to the maximum allowed,
        prioritizing subtypes and supertypes relationships.

        @param types: A list of all available types to be reduced.
        @return: A reduced list of types after merging.
        """
        if self.extraction_mode == "NODE":
            max_types = self.config.get("max_node_types")
        if self.extraction_mode == "EDGE":
            max_types = self.config.get("max_edge_types")


        while len(types) > max_types:
            types_without_subtypes = [t for t in types if not t.subtypes]

            all_without_supertypes = all(not t.supertypes for t in types_without_subtypes)

            if types_without_subtypes and not all_without_supertypes:
                type_to_merge = None
                best_supertype = None
                best_similarity = -1

                for type_ in reversed(types_without_subtypes):
                    supertype = self._find_most_similar_supertype(type_, types)
                    if supertype:
                        similarity = type_.jaccard_similarity(supertype)
                        if similarity > best_similarity:
                            best_similarity = similarity
                            type_to_merge = type_
                            best_supertype = supertype
                self._merge_with_supertype(type_to_merge, best_supertype, types)

            else:
                type1, type2 = self._find_most_similar_pair(types)
                type1.merge_into_other_type(type2)
                types.remove(type1)
                type2.supertypes.clear()
                type2.subtypes.clear()

        return types

    def _find_and_create_abstract_types(self, types):
        """
        Finds and creates abstract types by identifying pairs of types with high similarity
        and merging their common features into a new abstract type.

        @param types: A list of all available types from which abstract types are created.
        """
        created_abstract_types = []
        supertypes_map = defaultdict(set)
        type_dict = {type_.name: type_ for type_ in types}
        for type_ in types:
            supertypes_map[type_] = type_._get_all_supertypes(type_dict)

        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                type1 = types[i]
                type2 = types[j]

                if (type2.name not in supertypes_map[type1] and
                        type1.name not in supertypes_map[type2]):

                    similarity = type1.jaccard_similarity(type2)

                    if similarity >= self.config.get("abstract_type_threshold"):
                        abstract_type = self._create_abstract_type(type1, type2)
                        created_abstract_types.append(abstract_type)

        types.extend(created_abstract_types)

    def _create_abstract_type(self, type1, type2):
        """
        Creates a new abstract type from two types by merging their shared properties and labels.

        @param type1: The first type to be merged into the abstract type.
        @param type2: The second type to be merged into the abstract type.
        @return: The newly created abstract type.
        """

        shared_labels = type1.labels.intersection(type2.labels)
        shared_optional_labels = type1.optional_labels.intersection(type2.optional_labels)
        shared_properties = {k: v for k, v in type1.properties.items() if
                             k in type2.properties and type2.properties[k] == v}
        shared_optional_properties = {k: v for k, v in type1.optional_properties.items() if
                                      k in type2.optional_properties and type2.optional_properties[k] == v}

        abstract_type = Type(
            config=self.config,
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

    def _compute_endpoints(self, edge_types):
        """
        Computes the startpoint and endpoint types for each edge type by analyzing
        the nodes connected to the edges.

        @param edge_types: A list of edge types for which to compute endpoints.
        """
        threshold = self.config.get("endpoint_outlier_threshold")

        node_id_to_types = defaultdict(set)
        for node_type in self.graph_type.node_types:
            for node_id in node_type.nodes:
                node_id_to_types[node_id].add(node_type.name)

        edge_type_to_startpoint_types = defaultdict(Counter)
        edge_type_to_endpoint_types = defaultdict(Counter)

        for edge_type in edge_types:
            for edge_id in edge_type.edges:
                edge = self.graph_data.get_edge_by_id(edge_id)
                start_node_types = node_id_to_types.get(edge.start_node_id)
                end_node_types = node_id_to_types.get(edge.end_node_id)

                if start_node_types:
                    for type_ in start_node_types:
                        edge_type_to_startpoint_types[edge_type.name][type_] += 1
                if end_node_types:
                    for type_ in end_node_types:
                        edge_type_to_endpoint_types[edge_type.name][type_] += 1

        for edge_type in edge_types:
            startpoint_candidates = edge_type_to_startpoint_types[edge_type.name]
            endpoint_candidates = edge_type_to_endpoint_types[edge_type.name]

            edge_type.startpoint_types = set(
                [node_type for node_type, count in startpoint_candidates.items() if count >= threshold]
            )

            edge_type.endpoint_types = set(
                [node_type for node_type, count in endpoint_candidates.items() if count >= threshold]
            )
            self._filter_subtypes(edge_type.startpoint_types, self.graph_type.node_types)
            self._filter_subtypes(edge_type.endpoint_types, self.graph_type.node_types)

    def _filter_subtypes(self, point_types, node_types):
        """
        Filters out subtypes from a set of point types, ensuring only the most specific types remain.

        @param point_types: A set of point types to be filtered.
        @param node_types: A list of all node types used to find subtypes.
        @return: None
        """
        to_remove = set()
        type_dict = {type_.name: type_ for type_ in node_types}
        for node_type in point_types:
            supertypes = type_dict.get(node_type).get_all_supertypes(type_dict)
            if any(supertype in point_types for supertype in supertypes):
                to_remove.add(node_type)

        point_types.difference_update(to_remove)
