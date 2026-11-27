"""Print the account balance and the machines available for rent."""

import os

from octaspace import OctaSpaceClient, format_usd

with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"]) as client:
    print("Balance:", format_usd(client.accounts.balance()["balance"]))

    for machine in client.compute.list():
        gpus = ", ".join(gpu["model"] for gpu in machine["gpus"]) or "no GPU"
        print(machine["node_number"], machine["city"], format_usd(machine["base_price"]), gpus)
