from schema_discovery.graph_extraction.extractor_factory import ExtractorFactory
import argparse
from config.config import Config
from utils.logger import setup_logger
from fca.fca_helper import FCAHelper
from schema_inference.node_type_extractor import NodeTypeExtractor
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
    node_data = extractor.extract_node_data()

    # Step 2: Perform FCA
    node_fca_helper = FCAHelper(config)
    node_fca_helper.generate_node_concept_lattice(node_data)

    # Step 3: Extract types
    node_type_extractor = NodeTypeExtractor(extractor, node_fca_helper, config)
    node_types = node_type_extractor.extract_types()

    #edge_type_extractor = EdgeTypeExtractor(edge_concept_lattice, config)
    #edge_types = edge_type_extractor.extract_types()

    # Step 4: Create schema
    #schema_creator = SchemaCreator(node_types, edge_types)
    #schema = schema_creator.create_schema()
    #schema_creator.save_schema(config.get('output_schema_file'))

    logger.info('Schema extraction completed successfully.')


if __name__ == "__main__":
    main()