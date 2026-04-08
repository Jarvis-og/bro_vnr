from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import networkx as nx
import json
from mapFiles.nav_graph import (
    G, edges, rooms, nodes,
    heuristic, get_map_geojson,
    NODE_ID_COL, ROOM_ID_COL
)

router = APIRouter(prefix="/nav", tags=["navigation"])

class NavRequest(BaseModel):
    start: str
    goal: str

@router.get("/map-data")
def map_data():
    return get_map_geojson()

@router.get("/rooms")
def list_rooms():
    # Useful for autocomplete in the frontend
    room_ids = rooms[ROOM_ID_COL].dropna().astype(str).tolist()
    return {"rooms": sorted(room_ids)}

@router.post("/navigate")
def navigate(req: NavRequest):
    start = req.start.strip().upper()
    goal  = req.goal.strip().upper()

    if start not in G.nodes:
        return JSONResponse(status_code=400, content={"error": f"Room '{start}' not found"})
    if goal not in G.nodes:
        return JSONResponse(status_code=400, content={"error": f"Room '{goal}' not found"})

    try:
        path_ids = nx.astar_path(G, start, goal, heuristic=heuristic, weight="weight")
        cost     = nx.astar_path_length(G, start, goal, weight="weight")
    except nx.NetworkXNoPath:
        return JSONResponse(status_code=404, content={"error": "No route found between these rooms"})

    # Filter edges that belong to the path
    path_pairs = set(zip(path_ids, path_ids[1:])) | set(zip(path_ids[1:], path_ids))
    path_edges = edges[
        edges.apply(lambda r: (str(r["FROM"]), str(r["TO"])) in path_pairs, axis=1)
    ]

    return {
        "path_node_ids": path_ids,
        "path_geojson":  json.loads(path_edges.to_json()),
        "total_cost":    round(cost, 2),
    }