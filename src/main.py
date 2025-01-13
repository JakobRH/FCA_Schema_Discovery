from src.graph_extraction.extractor_factory import ExtractorFactory
import argparse
from config.config import Config
from src.graph_generator.schema_parser import SchemaParser
from src.graph_generator.graph_generator import GraphGenerator
from src.graph_type.graph_type import GraphType
from src.schema_inference.type_extractor import TypeExtractor
from src.schema_merger.schema_merger import SchemaMerger
from src.utils.validator import Validator
from utils.logger import setup_logger
from fca.fca_helper import FCAHelper
import time

def main():
    parser = argparse.ArgumentParser(description='Schema Extractor Tool')
    parser.add_argument('--config', type=str, help='Path to config file', default='config\config.json')
    args = parser.parse_args()

    logger = setup_logger('schema_extractor', 'schema_extractor.log')
    start_time = time.time()

    def log_with_time(message):
        elapsed = time.time() - start_time
        logger.info(f"[{elapsed:.2f}s] {message}")

    log_with_time('Start Schema Discovery.')

    config = Config(logger, args.config)
    if not config.validate_config():
        return

    # Step 1: Extract data
    if config.get("graph_generator"):
        schema_file_path = config.get("graph_generator_schema_path")
        with open(schema_file_path, 'r') as file:
            schema_content = file.read()
        schema_parser = SchemaParser(config, schema_content)
        schema_parser.parse_schema()
        graph_generator = GraphGenerator(schema_parser, config)
        graph_data = graph_generator.generate_graph()
        log_with_time(f'Graph successfully generated. Graph has {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges.')
    else:
        extractor = ExtractorFactory.get_extractor(config)
        extractor.extract_graph_data()
        graph_data = extractor.graph_data
        log_with_time('Data successfully extracted.')

    graph_data.infer_property_data_types()

    # Step 2: Perform FCA and extract Types from Concept Lattice
    node_fca_helper = FCAHelper(config)
    graph_type = GraphType(config)
    node_fca_helper.generate_node_concept_lattice(graph_data)
    log_with_time('Node Concept Lattice successfully generated.')

    type_extractor = TypeExtractor(config, node_fca_helper, graph_data, graph_type, "NODE")
    graph_type.node_types = type_extractor.extract_types()
    log_with_time('Node Types successfully extracted.')

    node_fca_helper.generate_edge_concept_lattice(graph_data)
    log_with_time('Edge Concept Lattice successfully generated.')

    type_extractor.extraction_mode = "EDGE"
    graph_type.edge_types = type_extractor.extract_types()
    log_with_time('Edge Types successfully extracted.')

    # Step 3: Create schema
    graph_type.create_schema()

    log_with_time('Schema extraction completed successfully.')

    if config.get("validate_graph"):
        validator = Validator(graph_data, graph_type.node_types, graph_type.edge_types, config, logger)
        validator.validate_graph()
        log_with_time('Graph validation completed.')

    if config.get("merge_schema"):
        schema_file_path = config.get("schema_to_merge_path")
        with open(schema_file_path, 'r') as file:
            schema_content = file.read()
        schema_parser = SchemaParser(config, schema_content)
        schema_parser.parse_schema()
        original_node_types = schema_parser.get_node_types()
        original_edge_types = schema_parser.get_edge_types()
        schema_merger = SchemaMerger(config)
        merged_node_types, merged_edge_types = schema_merger.merge_schemas(original_node_types, original_edge_types, graph_type.node_types, graph_type.edge_types)
        graph_type.node_types = merged_node_types
        graph_type.edge_types = merged_edge_types
        graph_type.create_schema(name="merged_schema.pgs", nodes_and_edges=False)

        log_with_time(f'Merged the new schema with the original one.')

    total_time = time.time() - start_time
    log_with_time(f'Total execution time: {total_time:.2f}s')

if __name__ == "__main__":
    main()
