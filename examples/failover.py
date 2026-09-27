from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key="your-api-key",
    base_urls=["https://api.octa.space", "https://api.octa.computer"],
) as client:
    print(client.transport_stats())
    print(client.nodes.list().data)
