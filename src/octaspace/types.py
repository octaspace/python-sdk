"""Types of the API's requests and responses.

Responses are plain ``dict`` objects parsed from JSON; these ``TypedDict``
classes describe their keys for type checkers and editors. Keys that the
types do not list are kept as well.

Units: money is an integer number of micro-USD (``1`` = $0.000001, see
``octaspace.format_usd``); network speeds are whole Mbit/s (``0`` if not
measured); memory and disk sizes are bytes unless a field says otherwise.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypeAlias, TypedDict

NodeNumber: TypeAlias = str
"""Node number, for example ``7KQ4-M2XD-4``. Case, dashes and spaces are ignored,
``O`` is read as ``0``, ``I`` and ``L`` as ``1``."""

MicroUsd: TypeAlias = int
"""Amount of money in micro-USD: ``1`` = $0.000001."""

UserEnvs: TypeAlias = dict[str, str]
"""Environment variables of a container: up to 64, values up to 4 KiB."""

BatchId: TypeAlias = str | int
"""Your id of a batch item, returned with its result."""


# Accounts


class AccountBalance(TypedDict):
    """Account balance: ``balance / 10 ** decimals`` in ``currency``.

    The balance is in micro-USD (``decimals`` is 6). It already includes what
    running sessions have used and can be negative.
    """

    balance: MicroUsd
    currency: Literal["USD"]
    decimals: int


# Machine listings


class MachineGpu(TypedDict):
    """A GPU of a machine for rent. Integer fields are ``None`` when unknown."""

    model: str
    mem_total_mb: int | None
    """Total memory, MB."""
    pcie_link_gen: int | None
    pcie_link_width: int | None
    core_clock: NotRequired[int | None]
    """Core clock ceiling, MHz: the one the owner locked, otherwise the card's maximum."""
    mem_clock: NotRequired[int | None]
    """Memory clock ceiling, MHz."""
    power_limit: NotRequired[int | None]
    """Power limit, watts."""
    tuned: NotRequired[bool]
    """The owner changed the power limit or locked the clocks."""


class Reliability(TypedDict, total=False):
    """Node reliability: ``uptime`` is the percent of time online over 30 days.

    Session counters (``stability``, ``s_normal``, ``s_failed``, …) are present
    when known.
    """

    uptime: float
    stability: float
    s_normal: int
    s_failed: int


class ComputeMachine(TypedDict):
    """A machine available for rent (``compute.list()``)."""

    node_number: NodeNumber
    base_price: MicroUsd
    """Per hour of rent."""
    storage_price: MicroUsd
    """Per GB of disk per hour."""
    traffic_price: MicroUsd
    """Per GB of traffic."""
    min_rent_minutes: int
    """Minimum rent, minutes; 0 = none.

    A session stopped sooner is charged as if it ran this long.
    """
    arch: Literal["x86_64", "aarch64"]
    cpu_cores: int
    cpu_model_name: str
    memory: int
    """Free memory, bytes."""
    memory_speed: int
    """MT/s."""
    memory_type: str
    disk: int
    """Free disk space, bytes."""
    disk_type: Literal["nvme", "ssd", "hdd"] | None
    disk_speed_mbs: int
    """MB/s."""
    net_down_mbps: int
    net_up_mbps: int
    free_ports: int
    gpu_vendor: str | None
    gpus: list[MachineGpu]
    cuda_version: str | None
    ai_score: int
    blender_score: int
    city: str
    country: str | None
    country_iso: NotRequired[str | None]
    """ISO 3166-1 alpha-2 code of the country."""
    os_version: NotRequired[str | None]
    """Operating system of the node, for example ``Ubuntu 24.04``."""
    virt: NotRequired[str]
    """Virtualization the node runs in; ``none`` on bare metal."""
    is_wsl: NotRequired[bool]
    """The node runs in WSL."""
    is_hive_os: NotRequired[bool]
    """The node runs HiveOS."""
    gpu_pt: NotRequired[bool]
    """GPU passthrough is available."""
    reliability: Reliability


class RenderMachine(TypedDict):
    """A node available for render (``render.list()``): an NVIDIA GPU with a Blender score."""

    node_number: NodeNumber
    base_price: MicroUsd
    """Per hour; render is billed by time only."""
    min_rent_minutes: int
    blender_score: int
    """Blender benchmark: the OptiX score, the CUDA one when there is none."""
    cpu_cores: int
    cpu_model_name: str
    memory: int
    disk: int
    net_down_mbps: int
    net_up_mbps: int
    gpu_vendor: str | None
    gpus: list[MachineGpu]
    cuda_version: str | None
    city: str
    country: str | None
    reliability: Reliability


