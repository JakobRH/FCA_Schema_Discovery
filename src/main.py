from src.graph_extraction.extractor_factory import ExtractorFactory
import argparse
from config.config import Config
from src.graph_generator.SchemaParser import SchemaParser
from src.graph_generator.graph_generator import GraphGenerator
from src.graph_type.graph_type import GraphType
from src.utils.validator import Validator
from utils.logger import setup_logger
from fca.fca_helper import FCAHelper
from schema_inference.node_type_extractor import NodeTypeExtractor
from schema_inference.edge_type_extractor import EdgeTypeExtractor


def main():
    parser = argparse.ArgumentParser(description='Schema Extractor Tool')
    parser.add_argument('--config', type=str, help='Path to config file', default='config\config.json')
    parser.add_argument('--output', type=str, help='Output schema file', default=None)
    args = parser.parse_args()

    config = Config(args.config)

    if args.output:
        config.config['output_schema_file'] = args.output

    logger = setup_logger('schema_extractor', 'schema_extractor.log')
    logger.info('Start Schmema Discovery.')

    # Step 1: Extract data
    if config.get("data_generator"):
        schema_file_path = config.get("graph_generator_schema_path")
        with open(schema_file_path, 'r') as file:
            schema_content = file.read()
        schema_parser = SchemaParser(schema_content)
        schema_parser.parse_schema()
        graph_generator = GraphGenerator(schema_parser)
        graph_data = graph_generator.generate_graph(10000, 100000)
    else:
        extractor = ExtractorFactory.get_extractor(config)
        extractor.extract_graph_data()
        graph_data = extractor.graph_data

    graph_data.infer_property_data_types()

    # Step 2: Perform FCA
    node_fca_helper = FCAHelper(config)
    graph_type = GraphType(config)

    node_fca_helper.generate_node_concept_lattice(graph_data)
    node_type_extractor = NodeTypeExtractor(config, node_fca_helper, graph_data, graph_type)
    graph_type.node_types = node_type_extractor.extract_types()

    node_fca_helper.generate_edge_concept_lattice(graph_data)
    edge_type_extractor = EdgeTypeExtractor(config, node_fca_helper, graph_data, graph_type)
    graph_type.edge_types = edge_type_extractor.extract_types()

    # Step 4: Create schema
    graph_type.create_schema()

    if config.get("validate_graph"):
        validator = Validator(graph_data, graph_type.node_types, graph_type.edge_types, config)
        validator.validate_graph()

    logger.info('Schema extraction completed successfully.')


if __name__ == "__main__":
    main()