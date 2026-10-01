import overpass
import json
import os
import dotenv

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]
print(QUARTER_NAME)

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False)

if api.slots_available > 0:
    quarter = api.get(f'relation["boundary"]["place"="quarter"]["name"="{QUARTER_NAME}"]',responseformat="json",verbosity="ids",)
    assert isinstance(quarter, dict)
    with open("quarter.json", "w") as f:
        json.dump(quarter, f, indent=4)
    relId = quarter["elements"][0]["id"]
    print(relId)
    
    response = api.get(f'nwr(area:{3600000000+relId})', responseformat="json")
    print(response)
    with open("output.json", "w") as f:
        json.dump(response, f, indent=4)
else:
    print("Ratelimited")