VpnProtocol: TypeAlias = Literal["wg", "awg", "reality", "http_proxy"]
"""A VPN protocol: WireGuard, AmneziaWG, VLESS Reality or an HTTP proxy."""


class VpnMachine(TypedDict):
    """A node offered for VPN (``vpn.list()``)."""

    node_number: NodeNumber
    traffic_price: MicroUsd
    """Per GB of traffic; VPN is billed by traffic only."""
    protocols: list[VpnProtocol]
    """Protocols that passed the end-to-end check on this node, at least one."""
    city: NotRequired[str]
    country: NotRequired[str | None]
    country_iso: NotRequired[str | None]
    latitude: NotRequired[float | None]
    longitude: NotRequired[float | None]
    residential: NotRequired[bool]
    """The node's address is believed to be assigned to a residence."""
    net_down_mbps: NotRequired[int]
    net_up_mbps: NotRequired[int]


# Apps and starts


class ComputeAppExtra(TypedDict, total=False):
    logo: str
    min_disk_size: int
    """Disk the app needs, GB. Advice only: a smaller ``disk_size`` is accepted."""


class ComputeApp(TypedDict):
    """An application to start a compute session from (``compute.apps()``)."""

    uuid: str
    """Pass as ``app`` to ``compute.start()``."""
    name: str
    image: str
    """Docker image, for example ``ubuntu:24.04``."""
    personal: bool
    """One of your own apps, not an official one."""
    category: NotRequired[str | None]
    description: NotRequired[str | None]
    entrypoint: NotRequired[str]
    ports: NotRequired[list[int]]
    http_ports: NotRequired[list[int]]
    extra: NotRequired[ComputeAppExtra]
    startup_script: NotRequired[str | None]
    """Your own apps only."""
    envs: NotRequired[UserEnvs]
    """Your own apps only."""


class StartResult(TypedDict):
    """A session start or restart accepted by the API."""

    uuid: str


class BatchSuccess(TypedDict):
    id: BatchId
    status: Literal[0]
    uuid: str


class BatchFailure(TypedDict):
    id: BatchId
    status: Literal[1]
    reason: str


BatchResult: TypeAlias = BatchSuccess | BatchFailure
"""Result of one batch item: ``status`` 0 with the session ``uuid``, or 1 with the ``reason``."""


class ComputeBatchItem(TypedDict):
    """One item of ``compute.start_batch()``: the arguments of ``compute.start()``."""

    node_number: NodeNumber
    image: str
    id: NotRequired[BatchId]
    """Returned with the item's result; its position in the list by default. Must be unique."""
    app: NotRequired[str]
    disk_size: NotRequired[int]
    envs: NotRequired[UserEnvs]
    ports: NotRequired[list[int]]
    http_ports: NotRequired[list[int]]
    entrypoint: NotRequired[str]
    args: NotRequired[str]
    ssh: NotRequired[bool]
    fm: NotRequired[bool]
    startup_script: NotRequired[str]


class RenderBatchItem(TypedDict):
    """One item of ``render.start_batch()``."""

    node_number: NodeNumber
    id: NotRequired[BatchId]


# Sessions

SessionStatus: TypeAlias = Literal["starting", "ready"]


class SshEndpoint(TypedDict):
    """Where to connect with SSH.

    ``user`` comes from the image's ``USER`` (``root`` when it sets none), so
    the image author controls it: validate ``user`` and ``host`` and pass them
    to ``ssh`` as separate arguments after ``--``.
    """

    host: str
    port: int
    user: str


class SessionSsh(TypedDict):
    direct: SshEndpoint | None
    """Directly on the node; only when your account has an SSH key."""
    proxy: SshEndpoint | None
    """Through the proxy."""
    web: str | None
    """Web terminal URL. It contains credentials: do not log it."""


class SessionGpu(TypedDict, total=False):
    model: str | None
    mem_total_mb: int | None


class ComputeSessionNodeHw(TypedDict, total=False):
    """Hardware of a compute session's node, as of its start."""

    cpu: str | None
    cpu_cores: int | None
    total_memory: int | None
    """Bytes."""
    memory_speed: int | None
    memory_type: str | None
    disk: int | None
    """The rented disk, GB."""
    disk_type: Literal["nvme", "ssd", "hdd"] | None
    disk_speed_mbs: int | None
    gpu_vendor: str | None
    gpus: list[SessionGpu]
    net_down_mbps: int | None
    net_up_mbps: int | None


class RenderSessionNodeHw(TypedDict, total=False):
    cpu_cores: int | None
    total_memory: int | None
    gpus: list[SessionGpu]


