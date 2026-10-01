import overpass
import json
import os
import dotenv

dotenv.load_dotenv()
QUARTER_NAME = os.environ["QUARTER"]
print(QUARTER_NAME)

api = overpass.API(user_agent="Ant Colony Simulation on Open Street Map (d00zyl1v3@gmail.com)", debug=False)

query = f'''
relation["boundary"]["place"="quarter"]["name"="{QUARTER_NAME}"]
'''

if api.slots_available > 0:
    response = api.get(query,responseformat="json")
    assert isinstance(response, dict)

    with open("output.json", "w") as f:
        json.dump(response, f, indent=4)
        
    quarter = response["elements"][0]
    print(quarter)
else:
    print("Ratelimited")