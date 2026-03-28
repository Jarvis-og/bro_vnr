import sys
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QMessageBox
)


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Indoor Navigation GUI")

        # ---------------- Load Data ----------------
        self.nodes = gpd.read_file("PG_1ST_NODES.shp")
        self.edges = gpd.read_file("PG_1ST_EDGES.shp")

        # Build graph
        self.G = nx.Graph()
        for _, row in self.nodes.iterrows():
            node_id = row["PG1NODES"]
            self.G.add_node(node_id, pos=(row.geometry.x, row.geometry.y))
        self.valid_nodes = set(self.G.nodes)

        for _, row in self.edges.iterrows():
            u = row["FROM"]
            v = row["TO"]
            length = row.geometry.length
            self.G.add_edge(u, v, weight=length, edge_id=row["PG1EDGES"])

        # Default start node
        self.start = "BE1"

        # ---------------- Matplotlib Figure ----------------
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # ---------------- GUI Layout ----------------
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter Destination Room Number:"))

        self.goal_input = QLineEdit()
        layout.addWidget(self.goal_input)

        self.nav_button = QPushButton("Navigate")
        self.nav_button.clicked.connect(self.run_astar)
        layout.addWidget(self.nav_button)

        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initial plot
        self.plot_map()

    def heuristic(self, u, v):
        (x1, y1) = self.G.nodes[u]["pos"]
        (x2, y2) = self.G.nodes[v]["pos"]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def plot_map(self, path=None):
     """Draw shapefile map with optional highlighted path"""
     self.ax.clear()
 
     # Plot base layers from shapefiles
     self.edges.plot(ax=self.ax, color="lightgray", linewidth=1)
     self.nodes.plot(ax=self.ax, color="lightblue", markersize=40)
 
     # Highlight path if available
     if path:
         # Highlight nodes
         path_nodes = self.nodes[self.nodes["PG1NODES"].isin(path)]
         path_nodes.plot(ax=self.ax, color="red", markersize=60)
 
         # Highlight edges
         path_edges = list(zip(path[:-1], path[1:]))
         for (u, v) in path_edges:
             edge_geom = self.edges[
                 ((self.edges["FROM"] == u) & (self.edges["TO"] == v)) |
                 ((self.edges["FROM"] == v) & (self.edges["TO"] == u))
             ]
             if not edge_geom.empty:
                 edge_geom.plot(ax=self.ax, color="red", linewidth=2)
 
     # ✅ Ensure valid aspect ratio
     self.ax.set_aspect("equal", adjustable="datalim")
     self.ax.autoscale(enable=True)
     self.ax.set_title("Navigation Map")
 
     self.canvas.draw()

    def run_astar(self):
        """Run A* and update map"""
        goal = self.goal_input.text().strip()

        if not goal:
            QMessageBox.warning(self, "Error", "Please enter a destination room number.")
            return

        if goal not in self.valid_nodes:
            QMessageBox.warning(self, "Invalid Node", f"Room {goal} not found in map.")
            return

        try:
            path = nx.astar_path(self.G, self.start, goal, heuristic=self.heuristic, weight="weight")
            QMessageBox.information(self, "Path Found", f"A* Path: {' → '.join(path)}")
            self.plot_map(path)
        except nx.NetworkXNoPath:
            QMessageBox.warning(self, "No Path", f"No path found from {self.start} to {goal}.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())