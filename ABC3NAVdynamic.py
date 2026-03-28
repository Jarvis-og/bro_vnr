import sys
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd # pandas is often needed internally by geopandas, so good to import
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QMessageBox,
)
from PyQt5.QtGui import QFont 

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏢 Dynamic Indoor Navigation GUI (ABC 3rd Floor)")

        # Define the expected names for ID columns
        self.NODE_ID_COL = "ABC3NODES"  
        self.EDGE_ID_COL = "ABC3EDGES"
        self.ROOM_ID_COL = "ABC3ROOMS"  # **ASSUMED COLUMN NAME for room labels**

        # ---------------- Load Data ----------------
        try:
            # 1. Core data for graph
            self.nodes = gpd.read_file("ABC_3RD_NODES.shp")
            self.edges = gpd.read_file("ABC_3RD_EDGES.shp")
            
            # 2. Visualization data
            self.rooms = gpd.read_file("ABC_3RD_ROOMS.shp")
            self.restricted_areas = gpd.read_file("ABC_3RD_RESTRICTEDAREA.shp")
            
        except Exception as e:
            QMessageBox.critical(self, "Data Error", 
                                 f"Could not load shapefiles. Ensure ABC_3RD_*.shp files exist.\nError: {e}")
            sys.exit(1)

        # Build graph
        self.G = nx.Graph()
        for _, row in self.nodes.iterrows():
            node_id = row[self.NODE_ID_COL]
            # Ensure node_id is handled as a string for consistency
            self.G.add_node(str(node_id), pos=(row.geometry.x, row.geometry.y)) 
        self.valid_nodes = set(self.G.nodes)

        for _, row in self.edges.iterrows():
            u = str(row["FROM"])
            v = str(row["TO"])
            
            if u in self.valid_nodes and v in self.valid_nodes:
                length = row.geometry.length
                self.G.add_edge(u, v, weight=length, edge_id=row[self.EDGE_ID_COL])
            else:
                pass 

        # ---------------- Matplotlib Figure ----------------
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # ---------------- GUI Layout ----------------
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(10)
        
        # 1. Start Room Input
        layout.addWidget(QLabel("📍 **Enter Current/Starting Room Number:**"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g., HOD, L101, etc.")
        self.start_input.setFont(font)
        layout.addWidget(self.start_input)

        # 2. Destination Room Input
        layout.addWidget(QLabel("🏁 **Enter Destination Room Number:**"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., L205, LAB, etc.")
        self.goal_input.setFont(font)
        layout.addWidget(self.goal_input)

        # 3. Navigation Button
        self.nav_button = QPushButton("🚀 Navigate (Find Shortest Path)")
        self.nav_button.clicked.connect(self.run_astar)
        layout.addWidget(self.nav_button)

        # 4. Map Canvas (Prioritizing size with stretch factor 4)
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
            # Should not happen if graph is built correctly
            return float('inf') 

    def plot_map(self, path=None):
        """Draw shapefile map with optional highlighted path"""
        self.ax.clear()

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
            hatch='///',           # Diagonal hatch pattern
            linewidth=1.0,
            alpha=0.6,
            aspect=1,
            zorder=0.5
        )

        # 3. Plot Edges (Hallways - Zorder 1)
        self.edges.plot(ax=self.ax, color="lightgray", linewidth=1, aspect=1, zorder=1)
        
        # 4. *** PLOT ROOM LABELS ***
        for idx, row in self.rooms.iterrows():
            # Calculate the centroid (center) of the room polygon
            x, y = row.geometry.centroid.x, row.geometry.centroid.y
            label = str(row[self.ROOM_ID_COL]) # Use the assumed column name
            self.ax.text(x, y, label, 
                         fontsize=7, 
                         color='darkgreen', 
                         ha='center', 
                         va='center', 
                         zorder=7, 
                         bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))

        # 5. Plot Nodes (Junctions/Points of Interest - Zorder 2)
        self.nodes.plot(ax=self.ax, color="lightblue", markersize=40, aspect=1, zorder=2)

        # 6. Highlight path if available
        if path:
            # Highlight nodes (Zorder 4)
            path_nodes = self.nodes[self.nodes[self.NODE_ID_COL].isin(path)]
            path_nodes.plot(ax=self.ax, color="red", markersize=80, aspect=1, zorder=4)

            # Highlight edges (Zorder 3)
            path_edges = list(zip(path[:-1], path[1:]))
            for (u, v) in path_edges:
                # Find the geometry for the edge (u, v) or (v, u)
                edge_geom = self.edges[
                    ((self.edges["FROM"] == u) & (self.edges["TO"] == v)) |
                    ((self.edges["FROM"] == v) & (self.edges["TO"] == u))
                ]
                # NOTE: Adjusted the column names for edges to match those used in the graph build
                
                if not edge_geom.empty:
                    edge_geom.plot(ax=self.ax, color="red", linewidth=2.5, zorder=3, aspect=1)
        
        # Ensure valid aspect ratio
        self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.autoscale(enable=True)
        self.ax.set_title("Navigation Map (ABC 3rd Floor)")

        self.canvas.draw()

    def run_astar(self):
        """Run A* and update map based on user input"""
        start = self.start_input.text().strip().upper() 
        goal = self.goal_input.text().strip().upper() 

        # 1. Validation Checks
        if not start or not goal:
            QMessageBox.warning(self, "Input Error", "Please enter both a **starting** and a **destination** room number.")
            return

        if start == goal:
            QMessageBox.information(self, "Same Location", "You are already at your destination!")
            self.plot_map() 
            return

        if start not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Start Node", f"Starting room **{start}** not found in map nodes.")
            return

        if goal not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Destination Node", f"Destination room **{goal}** not found in map nodes.")
            return
            
        # 2. Run A* Algorithm
        try:
            path = nx.astar_path(self.G, start, goal, heuristic=self.heuristic, weight="weight")
            
            # 3. Update GUI
            path_str = ' → '.join(path)
            distance = round(nx.path_weight(self.G, path, weight="weight"), 2)
            
            QMessageBox.information(
                self, 
                "Path Found", 
                f"**Start:** {start}\n**Destination:** {goal}\n**Total Distance:** {distance} units\n\n**Path:**\n{path_str}"
            )
            self.plot_map(path)
            
        except nx.NetworkXNoPath:
            QMessageBox.warning(self, "No Path", f"No path found from **{start}** to **{goal}**.")
        except Exception as e:
            QMessageBox.critical(self, "Navigation Error", f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())