import json
import argparse

class Config:
    def __init__(self, config_path='config\config.json'):
        self.config = self._load_config(config_path)
        self._override_with_cli_args()

    def _load_config(self, config_path):
        with open(config_path, 'r') as file:
            return json.load(file)

    def _override_with_cli_args(self):
        parser = argparse.ArgumentParser(description='Override config values.')
        parser.add_argument('--data_source', type=str, help='Data source type')
        parser.add_argument('--neo4j_uri', type=str, help='Neo4j URI')
        parser.add_argument('--neo4j_user', type=str, help='Neo4j user')
        parser.add_argument('--neo4j_password', type=str, help='Neo4j password')
        parser.add_argument('--node_type_approach', type=str, help='Node type extraction approach')
        parser.add_argument('--edge_type_approach', type=str, help='Edge type extraction approach')
        parser.add_argument('--output_schema_file', type=str, help='Output schema file')

        args = parser.parse_args()

        if args.data_source:
            self.config['data_source'] = args.data_source
        if args.neo4j_uri:
            self.config['neo4j']['uri'] = args.neo4j_uri
        if args.neo4j_user:
            self.config['neo4j']['user'] = args.neo4j_user
        if args.neo4j_password:
            self.config['neo4j']['password'] = args.neo4j_password
        if args.node_type_approach:
            self.config['node_type_extraction']['approach'] = args.node_type_approach
        if args.edge_type_approach:
            self.config['edge_type_extraction']['approach'] = args.edge_type_approach
        if args.output_schema_file:
            self.config['output_schema_file'] = args.output_schema_file

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is default:
                break
        return value