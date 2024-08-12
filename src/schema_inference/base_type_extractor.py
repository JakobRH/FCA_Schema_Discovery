from abc import ABC, abstractmethod


class BaseTypeExtractor(ABC):
    def __init__(self, config, fca_helper, graph_data):
        self.config = config
        self.fca_helper = fca_helper
        self.graph_data = graph_data

    @abstractmethod
    def extract_types(self):
        pass
