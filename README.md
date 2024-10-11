
# FCA Schema Discovery  
  
## Overview  

## Usage
After cloning the repository, I would recommend to run the program in a virtual environment. It is written in python 3.10, but any version >= 3.10 should also work. Run `pip install -r requirements.txt`to download the necessary packages. At the current state of the tool I would recommend to just run`main.py`. I have planned that in the end it will be usable as command-line tool (it is also implemented but regarding the huge number of config parameters, I prefer running with `main.py`). The parameters can be found in the `config.json`. Here in the `README.md` you can find a specification explaining the configuration parameters. Since you will use the graph generator and not a real graph database, make sure that the parameter `graph_generator` is `true`.
In the `schema_examples` folder you can find a couple of schemas I have tried out so far. Feel free to add schemas to this list (otherwise please dont upload any changes or make sure you fork it before you do). You have to put the file path of the schema you want to be generated into the`graph_generator_schema_path` field in the configuration. Regarding the graph generator, please be aware that the schema that can be parsed and the graphs that get generated are limited. The schema parser can only parse schemas for the following fields, labels and optional labels, properties and optional properties, and supertype defitions with `&`. This is due to the  fact, that the tool cant extract any other information (If we do the schema parsing, I might write a better parser if needed). The graph generator creates for every node and edge type between 10k and 100k entities according to their type definitions.  After the schema extraction, the graph will be validated against the schema. You can find all the end results in the `results` folder. `schema.txt` contains the final schema, `nodes_and_edges.json` shows which node and edges belong to which type, if any node/edge did not conform to the schema that was created, than there is a file called `invalid_elements`, which contains the nodes/edges that are invalid under the schema. You can also find a visualization of the concept lattices in this folder. Also the validator only validates the limited version of PG-Schema, meaning the one that are created by the extractor (again, if we do the schema merging, then I might have to extend the validation process).

## Configuration  
  
The configuration file allows you to control how schemas are extracted. Below is a list of the parameters:  
  
| Parameter                     | Type    | Description                                                         |
|-------------------------------|---------|---------------------------------------------------------------------|
| `data_source`                  | String  | Data source type. The current implementation allows for a `neo4j` data source. It is easy to extend the tool with a new data source type.                               |
| `neo4j.uri`                    | String  | URI for connecting to the Neo4j instance.                           |
| `neo4j.username`               | String  | Username for the Neo4j connection.                                  |
| `neo4j.password`               | String  | Password for the Neo4j connection.                                  |
| `graph_generator`              | Boolean | If true, the graph generator creates a graph based on the schema given in the `graph_generator_schema_path` field and the schema extraction will be executed on this graph and not on the graph given in the `data_source` field.                            |
| `graph_generator_schema_path`  | String  | File path for the schema used by the graph generator.               |
| `node_type_extraction`         | String  | Approach for extracting node types. Can only be `label_based`, `property_based` or `label_property_based.`
| `edge_type_extraction`         | String  | Approach for extracting edge types. Can only be `label_based`, `property_based` or `label_property_based.`
| `out_dir`                      | String  | Output directory for the generated results.                         |
| `optional_labels`              | Boolean | Allows optional labels for node and edge types.                              |
| `optional_properties`          | Boolean | Allows optional properties for node and edge types.                 |
| `label_outlier_threshold`      | Float   | Threshold for label outlier detection. If the number of nodes/edges that have a label is smaller than `label_outlier_threshold`, then the label will be ignored and will not appear in the result schema.                            |
| `property_outlier_threshold`   | Float   | Threshold for property outlier detection. If the number of nodes/edges that have a label is smaller than `property_outlier_threshold`, then the property will be ignored and will not appear in the result schema.                            |
| `endpoint_outlier_threshold`   | Float   | Threshold for endpoint outlier detection. If the number of endpoints of an edge having a certain node type is smaller than `endpoint_outlier_threshold`. Then the this node type will not appear as endpoint node type in the result schema.                         |
| `merge_threshold`              | Float   | Threshold for merging similar types (e.g., 0.8).                    |
| `graph_type_name`              | String  | Name of the graph type to be generated.                             |
| `graph_type_mode`              | String  | Graph type mode. Either `LOOSE` or `STRICT`.                         |
| `open_labels`                  | Boolean | Result schema will have either all open or closed types regarding their labels, depending on this value.
| `open_properties`              | Boolean | Result schema will have either all open or closed types regarding their properties, depending on this value.
| `abstract_type_threshold`      | Float   | Threshold for classifying a type as abstract (e.g., 0.8).           |
| `remove_inherited_features`    | Boolean | Whether to remove inherited features from subtypes.                 |
| `abstract_type_lookup`         | Boolean | Enables or disables abstract type lookup.                           |
| `max_node_types`               | Integer | Maximum number of node types allowed in the result schema.                               |
| `max_edge_types`               | Integer | Maximum number of edge types allowed in the result schema.                               |                              |
| `max_types`                    | Boolean | Whether to reduce the graph to a maximum number of node/edge types or not.                         |
| `validate_graph`               | Boolean | Enables validation of the generated graph against the schema.       |

