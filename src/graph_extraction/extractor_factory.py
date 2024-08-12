from src.graph_extraction.neo4j_extractor import Neo4jExtractor


class ExtractorFactory:
    @staticmethod
    def get_extractor(config):
        data_source = config.get("data_source")
        if data_source == "neo4j":
            return Neo4jExtractor(config)
        # Add more data source extractors here
        else:
            raise ValueError("Unsupported data source")
