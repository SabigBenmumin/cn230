# from fastapi import FastAPIs

# app = FastAPI()

# @app.get("/")
# def index():
#     return {"message": "Welcome TO FastAPI World"}

from fastapi import FastAPI, UploadFile
from neo4j import GraphDatabase
from pydantic import BaseModel
from typing import List, Union
import pandas as pd

class RelationshipModel (BaseModel):
    name: str
    to_node: str

class NodeModel (BaseModel):
    name: str
    relationships: List[RelationshipModel] = []

class KnowledgeGraph():
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_driver(self):
        return self.driver
    def close(self):
        self.driver.close()
    def get_all_node(self):
        records, summary, keys = self.driver.execute_query(
            "MATCH (n:Node)-[r]->(tn:Node) RETURN n.name, collect([type(r), tn.name]) as relationships", database_ = "neo4j"
        )
        return records, summary, keys
    def get_node_name(self, name):
        records, summary, keys = self.driver.execute_query(
            "MATCH (n:Node {name:$name})-[r]->(tn:Node) RETURN n.name, collect([type(r), tn.name]) as relationships",
            name = name,
            database_ = "neo4j"
        )
        return records, summary, keys

    def create_node(self, node_data:NodeModel):
        summary = self.driver.execute_query(
            "MERGE (:Node {name: $name})",name = node_data.name,database_="neo4j"
        ).summary
        print(f"Node '{node_data.name}' created status: {summary.counters.nodes_created}")

        added_relations = []
        for relation in node_data.relationships:
            success_nodes = self.create_relationship(node_data.name, relation)
            added_relations = success_nodes
        return summary, added_relations

    def create_relationship(self, from_node:str, relation_data:RelationshipModel):
        success_nodes = []
        try:
            records, summary, keys = self.driver.execute_query(
                """
                MATCH (n:Node {name: $name}), (tn:Node {name: $to_node})
                MERGE (n)-[r:""" + relation_data.name + """]->(tn)
                """,
                name = from_node,
                to_node = relation_data.to_node,
                database_ = "neo4j",
            )
        except Exception as e:
            print(e)
            print(f"relation error at {relation_data.name} -> {relation_data.to_node}")
        return success_nodes

neo_graph = KnowledgeGraph("bolt://neo4j:7687", "neo4j", "cn230_admin")
neo_graph.get_driver().verify_connectivity()

app=FastAPI()

@app.get("/")
def index():
    record, summary, key = neo_graph.get_all_node()
    return{"nodes": record}

@app.get("/node/{name}")
def get_node_name(name:str):
    record, summary, keys= neo_graph.get_node_name(name)
    return{"node":record}

@app.post("/add/node")
def create_node(node_data:NodeModel):
    summary, added_nodes = neo_graph.create_node(node_data)
    return{"status": summary.counters.nodes_created}

@app.post("/upload/triple/csv")
async def upload_triple_csv(file:UploadFile):
    df = pd.read_csv(file.file)
    success_node = []
    for idx, row in df.iterrows():
        relation = RelationshipModel(name=row['predicate'], to_node=row['object'])
        node = NodeModel(name=row['subject'], relationships = [relation])
        summary, added_node = neo_graph.create_node(node)
        success_node.append(added_node)
    return {"success_node": success_node}