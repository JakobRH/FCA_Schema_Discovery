class Type:
    def __init__(self, concept_id, labels, properties, supertypes, subtypes):
        self.concept_id = concept_id
        self.labels = labels
        self.properties = properties
        self.nodes = set()
        self.edges = set()
        self.supertypes = supertypes
        self.subtypes = subtypes
        self.name = self._generate_name()

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, edge):
        self.edges.add(edge)

    def add_supertype(self, supertype):
        self.supertypes.add(supertype)

    def add_subtype(self, subtype):
        self.subtypes.add(subtype)

    def to_schema_part(self):
        return {
            "name": self.name,
            "labels": list(self.labels),
            "properties": list(self.properties.keys()),
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "subtypes": [subtype.name for subtype in self.subtypes],
            "supertypes": [supertype.name for supertype in self.supertypes]
        }

    def _generate_name(self):
        return "type" + str(self.concept_id)
