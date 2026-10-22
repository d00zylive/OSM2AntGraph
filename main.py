import overpass
import json
import os
import dotenv
import time
import warnings
import math

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

nodes: dict[int, dict[str,int|float|str|None]] = {}
facilities: list[dict[str,str|float]] = []

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
                        "lon": geometry[i]["lon"],
                        "facility": None
                    }
            if way_nodes[-1] not in nodes.keys():
                nodes[way_nodes[-1]] = {
                    "id": way_nodes[len(way_nodes)-1],
                    "lat": geometry[len(way_nodes)-1]["lat"],
                    "lon": geometry[len(way_nodes)-1]["lon"],
                    "facility": None
                }
    elif element["type"] == "relation" and "bounds" in element.keys():
        parsed_quarter["bounds"] = element["bounds"]
    elif element["type"] == "node":
        facility: dict[str,str|float] = {
            "facility": "",
            "lat": element["lat"],
            "lon": element["lon"]
        }
        if "shop" in element["tags"].keys() and element["tags"]["shop"] == "supermarket":
            facility["facility"] = "store"
        
        assert facility["facility"] != ""
        facilities.append(facility)
        

for facility in facilities:
    closest_node:int|None = None
    smallest_distance:float = math.inf
    facility_lat, facility_lon = facility["lat"], facility["lon"]
    assert isinstance(facility_lat,float) and isinstance(facility_lon,float)
    for node in nodes.values():
        node_lat, node_lon = node["lat"], node["lon"]
        assert isinstance(node_lat,float) and isinstance(node_lon,float)
        distance = math.sqrt(abs(facility_lat-node_lat)**2+abs(facility_lon-node_lon)**2)
        if distance < smallest_distance:
            node_id = node["id"]
            assert isinstance(node_id,int)
            closest_node = node_id
            smallest_distance = distance
    assert closest_node is not None
    print(closest_node, smallest_distance)
    nodes[closest_node]["facility"] = facility["facility"]
        
            
for node in nodes.values():
    parsed_node: dict = {
        "id": node["id"],
        "x": node["lon"],
        "y": node["lat"],
        "facility": node["facility"],
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
        