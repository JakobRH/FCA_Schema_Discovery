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

    def generate_node_concept_lattice(self, node_data):
        self.node_context = FormalContext.from_pandas(node_data)
        self.node_concept_lattice = ConceptLattice.from_context(self.node_context)
        fig, ax = plt.subplots(figsize=(10, 5))
        vsl = LineVizNx()
        vsl.draw_concept_lattice(self.node_concept_lattice, ax=ax, flg_node_indices=True)
        ax.set_title('Node Concept Lattice', fontsize=18)
        plt.tight_layout()
        plt.savefig(self.config.get("out_dir")+"node_concept_lattice.png")

    def get_sub_super_concepts(self, concept_id):
        return self.node_concept_lattice.children_dict[concept_id], self.node_concept_lattice.parents_dict[concept_id]
