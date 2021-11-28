#

import json
import requests
from analysis.analyzer import Analyzer


# Dagda remote agent class

class Agent:

    # -- Public methods

    # Agent Constructor
    def __init__(self, dagda_server_url):
        super(Agent, self).__init__()
        self.dagda_server_url = dagda_server_url
        self.analyzer = Analyzer(dagda_server_url=dagda_server_url)

    def run_static_analysis(self, image_name=None, container_id=None):
        evaluated_docker_image = self.analyzer.evaluate_image(image_name=image_name, container_id=container_id)
        docker_image_name = evaluated_docker_image['image_name']
        r = requests.post(self.dagda_server_url + '/history/' + docker_image_name,
                          data=json.dumps(evaluated_docker_image),
                          headers={'content-type': 'application/json'})
        # -- Print cmd output
        if r is not None and r.content:
            print(json.dumps(json.loads(r.content.decode('utf-8')), sort_keys=True, indent=4))
