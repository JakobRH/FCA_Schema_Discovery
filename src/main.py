from src.graph_extraction.extractor_factory import ExtractorFactory
import argparse
from config.config import Config
from src.graph_type.graph_type import GraphType
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

    logger.info('Schema extraction completed successfully.')


if __name__ == "__main__":
    main()