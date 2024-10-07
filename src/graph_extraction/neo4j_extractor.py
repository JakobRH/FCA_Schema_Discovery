from .base_extractor import BaseExtractor
from neo4j import GraphDatabase
from ..graph_data.graph_data import Node, Edge

# Retrieves nodes, their labels, and their properties from the Neo4j database
def get_nodes_labels_and_properties(tx):
    query = """
        MATCH (n)
        RETURN DISTINCT id(n) AS node_id, labels(n) AS labels, properties(n) AS props
        """
    result = tx.run(query)
    return [(record["node_id"], record["labels"], record["props"]) for record in result]

# Retrieves edges, their type, properties, and start/end node IDs from the Neo4j database
def get_edges_labels_and_properties(tx):
    query = """
            MATCH (start)-[r]->(end)
            RETURN DISTINCT id(r) AS edge_id, type(r) AS type, properties(r) AS props, id(start) AS start_node_id, id(end) AS end_node_id
            """
    result = tx.run(query)
    return [(record["edge_id"], record["type"], record["props"], record["start_node_id"], record["end_node_id"]) for
            record in result]


class Neo4jExtractor(BaseExtractor):
    """
    Class for extracting graph data from a Neo4j database.
    """
    def __init__(self, config):
        super().__init__(config)

    def extract_graph_data(self):
        """
       Extracts graph data from the Neo4j database.
       Connects to the database, retrieves nodes, edges and corresponding labels and properties and populates the
       graph_data attribute.
       """
        driver = GraphDatabase.driver(self.config.get("neo4j.uri"),
                                      auth=(self.config.get("neo4j.username"), self.config.get("neo4j.password")))

        with driver.session() as session:
            node_data = session.read_transaction(get_nodes_labels_and_properties)
            edge_data = session.read_transaction(get_edges_labels_and_properties)
        driver.close()

        for node_id, labels, props in node_data:
            node = Node(node_id, labels, props)
            self.graph_data.add_node(node)

        for edge_id, etype, props, start_node_id, end_node_id in edge_data:
            edge = Edge(edge_id, start_node_id, end_node_id, [etype], props)
            self.graph_data.add_edge(edge)
