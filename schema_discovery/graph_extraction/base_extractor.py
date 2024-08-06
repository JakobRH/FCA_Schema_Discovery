class BaseExtractor:

    def __init__(self, config):
        self.config = config

    def extract_node_data(self):
        raise NotImplementedError("This method should be overridden by subclasses")