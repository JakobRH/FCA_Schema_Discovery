import pandas as pd
from fcapy.context import FormalContext
from fcapy.lattice import ConceptLattice
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from fcapy.visualizer import LineVizNx


class FCAHelper:
    def __init__(self, config):
        self.config = config
        self.node_context = None
        self.node_concept_lattice = None
        self.edge_context = None
        self.edge_concept_lattice = None

    def generate_node_concept_lattice(self, graph_data):
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
        nodes = graph_data.nodes
        node_ids = [node.id for node in nodes]

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
        else:
            raise ValueError("extraction_mode must be 'label_based', 'property_based', or 'label_property_based'")

        df = pd.DataFrame(False, index=node_ids, columns=columns)

        for node in nodes:
            if extraction_mode == "label_based" or extraction_mode == "label_property_based":
                for label in node.labels:
                    df.at[node.id, label] = True
            if extraction_mode == "property_based" or extraction_mode == "label_property_based":
                for key, value in node.properties.items():
                    df.at[node.id, key] = True

        return df

    def _create_edge_dataframe(self, graph_data):
        edges = graph_data.edges.values()
        edge_ids = list(graph_data.edges.keys())

        all_labels = sorted({label for edge in edges for label in edge.labels})
        all_properties = sorted({key for edge in edges for key in edge.properties.keys()})

        extraction_mode = self.config.get("node_type_extraction")
        columns = []
        if extraction_mode == "label_based":
            columns = all_labels
        elif extraction_mode == "property_based":
            columns = all_properties
        elif extraction_mode == "label_property_based":
            columns = all_labels + all_properties
        else:
            raise ValueError("extraction_mode must be 'label_based', 'property_based', or 'label_property_based'")

        df = pd.DataFrame(False, index=edge_ids, columns=columns)

        for edge in edges:
            if extraction_mode == "label_based" or extraction_mode == "label_property_based":
                for label in edge.labels:
                    df.at[edge.id, label] = True
            if extraction_mode == "property_based" or extraction_mode == "label_property_based":
                for key, value in edge.properties.items():
                    df.at[edge.id, key] = True

        return df

    def get_node_sub_super_concepts(self, concept_id):
        return self.node_concept_lattice.children_dict[concept_id], self.node_concept_lattice.parents_dict[concept_id]

    def get_edge_sub_super_concepts(self, concept_id):
        return self.edge_concept_lattice.children_dict[concept_id], self.edge_concept_lattice.parents_dict[concept_id]
