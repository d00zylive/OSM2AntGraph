import overpass
import json
import os
import dotenv

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]
print(QUARTER_NAME)

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False)

if api.slots_available > 0:
    boundary = api.get(f'relation["boundary"]["place"="quarter"]["name"="{QUARTER_NAME}"]',responseformat="json",verbosity="ids",)
    assert isinstance(boundary, dict)
    rel_id = boundary["elements"][0]["id"]
    response = api.get(f'nw(area:{3600000000+rel_id})', responseformat="json")
    print(response)
    with open("output.json", "w") as f:
        json.dump(response, f, indent=4)
else:
    raise RuntimeError("Ratelimited")

# TODO: process output