## Schema Examples  
A collection of schema examples used for evaluating. For each example the best approach and result is listed.  
### schema1.pgs  
One level inheritane with optional properties and labels.  Graphtype attributes like "LOOSE"/"STRICT" or "OPEN"/"CLOSED" are default values of the config and not based on the graph the schema is extracted from.
    
**CREATE GRAPH TYPE ExampleGraphType {    
  (PersonType: Person {name STRING, OPTIONAL birthday DATE}),    
  (CustomerType: PersonType & Customer & Gender? {c_id INTEGER}),    
  (AccountType: Account {acct_id INTEGER}),    
  (:PersonType|CustomerType)-[OwnsAccountType: owns & posses {since DATE, OPTIONAL amount FLOAT}]->(:AccountType)    
}**  
#### Result Schema  
**CREATE GRAPH TYPE GraphTypeExampleType LOOSE {    
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
}** This result was achieved with label-property-based approach with max_type for nodes 3. Here the types one its own  are correctly identified but the inheritance relation is lost because of the merging process.  
### schema2.pgs  
A Basic Schema to check if basic requirements can be met.  
**CREATE GRAPH TYPE BasicGraphType {    
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
**CREATE GRAPH TYPE InheritanceGraphType {    
  (PersonType: Person {name STRING, age INTEGER}),    
  (WorkerType: Worker {craft STRING}),    
  (UserType: PersonType & Customer? {username STRING}),    
  (EmployeeType: PersonType & WorkerType {employee_id INTEGER, salary FLOAT}),    
  (ManagerType: EmployeeType {manager_level STRING}),    
  (:EmployeeType)-[Manages: supervises]->(:ManagerType)    
}**
 #### Result Schema  
 **CREATE GRAPH TYPE GraphTypeExample LOOSE {    
(NodeType1: Person OPEN {age INTEGER, name STRING, OPEN}),    
(NodeType2: Worker OPEN {craft STRING, OPEN}),    
(NodeType3: NodeType1 & NodeType2 OPEN {employee_id INTEGER, salary FLOAT, OPTIONAL   manager_level STRING, OPEN}),    
(NodeType5: NodeType1 OPEN {username STRING, OPEN}),    
(NodeType6: NodeType5 & Customer OPEN),    
(:NodeType3) - [EdgeType0 : supervises ] -> (:NodeType3)    
}**
This result was achieved by the label-property-based approach with max types 5 for nodes and 1 for edges. In general the structure of the original schema was extracted but the Usertype was split up into to types, which can be resolved by setting the max types of nodes to 4. But the Managertype is not recognized on its own but merged into the Employeetype (manager_level STRING becomes an optinal property for Emplyeetype). If max type for nodes is set to 4 the result looks as follows:
**CREATE GRAPH TYPE GraphTypeExample LOOSE {    
(NodeType1: Person OPEN {age INTEGER, name STRING, OPEN}),   
(NodeType2: Worker OPEN {craft STRING, OPEN}),   
(NodeType3: NodeType2 & NodeType1 OPEN {salary FLOAT, employee_id INTEGER, OPTIONAL manager_level STRING, OPEN}),   
(NodeType5: NodeType1 & Customer? OPEN {username STRING, OPEN}),   
(:NodeType3) - [EdgeType0 : supervises ] -> (:NodeType3)   
}**
### schema4.pgs
Schema with more complex relationship and node type are defined by properties and not labels.

**CREATE GRAPH TYPE ComplexRelationshipGraphType {  
  (PersonType: {name STRING}),  
  (CustomerType: PersonType {customer_id INTEGER}),  
  (ProductType: {p_id INTEGER, category STRING}),  
  (OrderType: {order_id INTEGER, date DATE}),  
  (:CustomerType)-[PlacesOrderType: places]->(:OrderType),  
  (:OrderType)-[ContainsProductType: contains]->(:ProductType)  
}**
#### Result Schema
**CREATE GRAPH TYPE GraphTypeExample LOOSE {   
(NodeType1:  OPEN {category STRING, p_id INTEGER, OPEN}),   
(NodeType2:  OPEN {name STRING, OPEN}),   
(NodeType3:  OPEN {date DATE, order_id INTEGER, OPEN}),   
(NodeType4: NodeType2 OPEN {customer_id INTEGER, OPEN}),   
(:NodeType3) - [EdgeType1 : contains ] -> (:NodeType1),   
(:NodeType4) - [EdgeType2 : places ] -> (:NodeType3)   
}**
The extraction with property-based approach for nodes and label-based approach for edges, creates the schema exactly like the original.

### schema5.pgs
Cyclic Relationship schema. The result was exactly the same.
**CREATE GRAPH TYPE CyclicGraphType {  
  (UserType: Person {username STRING}),   
  (:UserType)-[Follows: follows]->(:UserType),   
  (:UserType)-[Blocks: blocks]->(:UserType)   
}**
### schema6.pgs
Disconnected Graph, to see if the structure without inheritance can also be extracted correctly. The result was exactly the same.
**CREATE GRAPH TYPE DisconnectedGraphType {  
  (UserType: User {username STRING}),  
  (PostType: Post {content STRING}),  
  (:UserType)-[LikesType: likes]->(:PostType),  
  (CityType: City {name STRING, population INTEGER}),  
  (CountryType: Country {name STRING}),  
  (:CityType)-[LocatedInType: located_in]->(:CountryType)  
}**
### schema7.pgs
A quite simple but big graph to check if the number of types in the schema matter.
**CREATE GRAPH TYPE BigUniversityGraphType {  
  (PersonType: Person {name STRING, birthdate DATE}),  
  (StudentType: PersonType & Student {student_id INTEGER}),  
  (ProfessorType: PersonType & Professor {professor_id INTEGER, department STRING}),  
  (StaffType: PersonType & Staff {staff_id INTEGER, role STRING}),  
  (ResearcherType: ProfessorType & StaffType & Researcher {research_area STRING, lab STRING}),  
  (CourseType: Course {course_id STRING, credits INTEGER}),  
  (DepartmentType: Department {dept_name STRING, OPTIONAL location STRING}),  
  (ClubType: Club {club_name STRING, OPTIONAL founded DATE}),  
  (:StudentType)-[EnrolledInType: enrolled_in {semester STRING}]->(:CourseType),  
  (:ProfessorType)-[TeachesType: teaches {semester STRING, OPTIONAL is_online BOOLEAN}]->(:CourseType),  
  (:StaffType)-[ManagesType: manages {since DATE}]->(:DepartmentType),  
  (:ResearcherType)-[CollaboratesWithType: collaborates_with {project_name STRING}]->(:ResearcherType),  
  (:ProfessorType)-[AdvisorOfType: advisor_of]->(:StudentType),  
  (:StudentType)-[MemberOfType: member_of {since DATE}]->(:ClubType),  
  (:ProfessorType)-[MemberOfType: member_of {since DATE}]->(:ClubType),  
  (:StaffType)-[WorksAtType: works_at]->(:DepartmentType)  
}**
#### Result Schema
**CREATE GRAPH TYPE GraphTypeExample LOOSE {   
(NodeType1: Person OPEN {name STRING, birthdate DATE, OPEN}),  
(NodeType2: NodeType1 & Professor OPEN {professor_id INTEGER, department STRING, OPEN}),  
(NodeType3: NodeType1 & Staff OPEN {staff_id INTEGER, role STRING, OPEN}),  
(NodeType4: NodeType1 & Student OPEN {student_id INTEGER, OPEN}),  
(NodeType5: Course OPEN {course_id STRING, credits INTEGER, OPEN}),  
(NodeType6: Club OPEN {club_name STRING, OPTIONAL founded DATE, OPEN}),  
(NodeType7: NodeType2 & NodeType3 & Researcher OPEN {research_area STRING, lab STRING, OPEN}),  
(NodeType8: Department OPEN {dept_name STRING, OPTIONAL location STRING, OPEN}),  
(:NodeType2) - [EdgeType1 : advisor_of ] -> (:NodeType4),  
(:NodeType2) - [EdgeType2 : member_of {since DATE, OPEN}] -> (:NodeType6),  
(:NodeType3) - [EdgeType3 : works_at ] -> (:NodeType8),  
(:NodeType2) - [EdgeType4 : teaches {semester STRING, OPTIONAL is_online INTEGER, OPEN}] -> (:NodeType5),  
(:NodeType4) - [EdgeType5 : enrolled_in {semester STRING, OPEN}] -> (:NodeType5),  
(:NodeType3) - [EdgeType6 : manages {since DATE, OPEN}] -> (:NodeType8),  
(:NodeType7) - [EdgeType7 : collaborates_with {project_name STRING, OPEN}] -> (:NodeType7)  
}**
The result achieved with label-based approach is exactly the same.

### schema8.pgs
A schema that shows the potential to introduce an abstract type. Both node type definitions share properties, that could be gathered into an abstract type.
**CREATE GRAPH TYPE AbstractTypeGraphType {   
  (StudentType: Student {student_id INTEGER, major STRING, name STRING, birthdate DATE, email STRING, phone_number STRING}),   
  (ProfessorType: Professor {professor_id INTEGER, department STRING, name STRING, birthdate DATE, email STRING, phone_number STRING})   
}**
#### Result Schema
**CREATE GRAPH TYPE GraphTypeExample LOOSE {    
(NodeType1: AbstractNodeTypeNodeType2+NodeType1 & Professor OPEN {professor_id INTEGER,  department STRING, OPEN}),   
(NodeType2: AbstractNodeTypeNodeType2+NodeType1 & Student OPEN {student_id INTEGER, major STRING, OPEN}),   
ABSTRACT (AbstractNodeTypeNodeType2+NodeType1 OPEN {name STRING, birthdate DATE, email STRING, phone_number STRING, OPEN})  
}**
The extraction process recognizes the similarities and gathers them together into an abstract type.

