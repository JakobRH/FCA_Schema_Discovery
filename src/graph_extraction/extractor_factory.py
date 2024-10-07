from src.graph_extraction.neo4j_extractor import Neo4jExtractor


class ExtractorFactory:
    """
   Factory class responsible for creating extractor instances based on the specified
   data source in the configuration.
   """
    @staticmethod
    def get_extractor(config):
        """
        Static method that returns the appropriate extractor based on the data source
        provided in the config.

        Args:
            config (dict): Configuration settings, including the data source type.

        Returns:
            An instance of the appropriate extractor class.

        Raises:
            ValueError: If the data source specified in the config is not supported.
        """
        data_source = config.get("data_source")
        if data_source == "neo4j":
            return Neo4jExtractor(config)
        # Add more data source extractors here
        else:
            raise ValueError("Unsupported data source")
