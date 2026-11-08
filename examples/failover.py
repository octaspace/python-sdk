"""Send requests to the next API host when one cannot be reached."""

import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    base_urls=["https://api.octa.space", "https://api.octa.computer"],
) as client:
    print(len(client.nodes.list().data), "nodes")
    print(client.transport_stats())
