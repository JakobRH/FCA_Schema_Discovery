# FCA Schema Discovery

## Overview


## Schema Examples
A collection of schema examples used for evaluating. For each example the best config setting and result is listed.
### schema1.pgs
One level inheritane with optional properties and labels.
  
**CREATE GRAPH TYPE ExampleGraphType {  
  (PersonType: Person {name STRING, OPTIONAL birthday DATE}),  
  (CustomerType: PersonType & Customer & Gender? {c_id INTEGER}),  
  (AccountType: Account {acct_id INTEGER}),  
  (:PersonType|CustomerType)-[OwnsAccountType: owns & posses {since DATE, OPTIONAL amount FLOAT}]->(:AccountType)  
}**
#### Result Schema
**CREATE GRAPH TYPE GraphTypeExample LOOSE {  
(NodeType1: Person OPEN {name STRING, OPTIONAL birthday DATE, OPEN}),  
(NodeType2: NodeType1 & Customer & Gender? OPEN {c_id INTEGER, OPEN}),  
(NodeType3: Account OPEN {acct_id INTEGER, OPEN}),  
(:NodeType1) - [EdgeType0 : owns & posses {since DATE, OPTIONAL amount FLOAT, OPEN}] -> (:NodeType3)  
}**    
This result was achieved with label-based approach. Result is the same as original Schema.
**CREATE GRAPH TYPE GraphTypeExample LOOSE {  
(NodeType1: Person OPEN {name STRING, OPTIONAL birthday DATE, OPEN}),  
(NodeType3: Account OPEN {acct_id INTEGER, OPEN}),  
(NodeType6: Customer & Person & Gender? OPEN {c_id INTEGER, name STRING, OPTIONAL birthday DATE, OPEN}),  
(:NodeType1|NodeType6) - [EdgeType0 : owns & posses {since DATE, OPTIONAL amount FLOAT, OPEN}] -> (:NodeType3)  
}**  
This result was achieved with label-property-based approach with max_type for nodes 3. Here the types one its own
are correctly identified but the inheritance relation is lost because of the merging process.
### schema2.pgs
A Basic Schema to check if basic requirements can be met.
**CREATE GRAPH TYPE BasicGraph {  
  (PersonType: Person {name STRING, age INTEGER}),  
  (CustomerType: Item {p_id INTEGER, price FLOAT}),  
  (:PersonType)-[Buys: purchases {quantity INTEGER}]->(:ProductType)  
}**
#### Result Schema
**CREATE GRAPH TYPE GraphTypeExample LOOSE {  
(NodeType1: Item OPEN {p_id INTEGER, price FLOAT, OPEN}),  
(NodeType2: Person OPEN {name STRING, age INTEGER, OPEN}),  
(:NodeType2) - [EdgeType0 : purchases {quantity INTEGER, OPEN}] -> (:NodeType1)  
}**  
The label-based approach extracts the schema exactly the same.

### schema3.pgs
A graph with multiple inheritance over two levels with optional labels.  
**CREATE GRAPH TYPE InheritanceGraph {  
  (PersonType: Person {name STRING, age INTEGER}),  
  (WorkerType: Worker {craft STRING}),  
  (UserType: PersonType & Customer? {username STRING}),  
  (EmployeeType: PersonType & WorkerType {employee_id INTEGER, salary FLOAT}),  
  (ManagerType: EmployeeType {manager_level STRING}),  
  (:EmployeeType)-[Manages: supervises]->(:ManagerType)  
}**  
#### Result Schema
## Configuration

The configuration file allows you to control how schemas are extracted and validated. Below is a list of some key parameters:

| Parameter                  | Type    | Description                                                 |
|----------------------------|---------|-------------------------------------------------------------|
| `data_source`               | String  | Data source type (e.g., `neo4j`).                           |
| `neo4j.uri`                 | String  | URI for connecting to the Neo4j instance.                   |
| `neo4j.username`            | String  | Username for the Neo4j instance.                            |
| `neo4j.password`            | String  | Password for the Neo4j instance.                            |
| `open_labels`               | Boolean | Whether to allow additional labels beyond those in schema.  |
| `open_properties`           | Boolean | Whether to allow additional properties beyond the schema.   |
| `node_type_extraction`      | String  | Approach to extract node types (e.g., `label_based`).       |
| `edge_type_extraction`      | String  | Approach to extract edge types (e.g., `label_based`).       |
| `validate_graph`            | Boolean | Whether to validate the graph against the extracted schema. |