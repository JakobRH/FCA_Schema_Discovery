from ..graph_data.graph_data import GraphData
class BaseExtractor:
    """
    Base class for extracting graph data. This class serves as a blueprint for
    creating different types of graph extractors.
    """

    def __init__(self, config):
        """
        Initializes the BaseExtractor with a configuration object.

        Args:
            config (dict): Configuration settings required for the extractor.
        """
        self.config = config  # Stores configuration settings
        self.graph_data = GraphData()  # Initializes an empty graph data object

    def extract_graph_data(self):
        """
        Abstract method that must be implemented by subclasses. This method will
        contain the logic for extracting graph data from a specific source or format.

        Raises:
            NotImplementedError: If a subclass does not override this method.
        """
        raise NotImplementedError("This method should be overridden by subclasses")