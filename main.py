import overpass
import json
import os
import dotenv
import time
import warnings

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]

with warnings.catch_warnings(action="ignore",category=DeprecationWarning):
    api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False, timeout=(25,120))

def get_quarter(quarter_name: str) -> dict:
    t = 1
    while True:
        try:
            with open(f"{quarter_name}_raw.json", "r") as f:
                quarter = json.load(f)
            assert isinstance(quarter,dict)
            return quarter
        except FileNotFoundError:
            try:
                print("Attempting request")
                with warnings.catch_warnings(action="ignore",category=DeprecationWarning):
                    quarter = api.get(f"""
                                        (
                                            area["name"="Lunetten"]["place"="quarter"]->.a;
                                            relation["boundary"]["name"="Lunetten"]["place"="quarter"](area.a);
                                            way["highway"~"(footway|pedestrian|living_street|residential|service|cycleway|path|unclassified|footpath)"](area.a);
                                            node["shop"="supermarket"](area.a);
                                        );
                                        """, responseformat="json", verbosity="geom")
                assert isinstance(quarter,dict)
                print("Request succesful")

                with open(f"{quarter_name}_raw.json", "w") as f:
                    json.dump(quarter, f, indent=4)
                return quarter
            except (overpass.errors.UnknownOverpassError, overpass.errors.TimeoutError, overpass.errors.ServerLoadError):
                print(f"Request failed. Retrying in {t} seconds")
                time.sleep(t)
                t *= 2

quarter = get_quarter(QUARTER_NAME)

nodes: dict[int, dict[str,int|float]] = {}

parsed_quarter: dict[str,list[dict]|dict[str,float]] = {
    "bounds": {},
    "nodes": []
}
assert isinstance(parsed_quarter["nodes"], list)

connections: list[tuple[int,int]] = []
for element in quarter["elements"]:
    if element["type"] == "way":
        if "nodes" in element.keys() and "geometry" in element.keys():
            way_nodes: list[int] = element["nodes"]
            geometry: list[dict[str,float]] = element["geometry"]
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
    elif element["type"] == "relation" and "bounds" in element.keys():
        parsed_quarter["bounds"] = element["bounds"]
    elif element["type"] == "node":
        pass # Gotta do something with facilities
            
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
        