class _SessionBase(TypedDict):
    uuid: str
    status: SessionStatus
    duration: int
    """Seconds since the start."""
    progress: NotRequired[str | None]
    """Current setup step, for example ``Prepare node``."""
    pull_percent: NotRequired[int | None]
    """Image pull progress, percent, while the image is being pulled."""
    started_at: NotRequired[int | None]
    """Unix milliseconds; ``None`` while starting."""
    node_number: NotRequired[NodeNumber | None]
    base_price: NotRequired[MicroUsd | None]
    """Price per hour, fixed at the start; ``None`` while starting."""
    charge_amount: NotRequired[MicroUsd]
    """What the session has cost so far."""
    app_name: NotRequired[str | None]
    app_logo: NotRequired[str | None]


class ComputeSession(_SessionBase):
    """A running compute session (``service == "compute"``)."""

    service: Literal["compute"]
    public_ip: NotRequired[str | None]
    city: NotRequired[str | None]
    country: NotRequired[str | None]
    country_iso: NotRequired[str | None]
    ports: NotRequired[dict[str, int]]
    """Container port → public port on the node."""
    urls: NotRequired[dict[str, str]]
    """HTTP port → public URL."""
    ssh: NotRequired[SessionSsh]
    fm: NotRequired[str | None]
    """Web file manager URL. It has no login: whoever has the URL has the files."""
    envs: NotRequired[UserEnvs]
    rx: NotRequired[int]
    """Bytes received."""
    tx: NotRequired[int]
    """Bytes sent."""
    storage_price: NotRequired[MicroUsd | None]
    traffic_price: NotRequired[MicroUsd | None]
    min_rent_minutes: NotRequired[int | None]
    node_hw: NotRequired[ComputeSessionNodeHw | None]


class RenderSession(_SessionBase):
    """A running render session (``service == "render"``)."""

    service: Literal["render"]
    node_hw: NotRequired[RenderSessionNodeHw | None]


class HttpProxyConfig(TypedDict):
    """What an ``http_proxy`` session connects with: the proxy and its login (HTTP Basic)."""

    ip: str
    port: int
    username: str | None
    password: str | None


class VpnSession(_SessionBase):
    """A running VPN session (``service == "vpn"``), billed by traffic."""

    service: Literal["vpn"]
    subkind: NotRequired[str | None]
    """The protocol, for example ``wg``."""
    config: NotRequired[str | HttpProxyConfig | None]
    """What the client connects with: a config file (``wg``, ``awg``), a link
    (``reality``) or the proxy and its login (``http_proxy``); ``None`` until
    ready. It is a credential: do not log it."""
    public_ip: NotRequired[str | None]
    """Exit IP address."""
    city: NotRequired[str | None]
    country: NotRequired[str | None]
    country_iso: NotRequired[str | None]
    rx: NotRequired[int]
    tx: NotRequired[int]


Session: TypeAlias = ComputeSession | RenderSession | VpnSession
"""A running session; narrow it with ``is_compute_session()`` and the like."""


class SystemLogEvent(TypedDict):
    msg: str
    """May span several lines."""
    ts: NotRequired[int | None]
    """Unix milliseconds."""


class SessionLogs(TypedDict):
    """Logs of a running compute session (``sessions.logs()``)."""

    system: list[SystemLogEvent]
    """Platform events, oldest first."""
    container: str | None
    """Latest container output; ``None`` when the node cannot be reached or there is none yet."""
    container_truncated: bool
    """The output was cut to its last 1 MiB."""


# Hosting

HostingNodeStatus: TypeAlias = Literal["idle", "rented", "verification", "benchmark", "unknown"]


class HostingNodeUsage(TypedDict):
    """Memory or disk of a hosted node, bytes."""

    size: int
    free: int
    used: int
    used_percent: float


class HostingNodePrices(TypedDict):
    base: MicroUsd
    """Per hour of rent."""
    storage: MicroUsd
    """Per GB of disk per hour."""
    traffic: MicroUsd
    """Per GB of traffic."""
    min_rent_minutes: int


class HostingNodeOffer(TypedDict):
    """Whether a node is offered for a service or a VPN protocol, and why not."""

    offered: bool
    reason: NotRequired[str | None]
    """Why not, for example ``ports_closed`` or ``vpn_probe_failed``."""
    details: NotRequired[str]


class HostingNodeService(HostingNodeOffer):
    protocols: NotRequired[dict[str, HostingNodeOffer]]
    """VPN only: the offer of each protocol."""


class HostingNodeActivity(TypedDict):
    kind: Literal["verification", "benchmark"]
    step: str
    started_at: int | None
    """Unix seconds."""


