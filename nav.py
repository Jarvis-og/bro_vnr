import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt


nodes = gpd.read_file("PG_2nd_Nodes.shp")
edges = gpd.read_file("PG_2nd_Edges.shp")


G = nx.Graph()

# Add nodes with coordinates
for idx, row in nodes.iterrows():
    node_id = row["Node ID"]  # field name in node shapefile
    G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))
    valid_nodes= set(G.nodes)

# Add edges (with geometry length as weight)
for idx, row in edges.iterrows():
    
    try:
        u = row["From"] 
        v = row["To"]   
    except KeyError:
        raise ValueError("Your edge shapefile must have start & end node IDs (e.g. From, To).")

    length = row.geometry.length
    G.add_edge(u, v, weight=length, edge_id=row["Edge ID"])


def heuristic(u, v):
    (x1, y1) = G.nodes[u]["pos"]
    (x2, y2) = G.nodes[v]["pos"]
    return ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5

while True:

 start = "BE"   
 goal = (input("Enter The Destination Room Number: ")).strip()
 
 if goal.lower()=="exit":
     print("Exiting Navigation....")
     break

 elif goal not in valid_nodes:
     print ("Room Number Invalid!")
     continue


 
 path = nx.astar_path(G, start, goal, heuristic=heuristic, weight="weight")
 
 print("A* shortest path:", path)
 
 
 pos = nx.get_node_attributes(G, "pos")
 
 plt.figure(figsize=(10, 8))
 nx.draw(G, pos, with_labels=True, node_size=200, node_color="lightblue")
 nx.draw_networkx_edges(G, pos, width=1)
 nx.draw_networkx_nodes(G, pos, nodelist=path, node_color="red")  # highlight path
 plt.title(f"A* Path from {start} to {goal}")
 plt.show()
