"""Reuse connections across requests with keep-alive."""

import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"], keep_alive=True, pool_size=10) as client:
    for session in client.sessions.list().data:
        info = client.services.session(session["uuid"]).info().data
        print(session["uuid"], info.get("is_ready"))
