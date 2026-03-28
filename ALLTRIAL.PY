import sys
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, 
    QLineEdit, QLabel, QMessageBox, QScrollArea
)
from PyQt5.QtGui import QFont
import numpy as np 

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏢 BRO - Multi-Floor Indoor Navigation")
        self.resize(1100, 900)  

        # --- Vertical Connections ---
        self.VERTICAL_CONNECTIONS = {
            "STAIRDOWNABC3": {"to_node": "STAIR UP2", "cost": 30.0},
            "STAIR UP2": {"to_node": "STAIRDOWNABC3", "cost": 30.0},
        }
        
        self.NODE_ID_COL = "PG1NODES"  
        self.EDGE_ID_COL = "PG1EDGES" 
        self.ROOM_ID_COL = "PG1ROOMS"

        # --- Data Loading ---
        try:
            self.nodes = gpd.read_file("ALLPGMERGEDNODES.shp")
            self.edges = gpd.read_file("ALLPGMERGEDEDGES.shp")
            self.rooms = gpd.read_file("ALLPGMERGEDROOMS.shp")
            # Loading both restricted and corridors as requested in your snippet
            self.restricted_areas = gpd.read_file("ALLPGMERGEDRESTRICTEDAREA.shp")
            self.corridors = gpd.read_file("ALLPGMERGEDCORRIDORS.shp")
        except Exception as e:
            QMessageBox.critical(self, "Data Error", f"File loading failed: {e}")
            sys.exit(1)

        # --- Build Graph ---
        self.G = nx.Graph()
        for _, row in self.nodes.iterrows():
            node_id = str(row[self.NODE_ID_COL])
            self.G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))
        
        self.valid_nodes = set(self.G.nodes)

        for _, row in self.edges.iterrows():
            u, v = str(row["FROM"]), str(row["TO"])
            if u in self.valid_nodes and v in self.valid_nodes:
                self.G.add_edge(u, v, weight=row.geometry.length, edge_id=str(row[self.EDGE_ID_COL]))

        for u, info in self.VERTICAL_CONNECTIONS.items():
            v = info["to_node"]
            if u in self.valid_nodes and v in self.valid_nodes:
                self.G.add_edge(u, v, weight=info["cost"], edge_id=f"{u}_{v}_V")

        # --- Matplotlib Setup ---
        # We use a taller figsize ratio (e.g., width=10, height=25) to prevent squishing
        self.figure, self.ax = plt.subplots(figsize=(10, 25)) 
        self.canvas = FigureCanvas(self.figure)

        # --- GUI Layout with Scrolling ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # 1. Fixed Header (Controls)
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        
        font = QFont("Arial", 10)
        controls_layout.addWidget(QLabel("📍 **Starting Room ID:**"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g., P101")
        controls_layout.addWidget(self.start_input)

        controls_layout.addWidget(QLabel("🏁 **Destination Room ID:**"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., P401")
        controls_layout.addWidget(self.goal_input)

        self.nav_button = QPushButton("🚀 Start Navigation")
        self.nav_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.nav_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.nav_button.clicked.connect(self.run_astar)
        controls_layout.addWidget(self.nav_button)
        
        main_layout.addWidget(controls_panel)

        # 2. Scrollable Map Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # This container holds the canvas
        self.canvas_container = QWidget()
        canvas_layout = QVBoxLayout(self.canvas_container)
        
        # CRITICAL: Force the canvas to be very tall (e.g., 3000 pixels) 
        # so each floor has room to be large.
        self.canvas.setMinimumHeight(3000) 
        canvas_layout.addWidget(self.canvas)
        
        self.scroll_area.setWidget(self.canvas_container)
        main_layout.addWidget(self.scroll_area)

        self.setCentralWidget(main_widget)
        self.plot_map()

    def heuristic(self, u, v):
        try:
            (x1, y1) = self.G.nodes[u]["pos"]
            (x2, y2) = self.G.nodes[v]["pos"]
            return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        except: return float('inf')

    def plot_map(self, path=None):
        self.ax.clear()

        # Plot Rooms
        self.rooms.plot(ax=self.ax, color="#C38EFC", edgecolor="black", linewidth=0.5, zorder=0,aspect=1)
        
        # Plot Restricted Areas
        self.restricted_areas.plot(ax=self.ax, color="#FFCCCC", hatch='///', alpha=0.6, zorder=0.5,aspect=1)

        # Plot Edges
        self.edges.plot(ax=self.ax, color="gray", linewidth=1.0, alpha=0.5, zorder=1,aspect=1)

        # Room Labels
        for _, row in self.rooms.iterrows():
            x, y = row.geometry.centroid.x, row.geometry.centroid.y
            self.ax.text(x, y, str(row[self.ROOM_ID_COL]), fontsize=7, color='darkgreen', 
                         ha='center', va='center', zorder=7,
                         bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))

        # Plot Nodes
        self.nodes.plot(ax=self.ax, color="lightblue", markersize=30, zorder=2,aspect=1)

        # Highlight Path
        if path:
            # Path Nodes
            path_nodes_gdf = self.nodes[self.nodes[self.NODE_ID_COL].isin(path)]
            path_nodes_gdf.plot(ax=self.ax, color="red", markersize=60, zorder=4,aspect=1)

            # Path Edges
            path_edges = list(zip(path[:-1], path[1:]))
            for (u, v) in path_edges:
                edge_geom = self.edges[((self.edges["FROM"] == u) & (self.edges["TO"] == v)) |
                                       ((self.edges["FROM"] == v) & (self.edges["TO"] == u))]
                
                if not edge_geom.empty:
                    edge_geom.plot(ax=self.ax, color="red", linewidth=4.0, zorder=3,aspect=1)
                else:
                    # Vertical connection (Stairs/Lifts)
                    pos_u, pos_v = self.G.nodes[u]["pos"], self.G.nodes[v]["pos"]
                    self.ax.plot([pos_u[0], pos_v[0]], [pos_u[1], pos_v[1]], 
                                 color='darkorange', linewidth=5.0, linestyle='--', zorder=5,aspect=1)

        self.ax.set_aspect("equal")
        self.ax.set_title("Multi-Floor Map (Scroll Down for More Floors)")
        self.canvas.draw()

    def run_astar(self):
        start = self.start_input.text().strip().upper()
        goal = self.goal_input.text().strip().upper()

        if start not in self.valid_nodes or goal not in self.valid_nodes:
            QMessageBox.warning(self, "Error", "Invalid Room IDs.")
            return

        try:
            path = nx.astar_path(self.G, start, goal, heuristic=self.heuristic, weight="weight")
            self.plot_map(path)
            
            # Optional: Scroll back to the top when a new path is found
            self.scroll_area.verticalScrollBar().setValue(0)
            
        except nx.NetworkXNoPath:
            QMessageBox.warning(self, "No Path", "No route found between floors.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())