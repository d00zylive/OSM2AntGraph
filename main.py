import overpass
import json
import os
import dotenv
import time

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False, timeout=(25,120))

def get_quarter(quarter_name: str) -> tuple[dict,dict[str,float]]:
    t = 1
    while True:
        try:
            with open(f"{quarter_name}_raw.json", "r") as f:
                quarter_file: list[dict] = json.load(f)
                boundingbox = quarter_file[0]
                quarter = quarter_file[1]
            return quarter, boundingbox
        except FileNotFoundError:
            try:
                print("Attempting request")
                boundary = api.get(f'relation["boundary"]["place"="quarter"]["name"="{quarter_name}"]',responseformat="json",verbosity="ids bb",)
                assert isinstance(boundary,dict)
                boundingbox = boundary["elements"][0]["bounds"]
                rel_id = boundary["elements"][0]["id"]
                quarter = api.get(f'way(area:{3600000000+rel_id})["highway"~"(footway|pedestrian|living_street|residential|service|cycleway|path|unclassified)"]', responseformat="json", verbosity="geom")
                assert isinstance(quarter,dict)
                with open(f"{quarter_name}_raw.json", "w") as f:
                    json.dump([boundingbox, quarter], f, indent=4)
            except (overpass.errors.UnknownOverpassError, overpass.errors.TimeoutError, overpass.errors.ServerLoadError):
                print(f"Request failed. Retrying in {t} seconds")
                time.sleep(t)
                t *= 2

quarter, boundingbox = get_quarter(QUARTER_NAME)

nodes: dict[int, dict[str,int|float]] = {}

parsed_quarter: dict[str,list[dict]|dict[str,float]] = {
    "bounds": boundingbox,
    "nodes": []
}
assert isinstance(parsed_quarter["nodes"], list)

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
        "x": node["lon"],
        "y": node["lat"],
        "facility": None, # Need to figure out later
        "connections": [connection[0] if connection[1] == node["id"] else connection[1] for connection in connections if node["id"] in connection]
    }
    parsed_quarter["nodes"].append(parsed_node)

try:
    with open(f"{QUARTER_NAME}.json", "x") as f:
        json.dump(parsed_quarter, f, indent=2)
except FileExistsError:
    if input(f"{QUARTER_NAME}.json already exists. Are you sure you want to overwrite? (y/N)    ") == "y":
        with open(f"{QUARTER_NAME}.json", "w") as f:
            json.dump(parsed_quarter, f, indent=2)
        