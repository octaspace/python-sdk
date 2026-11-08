"""Print the account balance and the machines available for rent."""

import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"]) as client:
    balance = client.accounts.balance().data["balance"]
    print(f"Balance: {balance / 10**18:.6f} OCTA")

    for machine in client.services.mr.list().data:
        print(machine["node_id"], machine["country"], machine["city"])
