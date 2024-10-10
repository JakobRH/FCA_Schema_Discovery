from src.graph_extraction.extractor_factory import ExtractorFactory
import argparse
from config.config import Config
from src.graph_generator.SchemaParser import SchemaParser
from src.graph_generator.graph_generator import GraphGenerator
from src.graph_type.graph_type import GraphType
from src.schema_inference.type_extractor import TypeExtractor
from src.utils.validator import Validator
from utils.logger import setup_logger
from fca.fca_helper import FCAHelper


def main():
    parser = argparse.ArgumentParser(description='Schema Extractor Tool')
    parser.add_argument('--config', type=str, help='Path to config file', default='config\config.json')
    args = parser.parse_args()
    logger = setup_logger('schema_extractor', 'schema_extractor.log')
    logger.info('Start Schmema Discovery.')

    config = Config(logger, args.config)
    if not config.validate_config():
        return

    # Step 1: Extract data
    if config.get("graph_generator"):
        schema_file_path = config.get("graph_generator_schema_path")
        with open(schema_file_path, 'r') as file:
            schema_content = file.read()
        schema_parser = SchemaParser(schema_content)
        schema_parser.parse_schema()
        graph_generator = GraphGenerator(schema_parser)
        graph_data = graph_generator.generate_graph(10000, 100000)
        logger.info(f'Graph successfully generated. Graph has {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges.')
    else:
        extractor = ExtractorFactory.get_extractor(config)
        extractor.extract_graph_data()
        graph_data = extractor.graph_data
        logger.info('Data successfully extracted.')

    graph_data.infer_property_data_types()

    # Step 2: Perform FCA and extract Types from Concept Lattice
    node_fca_helper = FCAHelper(config)
    graph_type = GraphType(config)
    node_fca_helper.generate_node_concept_lattice(graph_data)
    logger.info('Node Concept Lattice successfully generated.')
    type_extractor = TypeExtractor(config, node_fca_helper, graph_data, graph_type, "NODE")
    graph_type.node_types = type_extractor.extract_types()
    logger.info('Node Types successfully extracted.')
    node_fca_helper.generate_edge_concept_lattice(graph_data)
    logger.info('Edge Concept Lattice successfully generated.')
    type_extractor.extraction_mode = "EDGE"
    graph_type.edge_types = type_extractor.extract_types()
    logger.info('Edge Types successfully extracted.')

    # Step 3: Create schema
    graph_type.create_schema()

    if config.get("validate_graph"):
        validator = Validator(graph_data, graph_type.node_types, graph_type.edge_types, config, logger)
        validator.validate_graph()

    logger.info('Schema extraction completed successfully.')


if __name__ == "__main__":
    main()