class HostingNodeSystem(TypedDict, total=False):
    cpu_cores: int | None
    cpu_model_name: str | None
    cpu_load_percent: float | None
    os_version: str | None
    memory: HostingNodeUsage | None
    disk: HostingNodeUsage | None
    gpus: list[dict[str, Any]]
    """GPUs: ``model``, ``mem_total_mb``, and clocks, temperature, fan speed,
    power draw and utilization when the node reports them."""


class HostingNodeLocation(TypedDict, total=False):
    city: str
    country: str
    latitude: float
    longitude: float


class HostingNode(TypedDict):
    """A node of your account (``hosting.nodes()``, ``hosting.get()``)."""

    number: NodeNumber
    status: HostingNodeStatus
    prices: HostingNodePrices
    system: HostingNodeSystem
    location: HostingNodeLocation
    activity: NotRequired[HostingNodeActivity | None]
    """A verification or benchmark in progress."""
    maintenance: NotRequired[bool]
    """In maintenance: not offered for rent."""
    verified: NotRequired[bool | None]
    services: NotRequired[dict[str, HostingNodeService] | None]
    """For which services the node is offered, and why not."""
    ip: NotRequired[str | None]
    osn: NotRequired[str | None]
    """Version of the node software."""
    online_at: NotRequired[str | None]
    """Online since, ISO 8601."""
    uptime: NotRequired[int | None]
    """Seconds since the machine booted."""
    uptime_percent: NotRequired[float | None]
    """Online share over 30 days; 97 and above are reported as 100."""


# Network


class NetworkNodes(TypedDict):
    online: int
    available: int
    rented: int
    countries: int


class NetworkPower(TypedDict):
    cpu_cores: int
    disk: int
    gpus: int
    memory: int
    tflops: float
    gpus_rented: NotRequired[int | None]


class NetworkFramesWeek(TypedDict):
    week: str
    """ISO date, ``YYYY-MM-DD``."""
    frames: int


class NetworkRender(TypedDict):
    frames_24h: int
    frames_total: int
    frames_by_week: list[NetworkFramesWeek]


class NetworkSessions(TypedDict):
    running: int
    total: int
    last_24h: int


class NetworkUsers(TypedDict):
    total: int
    last_24h: int


class NetworkVpn(TypedDict):
    nodes: int
    countries: int


class NetworkInfo(TypedDict):
    """Platform statistics now (``network.info()``)."""

    at: int
    """Unix seconds."""
    nodes: NetworkNodes
    power: NetworkPower
    render: NetworkRender
    sessions: NetworkSessions
    users: NetworkUsers
    vpn: NetworkVpn


class NetworkHistory(TypedDict):
    """Platform statistics over time as parallel lists, one value per timestamp."""

    timestamps: list[int]
    """Start of each step, Unix seconds. Steps without data are left out."""
    nodes_online: list[float | None]
    gpus: list[float | None]
    gpus_rented: list[float | None]
    tflops: list[float | None]
    sessions_running: list[float | None]
    nodes_available: NotRequired[list[float | None]]
    nodes_rented: NotRequired[list[float | None]]
    countries: NotRequired[list[float | None]]
    vpn_nodes: NotRequired[list[float | None]]
    users: NotRequired[list[float | None]]
    sessions_24h: NotRequired[list[float | None]]


class NetworkHistoryPoint(TypedDict):
    """One point of the network history: averages over the step, so they can be fractional."""

    ts: int
    nodes_online: float | None
    nodes_available: float | None
    nodes_rented: float | None
    countries: float | None
    gpus: float | None
    gpus_rented: float | None
    tflops: float | None
    vpn_nodes: float | None
    users: float | None
    sessions_running: float | None
    sessions_24h: float | None


# Stats

GpuVerifiedFilter: TypeAlias = Literal["all", "yes", "no"]
MiningRole: TypeAlias = Literal["gpu", "cpu"]


class GpuPricePercentiles(TypedDict):
    """Price percentiles, micro-USD per GPU-hour; ``None`` when there is no price."""

    p10: MicroUsd | None
    p25: MicroUsd | None
    p50: MicroUsd | None
    p75: MicroUsd | None
    p90: MicroUsd | None


class GpuModelStats(TypedDict):
    """Market state of one GPU model. Counts are GPUs, not nodes."""

    model: str
    total: int
    available: int
    rented: int
    usage: float
    """Rented share now, percent."""
    ai_score: int
    available_price: GpuPricePercentiles
    rented_price: GpuPricePercentiles
    usage_30d: NotRequired[float | None]
    memory_mb: NotRequired[int | None]
    """Video memory of one GPU, MiB: the size most GPUs of the model have."""
    tflops: NotRequired[float | None]
    tflops_per_dollar: NotRequired[float | None]


