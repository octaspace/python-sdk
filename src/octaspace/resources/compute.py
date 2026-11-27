from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any, cast

from .. import _normalize
from ..types import (
    BatchResult,
    ComputeApp,
    ComputeBatchItem,
    ComputeMachine,
    StartResult,
    UserEnvs,
)
from .base import Resource, pick, segment, with_batch_ids

_RESTART_FIELDS = (
    "disk_size",
    "envs",
    "ports",
    "http_ports",
    "entrypoint",
    "args",
    "ssh",
    "fm",
    "startup_script",
)
_START_FIELDS = ("node_number", "image", "app", *_RESTART_FIELDS)


class ComputeResource(Resource):
    """Compute machines and apps: list, start (one or several) and restart."""

    def list(self) -> list[ComputeMachine]:
        """Return the machines available for rent (``GET /services/compute``).

        Works without an API key, but is then refreshed about once an hour;
        with a key it is at most 10 seconds old.
        """
        data = self._request("GET", "/services/compute", auth="optional")
        return cast("list[ComputeMachine]", _normalize.machines(data))

    def apps(self) -> builtins.list[ComputeApp]:
        """Return the apps to start a session from (``GET /compute/apps``).

        The official apps and, with an API key, your own (``personal`` is
        ``True``), which also carry ``startup_script`` and ``envs``.
        """
        data = self._request("GET", "/compute/apps", auth="optional")
        return cast("builtins.list[ComputeApp]", _normalize.apps(data))

    def start(
        self,
        node_number: str,
        image: str,
        *,
        app: str | None = None,
        disk_size: int | None = None,
        envs: UserEnvs | None = None,
        ports: Sequence[int] | None = None,
        http_ports: Sequence[int] | None = None,
        entrypoint: str | None = None,
        args: str | None = None,
        ssh: bool | None = None,
        fm: bool | None = None,
        startup_script: str | None = None,
    ) -> StartResult:
        """Start a compute session (``POST /services/compute``).

        Returns as soon as the session is created; wait for it with
        ``sessions.wait_ready()``. Never retried automatically: a start costs
        money. Arguments left as ``None`` are not sent and take their defaults.

        Args:
            node_number: The machine, from ``list()``.
            image: Docker image, for example ``"ubuntu:24.04"``; up to 512 bytes.
            app: UUID of an app from ``apps()``.
            disk_size: Disk size, GB; 1 by default.
            envs: Environment variables: up to 64; names of letters, digits
                and ``_``, not starting with a digit; values up to 4 KiB.
            ports: TCP/UDP container ports to expose; 0 and 22 are ignored
                (SSH is always exposed).
            http_ports: HTTP container ports to expose with a public URL, up
                to 10; 7681 and 7682 are reserved.
            entrypoint: Replaces the image's ENTRYPOINT and drops its CMD; one
                line up to 4 KiB, split like a shell command line, but nothing
                is expanded: use ``sh -c '…'`` for ``$VAR``, ``*`` or ``&&``.
            args: Replaces the image's CMD; one line up to 4 KiB.
            ssh: Web terminal and SSH access. ``None``: the app's setting, off
                without an app; ``False`` turns off what the app enables.
            fm: Web file manager. It has no login: anyone with its URL has
                the files. ``None``: the app's setting, off without an app.
            startup_script: Script run as root once the container is up, up
                to 64 KiB; its output goes to ``/var/log/onstart.log``.

        Raises:
            ValidationError: The request was rejected, for example
                ``Insufficient balance`` or ``Node not available``.
        """
        body = pick(
            {
                "node_number": node_number,
                "image": image,
                "app": app,
                "disk_size": disk_size,
                "envs": envs,
                "ports": _list(ports),
                "http_ports": _list(http_ports),
                "entrypoint": entrypoint,
                "args": args,
                "ssh": ssh,
                "fm": fm,
                "startup_script": startup_script,
            },
            _START_FIELDS,
            "compute.start()",
        )
        return cast(StartResult, self._request("POST", "/services/compute", body=body))

    def start_batch(self, items: Sequence[ComputeBatchItem]) -> builtins.list[BatchResult]:
        """Start several compute sessions at once (``POST /services/compute``).

        Each item takes the arguments of ``start()`` and an optional ``id``.
        Items are checked one by one: one that fails does not stop the others.
        Results come in the order of the items.

        Raises:
            TypeError: Two items have the same ``id``, or an item has an
                unknown field. Nothing is sent.
        """
        body = [
            {"id": item["id"], **pick(_without_id(item), _START_FIELDS, "compute.start_batch()")}
            for item in with_batch_ids(cast("Sequence[Mapping[str, Any]]", items))
        ]
        return cast(
            "builtins.list[BatchResult]", self._request("POST", "/services/compute", body=body)
        )

    def restart(
        self,
        uuid: str,
        *,
        disk_size: int | None = None,
        envs: UserEnvs | None = None,
        ports: Sequence[int] | None = None,
        http_ports: Sequence[int] | None = None,
        entrypoint: str | None = None,
        args: str | None = None,
        ssh: bool | None = None,
        fm: bool | None = None,
        startup_script: str | None = None,
    ) -> StartResult:
        """Recreate the session's container on the same node.

        ``POST /services/compute/{uuid}/restart``. The session keeps its
        ``uuid``, rent and prices; follow the restart with ``sessions.get()``.
        If the new parameters cannot be applied, the session stops.

        Without arguments the session restarts with the parameters it was
        started with. **Arguments you pass replace all of them**: every one
        you leave out takes its default (``disk_size`` 1 GB; no ``envs``,
        ports or ``startup_script``; the image's own ``entrypoint`` and
        ``args``; ``ssh`` and ``fm`` as the app sets them). The node, image
        and app cannot be changed. Never retried automatically.

        Raises:
            ConflictError: The session is already starting or restarting.
            RateLimitError: The session was restarted too recently: it can be
                restarted once in 5 minutes and 6 times an hour;
                ``retry_after`` says how long to wait.
        """
        body = pick(
            {
                "disk_size": disk_size,
                "envs": envs,
                "ports": _list(ports),
                "http_ports": _list(http_ports),
                "entrypoint": entrypoint,
                "args": args,
                "ssh": ssh,
                "fm": fm,
                "startup_script": startup_script,
            },
            _RESTART_FIELDS,
            "compute.restart()",
        )
        data = self._request(
            "POST", f"/services/compute/{segment(uuid)}/restart", body=body or None
        )
        return cast(StartResult, data) if data else {"uuid": uuid}


def _list(values: Sequence[int] | None) -> list[int] | None:
    return list(values) if values is not None else None


def _without_id(item: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "id"}
