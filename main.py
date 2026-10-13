import overpass
import json
import os
import dotenv

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]
print(QUARTER_NAME)

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False)

def get_quarter(quarter_name: str) -> dict:
    if api.slots_available > 1:
        try:
            with open(f"{quarter_name}.json", "r") as f:
                quarter = json.load(f)
        except FileNotFoundError:
            boundary = api.get(f'relation["boundary"]["place"="quarter"]["name"="{quarter_name}"]',responseformat="json",verbosity="ids",)
            assert isinstance(boundary,dict)
            rel_id = boundary["elements"][0]["id"]
            quarter = api.get(f'way(area:{3600000000+rel_id})["highway"="footway"]', responseformat="json",verbosity="geom")
            assert isinstance(quarter,dict)
            with open(f"{quarter_name}.json", "w") as f:
                json.dump(quarter, f, indent=4)
        return quarter
    else:
        raise RuntimeError("Ratelimited")

quarter = get_quarter(QUARTER_NAME)

nodes: dict[int, dict[str,int|float]] = {}

parsed_quarter: dict[str,list[dict]] = {
    "nodes": []
}

connections: list[tuple[int,int]] = []
for footway in quarter["elements"]:
    if "nodes" in footway.keys() and "geometry" in footway.keys():
        way_nodes: list[int] = footway["nodes"]
        geometry: list[dict[str,float]] = footway["geometry"]
        for i in range(len(way_nodes)-1):
            connections.append((way_nodes[i],way_nodes[i+1]))
            if way_nodes[i] not in nodes.keys():
                nodes[way_nodes[i]] = {
                    "id": way_nodes[i],
                    "lat": geometry[i]["lat"],
                    "lon": geometry[i]["lon"]
                }
        if way_nodes[-1] not in nodes.keys():
            nodes[way_nodes[-1]] = {
                "id": way_nodes[len(way_nodes)-1],
                "lat": geometry[len(way_nodes)-1]["lat"],
                "lon": geometry[len(way_nodes)-1]["lon"]
            }
            
for node in nodes.values():
    parsed_node: dict = {
        "id": node["id"],
        "x": node["lat"],
        "y": node["lon"],
        "facility": None, # Need to figure out later
        "connections": [connection[0] if connection[1] == node["id"] else connection[1] for connection in connections if node["id"] in connection]
    }
    parsed_quarter["nodes"].append(parsed_node)
    
with open("export.json", "x") as f:
    json.dump(parsed_quarter, f, indent=2)