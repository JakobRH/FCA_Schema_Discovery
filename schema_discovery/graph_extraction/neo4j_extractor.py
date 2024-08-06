from .base_extractor import BaseExtractor
from neo4j import GraphDatabase
import pandas as pd


def get_nodes_labels_and_properties(tx):
    query = """
        MATCH (n)
        RETURN DISTINCT id(n) AS node_id, labels(n) AS labels, properties(n) AS props
        """
    result = tx.run(query)
    return [(record["node_id"], record["labels"], record["props"]) for record in result]


class Neo4jExtractor(BaseExtractor):
    def __init__(self, config):
        super().__init__(config)
        self.node_data = None

    def extract_node_data(self):
        driver = GraphDatabase.driver(self.config.get("neo4j.uri"),
                                      auth=(self.config.get("neo4j.username"), self.config.get("neo4j.password")))

        with driver.session() as session:
            self.node_data = session.read_transaction(get_nodes_labels_and_properties)

        driver.close()

        node_ids = list({str(nl[0]) for nl in self.node_data})
        labels = sorted({label for _, labels, _ in self.node_data for label in labels})
        properties = sorted({key for _, _, props in self.node_data for key in props.keys()})

        columns = []
        if self.config.get("node_type_extraction") == "label_based":
            columns = labels
        if self.config.get("node_type_extraction") == "property_based":
            columns = properties
        if self.config.get("node_type_extraction") == "label_property_based":
            columns = labels + properties

        df = pd.DataFrame(False, index=node_ids, columns=columns)
        self._fill_node_dataframe_context(df, self.node_data)

        return df

    def _fill_node_dataframe_context(self, df, node_data):

        for node_id, labels, props in node_data:
            node_id_str = str(node_id)
            if self.config.get("node_type_extraction") == "label_based" or self.config.get(
                    "node_type_extraction") == "label_property_based":
                for label in labels:
                    df.at[node_id_str, label] = True
            if self.config.get("node_type_extraction") == "property_based" or self.config.get(
                    "node_type_extraction") == "label_property_based":
                for key, value in props.items():
                    df.at[node_id_str, key] = True