class GpuCurrent(TypedDict):
    at: int | None
    """Unix seconds."""
    gpus: list[GpuModelStats]


class GpuPriceSeries(TypedDict):
    p10: list[MicroUsd | None]
    p25: list[MicroUsd | None]
    p50: list[MicroUsd | None]
    p75: list[MicroUsd | None]
    p90: list[MicroUsd | None]


class GpuSupplyDemand(TypedDict):
    total: list[int]
    available: list[int]
    rented: list[int]


class GpuModelHistory(TypedDict):
    """History of one GPU model as parallel lists, one value per timestamp."""

    timestamps: list[int]
    """Unix seconds."""
    supply_demand: GpuSupplyDemand
    available_price: GpuPriceSeries
    rented_price: GpuPriceSeries
    tflops: NotRequired[float | None]


GpuHistory: TypeAlias = dict[str, GpuModelHistory]
"""GPU market history by model name."""


class GpuHistoryPoint(TypedDict):
    ts: int
    total: int | None
    available: int | None
    rented: int | None
    available_price: GpuPricePercentiles
    rented_price: GpuPricePercentiles


class GpuLocation(TypedDict):
    """GPUs of one model in one city."""

    city: str
    country: str
    model: str
    gpus: int
    rented: int
    verified: int
    latitude: NotRequired[float | None]
    longitude: NotRequired[float | None]


class MiningUsageRow(TypedDict):
    name: str
    """Catalogue name, or ``other``."""
    label: str | None
    started: int
    """Sessions that started with it, or restarted into it."""
    hours: float
    gpu_hours: float
    """Hours times GPUs; 0 for the CPU role."""


class MiningPoolRow(MiningUsageRow):
    coins: list[str]


class MiningTotal(TypedDict):
    started: int
    hours: float
    gpu_hours: float


class MiningDaily(TypedDict):
    dates: list[str]
    miners: dict[str, list[float]]
    """A value of ``measure`` per date, by miner name."""


# "from" is a Python keyword, so this part is declared with the functional syntax.
_MiningPeriod = TypedDict("_MiningPeriod", {"from": str, "to": str})


class MiningUsage(_MiningPeriod):
    """Mining sessions of the platform over the last days, most used first.

    ``from`` and ``to`` are ISO dates (``YYYY-MM-DD``).
    """

    role: MiningRole
    days: int
    measure: Literal["gpu_hours", "hours"]
    total: MiningTotal
    miners: list[MiningUsageRow]
    algorithms: list[MiningUsageRow]
    pools: list[MiningPoolRow]
    daily: MiningDaily
    at: NotRequired[int | None]


__all__ = [
    "AccountBalance",
    "BatchFailure",
    "BatchId",
    "BatchResult",
    "BatchSuccess",
    "ComputeApp",
    "ComputeAppExtra",
    "ComputeBatchItem",
    "ComputeMachine",
    "ComputeSession",
    "ComputeSessionNodeHw",
    "GpuCurrent",
    "GpuHistory",
    "GpuHistoryPoint",
    "GpuLocation",
    "GpuModelHistory",
    "GpuModelStats",
    "GpuPricePercentiles",
    "GpuPriceSeries",
    "GpuSupplyDemand",
    "GpuVerifiedFilter",
    "HostingNode",
    "HostingNodeActivity",
    "HostingNodeLocation",
    "HostingNodeOffer",
    "HostingNodePrices",
    "HostingNodeService",
    "HostingNodeStatus",
    "HostingNodeSystem",
    "HostingNodeUsage",
    "HttpProxyConfig",
    "MachineGpu",
    "MicroUsd",
    "MiningDaily",
    "MiningPoolRow",
    "MiningRole",
    "MiningTotal",
    "MiningUsage",
    "MiningUsageRow",
    "NetworkFramesWeek",
    "NetworkHistory",
    "NetworkHistoryPoint",
    "NetworkInfo",
    "NetworkNodes",
    "NetworkPower",
    "NetworkRender",
    "NetworkSessions",
    "NetworkUsers",
    "NetworkVpn",
    "NodeNumber",
    "Reliability",
    "RenderBatchItem",
    "RenderMachine",
    "RenderSession",
    "RenderSessionNodeHw",
    "Session",
    "SessionGpu",
    "SessionLogs",
    "SessionSsh",
    "SessionStatus",
    "SshEndpoint",
    "StartResult",
    "SystemLogEvent",
    "UserEnvs",
    "VpnMachine",
    "VpnProtocol",
    "VpnSession",
]
