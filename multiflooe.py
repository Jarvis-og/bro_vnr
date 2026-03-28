import sys
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QMessageBox,
)
from PyQt5.QtGui import QFont
import numpy as np 


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏢 Multi-Floor Indoor Navigation")

        self.resize(1000,800)
        

        # Define vertical connections and their traversal cost (weight)
        self.VERTICAL_CONNECTIONS = {
            # Connection 1: Stair Down Point (PG2 node to PG1 node)
            #"SD": {"to_node": "STAIRUP1", "cost": 30.0},
            
            # Connection 2: Stair Up Point
            #"STAIRUP1": {"to_node": "SD", "cost": 30.0},
        }
        
        # Define the expected names for the geometric ID columns
        self.NODE_ID_COL = "PG1NODES"    
        self.EDGE_ID_COL = "PG1EDGES" 
        self.ROOM_ID_COL = "PG1ROOMS"  # Column name for Room IDs in the rooms shapefile
        # No ID column needed for restricted areas, just the geometry

        # ---------------- Load Data from Merged Shapefiles ----------------
        try:
            # Load the single merged node file 
            self.nodes = gpd.read_file("NODES_Merged.shp")

            # Load the single merged edge file 
            self.edges = gpd.read_file("MERGEDEDGES.shp")
            
            # Load the single merged room file
            self.rooms = gpd.read_file("MERGEDROOMSALL.shp")
            
            # *** NEW: Load the single merged restricted area file ***
            self.restricted_areas = gpd.read_file("MERGEDRESTRICTEDAREAALL.shp")
            
        except Exception as e:
            QMessageBox.critical(self, "Data Loading Error", 
                                 f"Could not load necessary files (NODES, EDGES, ROOMS, or RESTRICTED). Check filenames and directory.\nError: {e}")
            sys.exit(1)

        # ---------------- Build Graph (Single Unified Graph G) ----------------
        self.G = nx.Graph()
        
        # 1. Add ALL nodes 
        for _, row in self.nodes.iterrows():
            node_id = str(row[self.NODE_ID_COL])
            self.G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))
        
        self.valid_nodes = set(self.G.nodes)

        # 2. Add ALL horizontal edges
        for _, row in self.edges.iterrows():
            u = str(row["FROM"])
            v = str(row["TO"])
            edge_id = str(row[self.EDGE_ID_COL])
            
            if u in self.valid_nodes and v in self.valid_nodes:
                length = row.geometry.length 
                self.G.add_edge(u, v, weight=length, edge_id=edge_id)
            else:
                print(f"Warning: Edge ({u} to {v}) skipped due to missing node(s).")
        
        # 3. Add VERTICAL edges manually (connecting the floors)
        for u, connection_info in self.VERTICAL_CONNECTIONS.items():
            v = connection_info["to_node"]
            cost = connection_info["cost"]
            
            if u in self.valid_nodes and v in self.valid_nodes:
                self.G.add_edge(u, v, weight=cost, edge_id=f"{u}_to_{v}_VERTICAL")
            else:
                QMessageBox.warning(self, "Vertical Connection Error", 
                                    f"Missing node for vertical connection: **{u}** or **{v}**. Check VERTICAL_CONNECTIONS.")
                print(f"Warning: Missing node for vertical connection: {u} or {v}")
                
        # ---------------- Matplotlib Figure ----------------
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # ---------------- GUI Layout ----------------
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(10)
        
        layout.addWidget(QLabel("📍 **Enter Current/Starting Room ID:**"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g., P205 (PG2), P101 (PG1)")
        self.start_input.setFont(font)
        layout.addWidget(self.start_input)

        layout.addWidget(QLabel("🏁 **Enter Destination Room ID:**"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., P110 (PG1), LIFT1")
        self.goal_input.setFont(font)
        layout.addWidget(self.goal_input)

        self.nav_button = QPushButton("🚀 Navigate (Find Shortest Path)")
        self.nav_button.clicked.connect(self.run_astar)
        layout.addWidget(self.nav_button)

        # Set the map canvas to take up the majority of the vertical space (Stretch factor 4)
        layout.addWidget(self.canvas, 20) 

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initial plot
        self.plot_map()

    def heuristic(self, u, v):
        """Euclidean distance heuristic for A*"""
        try:
            (x1, y1) = self.G.nodes[u]["pos"]
            (x2, y2) = self.G.nodes[v]["pos"]
            return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        except KeyError:
            return float('inf')


    def plot_map(self, path=None):
        """Draw shapefile map with optional highlighted path"""
        self.ax.clear()

        # Add side labels (assuming PG1 is on the left, PG2 is on the right)
        if not self.edges.empty:
            x_min, y_min, x_max, y_max = self.edges.total_bounds
            x_mid = (x_min + x_max) / 2
            
            # Label PG1
            #self.ax.text(x_min + (x_mid - x_min) / 2, y_max * 1.02, 
                         #'Floor PG1', fontsize=12, color='darkblue', ha='center')
            
            # Label PG2
            #self.ax.text(x_mid + (x_max - x_mid) / 2, y_max * 1.02, 
                         #'Floor PG2', fontsize=12, color='darkred', ha='center')

        # 1. Plot Room Polygons (The Floor Plan - Bottom Layer)
        self.rooms.plot(
            ax=self.ax, 
            color="#C38EFC",       # Light Yellow/Cream Fill
            edgecolor="black", 
            linewidth=0.5, 
            aspect=1, 
            zorder=0                
        )
        
        # 2. *** NEW: Plot Restricted Area Polygons ***
        # Plotting this layer above the room fill but below edges/nodes
        self.restricted_areas.plot(
            ax=self.ax,
            color="#FFCCCC",       # Light Red Fill
            edgecolor="darkred",
            hatch='///',           # Add diagonal hatch pattern to signify restriction
            linewidth=1.0,
            alpha=0.6,
            aspect=1,
            zorder=0.5
        )

        # 3. Plot Edges (Hallways)
        self.edges.plot(ax=self.ax, color="gray", linewidth=1.0, alpha=0.7, aspect=1, zorder=1)
        
        # 4. Add Room ID Labels for Clarity (on the room centers)
        for idx, row in self.rooms.iterrows():
            x, y = row.geometry.centroid.x, row.geometry.centroid.y
            label = row[self.ROOM_ID_COL]
            self.ax.text(x, y, label, 
                         fontsize=7, 
                         color='darkgreen', 
                         ha='center', 
                         va='center', 
                         zorder=7, 
                         bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))

        # 5. Plot Nodes (Junctions/Points of Interest)
        self.nodes.plot(ax=self.ax, color="lightblue", markersize=40, zorder=2, aspect=1)
        
        # 6. Highlight path if available (Highest Layers)
        if path:
            # Highlight nodes on the path
            path_nodes = self.nodes[self.nodes[self.NODE_ID_COL].isin(path)]
            path_nodes.plot(ax=self.ax, color="red", markersize=80, zorder=4, aspect=1)

            # Highlight edges on the path
            path_edges = list(zip(path[:-1], path[1:]))
            for (u, v) in path_edges:
                # 1. Check if it's a horizontal edge
                edge_geom = self.edges[
                    ((self.edges["FROM"] == u) & (self.edges["TO"] == v)) |
                    ((self.edges["FROM"] == v) & (self.edges["TO"] == u))
                ]
                
                # 2. Check if it's a vertical connection
                is_vertical = any((u == n1 and v == n2["to_node"]) or (v == n1 and u == n2["to_node"])
                                  for n1, n2 in self.VERTICAL_CONNECTIONS.items())

                if not edge_geom.empty:
                    # Draw horizontal edge (GeoPandas plot call)
                    edge_geom.plot(ax=self.ax, color="red", linewidth=3.0, zorder=3, aspect=1)
                elif is_vertical:
                    # Draw vertical connection manually
                    pos_u = self.G.nodes[u]["pos"]
                    pos_v = self.G.nodes[v]["pos"]
                    
                    # Draw a distinct orange dashed line for the floor change
                    self.ax.plot([pos_u[0], pos_v[0]], [pos_u[1], pos_v[1]], 
                                 color='darkorange', linewidth=4.0, linestyle='--', marker='o', zorder=5,
                                 label="Floor Change")

        # Set the final, explicit planar aspect ratio on the Matplotlib axes.
        self.ax.set_aspect("equal", adjustable="datalim") 
        
        self.ax.autoscale(enable=True)
        self.ax.set_title("Unified Multi-Floor Map")
        
        self.canvas.draw()

    def run_astar(self):
        """Run A* and update map based on user input for multi-floor navigation"""
        start = self.start_input.text().strip().upper()  
        goal = self.goal_input.text().strip().upper()    

        # 1. Validation Checks
        if not start or not goal:
            QMessageBox.warning(self, "Input Error", "Please enter both a **starting** and a **destination** Room ID.")
            return

        if start == goal:
            QMessageBox.information(self, "Same Location", "You are already at your destination!")
            self.plot_map()
            return

        if start not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Node", f"Starting ID **{start}** not found in the unified map nodes.")
            return

        if goal not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Node", f"Destination ID **{goal}** not found in the unified map nodes.")
            return
            
        # 2. Run A* Algorithm on the unified graph
        try:
            path = nx.astar_path(self.G, start, goal, heuristic=self.heuristic, weight="weight")
            
            # 3. Update GUI
            path_str = ' → '.join(path)
            distance = round(nx.path_weight(self.G, path, weight="weight"), 2)
            
            QMessageBox.information(
                self, 
                "Path Found", 
                f"**Start:** {start}\n**Destination:** {goal}\n**Total Cost/Distance:** {distance} units\n\n**Path:**\n{path_str}"
            )
            self.plot_map(path)
            
        except nx.NetworkXNoPath:
            QMessageBox.warning(self, "No Path", f"No path found from **{start}** to **{goal}**. Check connections!")
        except Exception as e:
            QMessageBox.critical(self, "Navigation Error", f"An unexpected error occurred during pathfinding: {e}")


if __name__ == "__main__":
    import logging
    logging.getLogger('matplotlib').setLevel(logging.ERROR) 

    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())