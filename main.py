import overpass
import json
import os
import dotenv

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]
print(QUARTER_NAME)

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False)

def get_quarter(quarter_name: str) -> dict:
    if api.slots_available > 0:
        try:
            with open(f"{quarter_name}.json", "r") as f:
                quarter = json.load(f)
        except FileNotFoundError:
            boundary = api.get(f'relation["boundary"]["place"="quarter"]["name"="{quarter_name}"]',responseformat="json",verbosity="ids",)
            assert isinstance(boundary, dict)
            rel_id = boundary["elements"][0]["id"]
            quarter = api.get(f'node(area:{3600000000+rel_id});way(area:{3600000000+rel_id})["highway"="footway"]', responseformat="json")
            assert isinstance(quarter,dict)
            with open(f"{quarter_name}.json", "w") as f:
                json.dump(quarter, f, indent=4)
        return quarter
    else:
        raise RuntimeError("Ratelimited")

quarter = get_quarter(QUARTER_NAME)

nodes: list[dict] = []
footways: list[dict] = []

parsed_quarter: dict[str,list[dict]] = {
    "nodes": []
}

for element in quarter["elements"]:
    assert isinstance(element,dict)
    if element["type"] == "way":
        footways.append(element)
    elif element["type"] == "node":
        nodes.append(element)

connections: list[tuple[int,int]] = []
for footway in footways:
    if "nodes" in footway.keys():
        way_nodes: list[int] = footway["nodes"]
        for i in range(len(way_nodes)-1):
            connections.append((way_nodes[i],way_nodes[i+1]))
            
for node in nodes:
    parsed_node: dict = {
        "id": node["id"]
    }
            
print(connections)