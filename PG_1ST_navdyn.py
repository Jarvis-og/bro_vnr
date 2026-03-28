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


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏢 PG2nd Floor Indoor Navigation Demo")

        # Define the expected names for the geometric ID columns
        self.NODE_ID_COL = "PG1NODES"  
        self.EDGE_ID_COL = "PG1EDGES" 
        self.ROOM_ID_COL = "PG1ROOMS"  # Column name for Room IDs in the rooms shapefile

        # ---------------- Load Data ----------------
        try:
            # Load basic node and edge data
            self.nodes = gpd.read_file("PG_1ST_NODES.shp")
            self.edges = gpd.read_file("PG_1ST_EDGES.shp")
            
            # Load visualization data (Rooms and Restricted Areas)
            self.rooms = gpd.read_file("PG_1ST_ROOMS.shp")
            self.restricted_areas = gpd.read_file("PG_1ST_RESTRICTEDAREA.shp")

        except Exception as e:
            QMessageBox.critical(self, "Data Loading Error", 
                                 f"Could not load shapefiles. Check filenames and path.\nError: {e}")
            sys.exit(1)

        # ---------------- Build Graph ----------------
        self.G = nx.Graph()
        for _, row in self.nodes.iterrows():
            node_id = row[self.NODE_ID_COL]
            self.G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))
        
        self.valid_nodes = set(self.G.nodes)

        for _, row in self.edges.iterrows():
            # NOTE: Assuming columns in PG_2nd_Edges are named "From" and "To"
            u = row["FROM"]
            v = row["TO"]
            length = row.geometry.length
            self.G.add_edge(u, v, weight=length, edge_id=row[self.EDGE_ID_COL])

        # ---------------- Matplotlib Figure ----------------
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # ---------------- GUI Layout ----------------
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(10)

        # Dynamic Start Input Field
        layout.addWidget(QLabel("📍 **Enter Current/Starting Room ID:**"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g., R201, BE")
        self.start_input.setFont(font)
        layout.addWidget(self.start_input)
        
        layout.addWidget(QLabel("🏁 **Enter Destination Room ID:**"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., R205, HOD")
        self.goal_input.setFont(font)
        layout.addWidget(self.goal_input)

        self.nav_button = QPushButton("🚀 Navigate (Find Shortest Path)")
        self.nav_button.clicked.connect(self.run_astar)
        layout.addWidget(self.nav_button)

        # Set the map canvas to take up the majority of the vertical space (Stretch factor 4)
        layout.addWidget(self.canvas, 4) 

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

        # Add title
        self.ax.set_title("PG1st Floor Navigation Map")
        
        # 1. Plot Room Polygons (Floor Plan - Zorder 0)
        self.rooms.plot(
            ax=self.ax, 
            color="#FEFCE8",       # Light Yellow/Cream Fill
            edgecolor="black", 
            linewidth=0.5, 
            aspect=1, 
            zorder=0                
        )
        
        # 2. Plot Restricted Area Polygons (Zorder 0.5)
        self.restricted_areas.plot(
            ax=self.ax,
            color="#FFCCCC",       # Light Red Fill
            edgecolor="darkred",
            hatch='///',           # Add diagonal hatch pattern
            linewidth=1.0,
            alpha=0.6,
            aspect=1,
            zorder=0.5
        )

        # 3. Plot Edges (Hallways - Zorder 1)
        self.edges.plot(ax=self.ax, color="lightgray", linewidth=1, aspect=1, zorder=1)
        
        # 4. *** RE-ADDED: Room ID Labels ***
        for idx, row in self.rooms.iterrows():
            # Calculate the centroid (center) of the room polygon
            x, y = row.geometry.centroid.x, row.geometry.centroid.y
            label = row[self.ROOM_ID_COL]
            self.ax.text(x, y, label, 
                         fontsize=7, 
                         color='darkgreen', 
                         ha='center', 
                         va='center', 
                         zorder=7, 
                         bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))

        # 5. Plot Nodes (Junctions/Points of Interest - Zorder 2)
        self.nodes.plot(ax=self.ax, color="lightblue", markersize=40, aspect=1, zorder=2)
        
        # 6. Highlight path if available (Highest Layers)
        if path:
            # Highlight nodes (Zorder 4)
            path_nodes = self.nodes[self.nodes[self.NODE_ID_COL].isin(path)]
            path_nodes.plot(ax=self.ax, color="red", markersize=80, aspect=1, zorder=4)

            # Highlight edges (Zorder 3)
            path_edges = list(zip(path[:-1], path[1:]))
            for (u, v) in path_edges:
                edge_geom = self.edges[
                    ((self.edges["FROM"] == u) & (self.edges["TO"] == v)) |
                    ((self.edges["FROM"] == v) & (self.edges["TO"] == u))
                ]
                if not edge_geom.empty:
                    edge_geom.plot(ax=self.ax, color="red", linewidth=3.0, aspect=1, zorder=3)
        
        # Ensure valid aspect ratio
        self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.autoscale(enable=True)
        
        self.canvas.draw()

    def run_astar(self):
        """Run A* and update map based on dynamic user input"""
        start = self.start_input.text().strip()
        goal = self.goal_input.text().strip()

        if not start or not goal:
            QMessageBox.warning(self, "Input Error", "Please enter both a **starting** and a **destination** Room ID.")
            return

        if start == goal:
            QMessageBox.information(self, "Same Location", "You are already at your destination!")
            self.plot_map()
            return
            
        if start not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Node", f"Starting ID **{start}** not found in map nodes.")
            return

        if goal not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Node", f"Destination ID **{goal}** not found in map nodes.")
            return

        try:
            path = nx.astar_path(self.G, start, goal, heuristic=self.heuristic, weight="weight")
            distance = round(nx.path_weight(self.G, path, weight="weight"), 2)
            
            QMessageBox.information(
                self, 
                "Path Found", 
                f"**Start:** {start}\n**Destination:** {goal}\n**Total Distance:** {distance} units\n\n**Path:**\n{' → '.join(path)}"
            )
            self.plot_map(path)
            
        except nx.NetworkXNoPath:
            QMessageBox.warning(self, "No Path", f"No path found from **{start}** to **{goal}**.")
        except Exception as e:
            QMessageBox.critical(self, "Navigation Error", f"An unexpected error occurred during pathfinding: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())