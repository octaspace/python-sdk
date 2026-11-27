"""Send requests to the next API host when one cannot be reached.

Replace the second host with a proxy of your own in front of the OctaSpace API.
"""

import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    base_urls=["https://api.octa.space", "https://octa-proxy.example.com"],
) as client:
    print(len(client.sessions.list()), "running sessions")
    print(client.transport_stats())
