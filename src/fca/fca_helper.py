import pandas as pd
from fcapy.context import FormalContext
from fcapy.lattice import ConceptLattice
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from fcapy.visualizer import LineVizNx


class FCAHelper:
    """
    Class to generate concept lattices for nodes and edges based ont the given graph data using the fcapy library.
    It also saves a visualization of the concept lattices. It also allows querying sub-concepts and super-concepts
    in these lattices.
    """
    def __init__(self, config):
        self.config = config
        self.node_context = None
        self.node_concept_lattice = None
        self.edge_context = None
        self.edge_concept_lattice = None

    def generate_node_concept_lattice(self, graph_data):
        """
        Generates a concept lattice for nodes of the given graph and saves the visualization output as a PNG.

        :param graph_data: The graph data from which node concept lattices are generated.
        """
        node_data = self._create_node_dataframe(graph_data)
        self.node_context = FormalContext.from_pandas(node_data)
        self.node_concept_lattice = ConceptLattice.from_context(self.node_context)

        fig, ax = plt.subplots(figsize=(10, 5))
        vsl = LineVizNx()
        vsl.draw_concept_lattice(self.node_concept_lattice, ax=ax, flg_node_indices=True)
        ax.set_title('Node Concept Lattice', fontsize=18)
        plt.tight_layout()
        plt.savefig(self.config.get("out_dir") + "node_concept_lattice.png")

    def generate_edge_concept_lattice(self, graph_data):
        """
        Generates a concept lattice for edges of the given graph and saves the visualization output as a PNG.

        :param graph_data: The graph data from which edge concept lattices are generated.
        """
        edge_data = self._create_edge_dataframe(graph_data)
        self.edge_context = FormalContext.from_pandas(edge_data)
        self.edge_concept_lattice = ConceptLattice.from_context(self.edge_context)

        fig, ax = plt.subplots(figsize=(10, 5))
        vsl = LineVizNx()
        vsl.draw_concept_lattice(self.edge_concept_lattice, ax=ax, flg_node_indices=True)
        ax.set_title('Edge Concept Lattice', fontsize=18)
        plt.tight_layout()
        plt.savefig(self.config.get("out_dir") + "edge_concept_lattice.png")

    def _create_node_dataframe(self, graph_data):
        """
       Creates a pandas DataFrame from the node data in the graph based on the extraction mode.

       :param graph_data: The graph data containing nodes and their properties.
       :return: A pandas DataFrame with nodes as rows and labels/properties as columns.
       """
        nodes = list(graph_data.nodes.values())

        all_labels = sorted({label for node in nodes for label in node.labels})
        all_properties = sorted({key for node in nodes for key in node.properties.keys()})

        extraction_mode = self.config.get("node_type_extraction")
        columns = []
        if extraction_mode == "label_based":
            columns = all_labels
        elif extraction_mode == "property_based":
            columns = all_properties
        elif extraction_mode == "label_property_based":
            columns = all_labels + all_properties
        if not columns:
            columns = ['']
        data = {node.id: {col: False for col in columns} for node in nodes}

        for node in nodes:
            node_data = data[node.id]

            if extraction_mode == "label_based" or extraction_mode == "label_property_based":
                for label in node.labels:
                    node_data[label] = True

            if extraction_mode == "property_based" or extraction_mode == "label_property_based":
                for key in node.properties.keys():
                    node_data[key] = True

            data[node.id] = node_data

        df = pd.DataFrame.from_dict(data, orient='index').fillna(False)

        return df

    def _create_edge_dataframe(self, graph_data):
        """
        Creates a pandas DataFrame from the edge data in the graph based on the extraction mode.

        :param graph_data: The graph data containing edges and their properties.
        :return: A pandas DataFrame with edges as rows and labels/properties as columns.
        """
        edges = list(graph_data.edges.values())

        all_labels = sorted({label for edge in edges for label in edge.labels})
        all_properties = sorted({key for edge in edges for key in edge.properties.keys()})
        extraction_mode = self.config.get("edge_type_extraction")

        columns = []
        if extraction_mode == "label_based":
            columns = all_labels
        elif extraction_mode == "property_based":
            columns = all_properties
        elif extraction_mode == "label_property_based":
            columns = all_labels + all_properties
        if not columns:
            columns = ['']

        data = {edge.id: {col: False for col in columns} for edge in edges}

        for edge in edges:

            edge_data = data[edge.id]

            if extraction_mode == "label_based" or extraction_mode == "label_property_based":
                for label in edge.labels:
                    edge_data[label] = True

            if extraction_mode == "property_based" or extraction_mode == "label_property_based":
                for key in edge.properties.keys():
                    edge_data[key] = True

            data[edge.id] = edge_data

        df = pd.DataFrame.from_dict(data, orient='index').fillna(False)

        return df

    def get_node_sub_super_concepts(self, concept_id):
        """
        Retrieves the sub-concepts and super-concepts of a concept in the concept lattice.

        :param concept_id: The ID of the concept in the node concept lattice.
        :return: A tuple containing sub-concepts and super-concepts.
        """
        return self.node_concept_lattice.children_dict[concept_id], self.node_concept_lattice.parents_dict[concept_id]

    def get_edge_sub_super_concepts(self, concept_id):
        """
        Retrieves the sub-concepts and super-concepts of a concept in the concept lattice.

        :param concept_id: The ID of the concept in the edge concept lattice.
        :return: A tuple containing sub-concepts and super-concepts.
        """
        return self.edge_concept_lattice.children_dict[concept_id], self.edge_concept_lattice.parents_dict[concept_id]
