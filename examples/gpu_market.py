"""Print the GPU market now; no API key needed."""

from octaspace import OctaSpaceClient, format_usd

with OctaSpaceClient() as client:
    for gpu in client.stats.gpu_current()["gpus"]:
        median = gpu["available_price"]["p50"]
        price = format_usd(median) if median is not None else "—"
        print(f"{gpu['model']:<32} {gpu['available']:>4} free  {price} per GPU-hour")
