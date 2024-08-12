from ..graph_data.graph_data import GraphData
class BaseExtractor:

    def __init__(self, config):
        self.config = config
        self.graph_data = GraphData()

    def extract_graph_data(self):
        raise NotImplementedError("This method should be overridden by subclasses")