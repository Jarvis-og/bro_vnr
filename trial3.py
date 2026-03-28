import sys
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QFont
import numpy as np 

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏢 Multi-Floor Indoor Navigation (Meters)")
        self.resize(1100, 950)  

        # Adjust this scale factor based on your coordinate system
        self.SCALE_FACTOR = 0.01  

        self.VERTICAL_CONNECTIONS = {
            "STAIRDOWNABC3": {"to_node": "STAIR UP2", "cost": 30.0},
            "STAIR UP2": {"to_node": "STAIRDOWNABC3", "cost": 30.0},
        }
        
        self.NODE_ID_COL = "ABC2NODES"  
        self.EDGE_ID_COL = "ABC2EDGES" 
        self.ROOM_ID_COL = "ABC2ROOMS" 

        try:
            self.nodes = gpd.read_file("PG_ABC_MERGEDNODES.shp")
            self.edges = gpd.read_file("PG_ABC_MERGEDEDGES.shp")
            self.rooms = gpd.read_file("PG_ABC_MERGEDROOMS.shp")
            self.restricted_areas = gpd.read_file("PG_ABC_MERGEDRESTRICTEDAREA.shp")
        except Exception as e:
            QMessageBox.critical(self, "Data Loading Error", f"Error: {e}")
            sys.exit(1)

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
                self.G.add_edge(u, v, weight=info["cost"], edge_id=f"{u}_to_{v}_VERTICAL")

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        font = QFont(); font.setPointSize(10)
        
        layout.addWidget(QLabel("📍 **Enter Current/Starting Room ID:**"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g., A302")
        layout.addWidget(self.start_input)

        layout.addWidget(QLabel("🏁 **Enter Destination Room ID:**"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., B205")
        layout.addWidget(self.goal_input)

        self.nav_button = QPushButton("🚀 Navigate (Find Shortest Path)")
        self.nav_button.clicked.connect(self.run_astar)
        layout.addWidget(self.nav_button)

        layout.addWidget(QLabel("📜 **Step-by-Step Directions (Meters):**"))
        self.instruction_box = QTextEdit()
        self.instruction_box.setReadOnly(True)
        self.instruction_box.setMinimumHeight(200)
        self.instruction_box.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.instruction_box)

        layout.addWidget(self.canvas, 20) 

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.plot_map()

    def generate_directions(self, path):
        directions = []
        directions.append(f"🟢 **START**: Exit Room {path[0]} and walk straight.")
        accumulated_dist = 0
        
        for i in range(1, len(path) - 1):
            u, v, w = path[i-1], path[i], path[i+1]
            segment_dist = self.G[u][v].get("weight", 0) * self.SCALE_FACTOR
            accumulated_dist += segment_dist

            pos_v = self.G.nodes[v]["pos"]
            distances = self.rooms.geometry.centroid.distance(
                gpd.points_from_xy([pos_v[0]], [pos_v[1]])[0]
            )
            landmark = self.rooms.loc[distances.idxmin(), self.ROOM_ID_COL]

            is_vertical = any((v == node1 and w == info["to_node"]) 
                             for node1, info in self.VERTICAL_CONNECTIONS.items())
            
            p1, p2, p3 = self.G.nodes[u]["pos"], pos_v, self.G.nodes[w]["pos"]
            v1 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
            angle1, angle2 = np.arctan2(v1[1], v1[0]), np.arctan2(v2[1], v2[0])
            diff = np.degrees(angle2 - angle1)
            diff = (diff + 180) % 360 - 180 

            action = None
            dist_str = f"{round(accumulated_dist, 1)} meters"

            if is_vertical:
                action = f"🪜 **STEP**: Walk {dist_str}, then take the stairs/lift near {landmark} to reach {w}."
            elif diff > 25:
                action = f"👈 **STEP**: Walk {dist_str}, then turn LEFT near {landmark}."
            elif diff < -25:
                action = f"👉 **STEP**: Walk {dist_str}, then turn RIGHT near {landmark}."

            if action:
                directions.append(action)
                accumulated_dist = 0 

        final_dist = self.G[path[-2]][path[-1]].get("weight", 0) * self.SCALE_FACTOR
        accumulated_dist += final_dist
        directions.append(f"🏁 **DESTINATION**: Walk {round(accumulated_dist, 1)} meters to arrive at Room {path[-1]}.")
        return "\n\n".join(directions)

    def plot_map(self, path=None):
        self.ax.clear()
        
        # Plotting with aspect=1 for accurate proportions
        self.rooms.plot(ax=self.ax, color="#C38EFC", edgecolor="black", linewidth=0.5, zorder=0, aspect=1)
        self.restricted_areas.plot(ax=self.ax, color="#FFCCCC", edgecolor="darkred", hatch='///', alpha=0.6, zorder=0.5, aspect=1)
        self.edges.plot(ax=self.ax, color="gray", linewidth=1.0, alpha=0.7, zorder=1, aspect=1)
        
        for idx, row in self.rooms.iterrows():
            self.ax.text(row.geometry.centroid.x, row.geometry.centroid.y, str(row[self.ROOM_ID_COL]), 
                         fontsize=7, color='darkgreen', ha='center', va='center', zorder=7,
                         bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))

        self.nodes.plot(ax=self.ax, color="lightblue", markersize=40, zorder=2, aspect=1)
        
        if path:
            path_nodes = self.nodes[self.nodes[self.NODE_ID_COL].isin(path)]
            path_nodes.plot(ax=self.ax, color="red", markersize=80, zorder=4, aspect=1)
            path_edges = list(zip(path[:-1], path[1:]))
            for (u, v) in path_edges:
                edge_geom = self.edges[((self.edges["FROM"] == u) & (self.edges["TO"] == v)) | 
                                       ((self.edges["FROM"] == v) & (self.edges["TO"] == u))]
                if not edge_geom.empty:
                    edge_geom.plot(ax=self.ax, color="red", linewidth=3.0, zorder=3, aspect=1)
                elif any((u == n1 and v == n2["to_node"]) or (v == n1 and u == n2["to_node"]) 
                         for n1, n2 in self.VERTICAL_CONNECTIONS.items()):
                    p_u, p_v = self.G.nodes[u]["pos"], self.G.nodes[v]["pos"]
                    self.ax.plot([p_u[0], p_v[0]], [p_u[1], p_v[1]], color='darkorange', linewidth=4.0, linestyle='--', zorder=5,aspect=1)

        # Force Matplotlib to also respect the aspect ratio and adjust limits automatically
        self.ax.set_aspect('equal', adjustable='datalim')
        self.canvas.draw()

    def run_astar(self):
        start, goal = self.start_input.text().strip().upper(), self.goal_input.text().strip().upper()
        if not start or not goal: return
        if start not in self.valid_nodes or goal not in self.valid_nodes: return

        try:
            path = nx.astar_path(self.G, start, goal, weight="weight")
            self.plot_map(path)
            self.instruction_box.setText(self.generate_directions(path))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())