import random
import string
from datetime import date, timedelta, time, datetime

from src.graph_data.graph_data import GraphData, Node, Edge


class GraphGenerator:
    def __init__(self, schema_parser):
        self.schema_parser = schema_parser
        self.graph_data = GraphData()

    def _random_string(self, length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def _random_value(self, data_type):
        if data_type == "STRING":
            return self._random_string()
        elif data_type == "INTEGER":
            return random.randint(0, 100)
        elif data_type == "FLOAT":
            return random.uniform(0.0, 100.0)
        elif data_type == "BOOLEAN":
            return random.choice([True, False])
        elif data_type == "LIST":
            return [self._random_string() for _ in range(random.randint(1, 5))]
        elif data_type == "MAP":
            return {self._random_string(): self._random_string() for _ in
                    range(random.randint(1, 5))}
        elif data_type == "DATE":
            start_date = date(2000, 1, 1)
            end_date = date.today()
            return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        elif data_type == "TIME":
            return time(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        elif data_type == "DATETIME":
            start_date = datetime(2000, 1, 1)
            end_date = datetime.now()
            return start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
        elif data_type == "DURATION":
            return timedelta(seconds=random.randint(0, 3600 * 24 * 365))
        elif data_type == "POINT":
            return {"x": random.uniform(-180.0, 180.0), "y": random.uniform(-90.0, 90.0)}
        else:
            return None

    def generate_graph(self, num_nodes=10, num_edges=15):
        for node_type_name, node_type in self.schema_parser.node_types.items():
            for _ in range(num_nodes):
                node_id = self._random_string()
                labels = node_type.get('labels', [])
                properties = {
                    prop['key']: self._random_value(prop['type'])
                    for prop in node_type.get('properties', [])
                }
                node = Node(node_id, labels, properties)
                self.graph_data.add_node(node)

        # Generate edges
        for edge_type_name, edge_type in self.schema_parser.edge_types.items():
            for _ in range(num_edges):
                edge_id = self._random_string()
                start_node = random.choice(list(self.graph_data.nodes.values()))
                end_node = random.choice(list(self.graph_data.nodes.values()))
                labels = edge_type.get('labels', [])
                properties = {
                    prop['key']: self._random_value(prop['type'])
                    for prop in edge_type.get('properties', [])
                }
                edge = Edge(edge_id, start_node.id, end_node.id, labels, properties)
                self.graph_data.add_edge(edge)

        # Infer global property data types after graph generation
        self.graph_data.infer_property_data_types()

        return self.graph_data