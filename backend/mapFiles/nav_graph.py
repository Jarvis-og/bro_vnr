import os
import geopandas as gpd
import networkx as nx
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def shp(filename):
    return os.path.join(BASE_DIR, filename)

NODE_ID_COL = "ABC1NODES"
EDGE_ID_COL = "ABC1EDGES"
ROOM_ID_COL = "ABC1ROOMS"

VERTICAL_CONNECTIONS = {
    "STAIRDOWNABC3": {"to_node": "STAIR UP2", "cost": 30.0},
    "STAIR UP2":     {"to_node": "STAIRDOWNABC3", "cost": 30.0},
}

# Load and reproject once
nodes = gpd.read_file(shp("ALLMERGEDNODES.shp"))
edges = gpd.read_file(shp("ALLMERGEDEDGES.shp"))
rooms = gpd.read_file(shp("ALLMERGEDROOMS.shp"))
restricted = gpd.read_file(shp("ALLMERGEDRESTRICTEDAREA.shp"))
corridors = gpd.read_file(shp("ALLMERGEDCORRIDORS.shp"))

# Build graph
G = nx.Graph()
for _, row in nodes.iterrows():
    node_id = str(row[NODE_ID_COL])
    G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))

valid_nodes = set(G.nodes)

for _, row in edges.iterrows():
    u, v = str(row["FROM"]), str(row["TO"])
    if u in valid_nodes and v in valid_nodes:
        G.add_edge(u, v, weight=row.geometry.length, edge_id=str(row[EDGE_ID_COL]))

for u, info in VERTICAL_CONNECTIONS.items():
    v = info["to_node"]
    if u in valid_nodes and v in valid_nodes:
        G.add_edge(u, v, weight=info["cost"], edge_id=f"{u}_{v}_V")

def heuristic(u, v):
    try:
        x1, y1 = G.nodes[u]["pos"]
        x2, y2 = G.nodes[v]["pos"]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    except:
        return float("inf")

def get_map_geojson():
    return {
        "rooms":      json.loads(rooms.to_json()),
        "edges":      json.loads(edges.to_json()),
        "nodes":      json.loads(nodes.to_json()),
        "restricted": json.loads(restricted.to_json()),
        "corridors":  json.loads(corridors.to_json()),
    }