import random
import string
from datetime import date, timedelta, time, datetime

from src.graph_data.graph_data import GraphData, Node, Edge


class GraphGenerator:
    """
    Creates a graph data instance based on a schema.
    """
    def __init__(self, parser, config):
        self.config = config
        self.parser = parser
        self.graph_data = GraphData()
        self.node_type_to_nodes = {}

    def _random_string(self, length=6):
        """
        Generate a random string of a given length.

        @param length: Length of the string to generate.
        @return: A random string consisting of uppercase letters and digits.
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def _generate_random_value(self, data_type):
        """
        Generate a random value based on the given data type.

        @param data_type: The type of the value to generate.
        @return: A random value corresponding to the data type or None if the data type is unknown.
        """
        if data_type == "STRING" or data_type == "UNKNOWN":
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

    def _get_random_node_from_type(self, node_type):
        """
        Get a random node ID from nodes of a given node type.

        @param node_type: Type of the node to get.
        @:return: Random node ID of the given type.
        """
        if node_type in self.node_type_to_nodes:
            return random.choice(self.node_type_to_nodes[node_type])
        return None

    def generate_graph(self):
        """
        Generates a graph data instance based on the given schema. For each type
        a number between min_number_of_elements and max_number_of_elements of
        nodes or edges is created.

        @param min_number_of_elements: Minimum number of elements to be created for each type.
        @param max_number_of_elements: Maximum number of elements to be created for each type.
        @:return: A graph data instance based on the specified schema.
        """
        min_number_of_elements = self.config.get("graph_generator_min_entities")
        max_number_of_elements = self.config.get("graph_generator_max_entities")
        for node_type_name, node_type_def in self.parser.node_types.items():
            if node_type_def["abstract"]:
                continue
            num_nodes = random.randint(min_number_of_elements, max_number_of_elements)
            self.node_type_to_nodes[node_type_name] = []
            for _ in range(num_nodes):
                node_id = f"node_{len(self.graph_data.nodes) + 1}"
                labels = node_type_def["labels"].copy()
                for opt_label in node_type_def.get("optional_labels", []):
                    if random.choice([True, False]):
                        labels.append(opt_label)

                properties = {}

                for prop_name, prop_type in node_type_def.get("properties", {}).items():
                    properties[prop_name] = self._generate_random_value(prop_type)

                for prop_name, prop_type in node_type_def.get("optional_properties", {}).items():
                    if random.choice([True, False]):
                        properties[prop_name] = self._generate_random_value(prop_type)

                node = Node(node_id, labels=labels, properties=properties)
                self.graph_data.add_node(node)
                self.node_type_to_nodes[node_type_name].append(node_id)

        for edge_type_name, edge_type_def in self.parser.edge_types.items():
            if edge_type_def["abstract"]:
                continue
            num_edges = random.randint(min_number_of_elements, max_number_of_elements)

            for _ in range(num_edges):
                edge_id = f"edge_{len(self.graph_data.edges) + 1}"

                start_node_type = random.choice(edge_type_def["start_node_types"])

                start_node_id = self._get_random_node_from_type(start_node_type)

                if start_node_id == None:
                    raise ValueError(f"Wrong definition of Endpoint Types.")

                end_node_type = random.choice(edge_type_def["end_node_types"])
                end_node_id = self._get_random_node_from_type(end_node_type)

                if end_node_id == None:
                    raise ValueError(f"Wrong definition of Endpoint Types.")

                labels = edge_type_def["labels"].copy()

                for opt_label in edge_type_def.get("optional_labels", []):

                    if random.choice([True, False]):
                        labels.append(opt_label)

                properties = {}

                for prop_name, prop_type in edge_type_def.get("properties", {}).items():
                    properties[prop_name] = self._generate_random_value(prop_type)

                for prop_name, prop_type in edge_type_def.get("optional_properties", {}).items():
                    if random.choice([True, False]):
                        properties[prop_name] = self._generate_random_value(prop_type)

                edge = Edge(edge_id, start_node_id, end_node_id, labels=labels, properties=properties)
                self.graph_data.add_edge(edge)

        return self.graph_data
