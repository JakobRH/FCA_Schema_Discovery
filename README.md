
# FCA Schema Discovery  
This repository was created in the course of a master thesis. It includes a fully automatic method for schema discovery in property graphs. The uses Formal Concept Analysis (FCA) to build a formal concept lattice, which serves as basis for a schema. 


## Overview  

## Usage
After cloning the repository, I would recommend to run the program in a virtual environment. It is written in python 3.10, but any version >= 3.10 should also work. Run `pip install -r requirements.txt`to download the necessary packages. At the current state of the tool I would recommend to just run`main.py`. I have planned that in the end it will be usable as command-line tool (it is also implemented but regarding the huge number of config parameters, I prefer running with `main.py`). The parameters can be found in the `config.json`. Here in the `README.md` you can find a specification explaining the configuration parameters. Since you will use the graph generator and not a real graph database, make sure that the parameter `graph_generator` is `true`.
In the `schema_examples` folder you can find a couple of schemas I have tried out so far. Feel free to add schemas to this list (otherwise please dont upload any changes or make sure you fork it before you do). You have to put the file path of the schema you want to be generated into the`graph_generator_schema_path` field in the configuration. Regarding the graph generator, please be aware that the schema that can be parsed and the graphs that get generated are limited. The schema parser can only parse schemas for the following fields, labels and optional labels, properties and optional properties, and supertype defitions with `&`. This is due to the  fact, that the tool cant extract any other information (If we do the schema parsing, I might write a better parser if needed). The graph generator creates for every node and edge type between 10k and 100k entities according to their type definitions.  After the schema extraction, the graph will be validated against the schema. You can find all the end results in the `results` folder. `schema.txt` contains the final schema, `nodes_and_edges.json` shows which node and edges belong to which type, if any node/edge did not conform to the schema that was created, than there is a file called `invalid_elements`, which contains the nodes/edges that are invalid under the schema. You can also find a visualization of the concept lattices in this folder. Also the validator only validates the limited version of PG-Schema, meaning the one that are created by the extractor (again, if we do the schema merging, then I might have to extend the validation process).

## Configuration  
  
The configuration file allows you to control how schemas are extracted. Below is a list of the parameters:  
  
| **Parameter** | **Type** | **Description** | **Default Value** |
|--------------|---------|----------------|----------------|
| `data_source` | `str` | Specifies the source of the data. Currently, only `neo4j` is supported. | `neo4j` |
| `neo4j.uri` | `str` | URI for connecting to the Neo4j database. | `bolt://localhost:7687` |
| `neo4j.username` | `str` | Username for authentication. | `neo4j` |
| `neo4j.password` | `str` | Password for authentication. | `password` |
| `graph_generator` | `bool` | Enables or disables graph generation mode. | `false` |
| `graph_generator_schema_path` | `str` | Path to the schema file used for graph generation. | `None` |
| `graph_generator_max_entities` | `int` | Maximum number of entities to generate per type. | `100000` |
| `graph_generator_min_entities` | `int` | Minimum number of entities to generate per type. | `10000` |
| `node_type_extraction` | `str` | Method for extracting node types. | `label_based` |
| `edge_type_extraction` | `str` | Method for extracting edge types. | `label_based` |
| `optional_labels` | `bool` | Includes optional labels in the schema. | `true` |
| `optional_properties` | `bool` | Includes optional properties in the schema. | `true` |
| `type_outlier_threshold` | `int` | Minimum number of nodes/edges required for a type to be valid. | `5` |
| `label_outlier_threshold` | `int` | Minimum number of elements containing a label for validity. | `5` |
| `property_outlier_threshold` | `int` | Minimum number of elements containing a property for validity. | `5` |
| `endpoint_outlier_threshold` | `int` | Minimum number of edges involving a source/target node type for validity. | `5` |
| `merge_threshold` | `float` | Similarity threshold for merging types. | `0.6` |
| `remove_empty_types` | `bool` | Removes types with no nodes/edges assigned. | `true` |
| `max_node_types` | `int` | Maximum number of node types in the schema. | `0` |
| `max_edge_types` | `int` | Maximum number of edge types in the schema. | `0` |
| `max_types` | `bool` | Enables type merging to conform to max allowed types. | `false` |
| `abstract_type_threshold` | `float` | Threshold for creating abstract types from shared attributes. | `0.6` |
| `abstract_type_lookup` | `bool` | Enables lookup for abstract types. | `false` |
| `graph_type_name` | `str` | Name of the graph type. | `ResultGraphType` |
| `out_dir` | `str` | Directory to save results. | `None` |
| `validate_graph` | `bool` | Enables graph validation against schema. | `true` |
| `open_labels` | `bool` | Permits labels not defined in the schema. | `false` |
| `open_properties` | `bool` | Permits properties not defined in the schema. | `false` |
| `merge_schema` | `bool` | Enables schema merging. | `false` |
| `schema_to_merge_path` | `str` | Path to schema file for merging. | `None` |
| `schema_merge_threshold` | `float` | Similarity threshold for merging entities. | `0.5` |

