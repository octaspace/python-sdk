from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypedDict

from ...response import APIResponse
from ..base import Resource


class _MachineRentalRequiredPayload(TypedDict):
    node_id: int
    disk_size: int
    image: str


class MachineRentalCreatePayload(_MachineRentalRequiredPayload, total=False):
    app: str
    envs: dict[str, str]
    ports: list[int]
    http_ports: list[int]
    start_command: str
    entrypoint: str


class MachineRentalResource(Resource):
    """Machines for rent, to run your own container."""

    def list(self, **params: Any) -> APIResponse:
        """List the machines available for rent.

        ``GET /services/mr``. Works without an API token.
        """
        return self.get("/services/mr", params=params or None)

    def create(
        self,
        *,
        node_id: int,
        disk_size: int,
        image: str,
        app: str = "",
        envs: dict[str, str] | None = None,
        ports: Sequence[int] | None = None,
        http_ports: Sequence[int] | None = None,
        start_command: str = "",
        entrypoint: str = "",
    ) -> APIResponse:
        """Start a machine rental session.

        ``POST /services/mr``. Never retried.

        Args:
            node_id: The machine to rent.
            disk_size: Disk to allocate, in GB.
            image: The container image, for example ``"ubuntu:24.04"``.
            app: UUID of an application from ``apps.list()``.
            envs: Environment variables of the container.
            ports: TCP/UDP ports to expose.
            http_ports: HTTP ports to expose as HTTPS links.
            start_command: Shell commands to run after the container starts.
            entrypoint: The container entrypoint.

        Returns:
            The response; ``data["uuid"]`` is the session UUID.

        Raises:
            APIError: Status 400 when the session cannot be started, for
                example for an insufficient balance.
        """
        payload: MachineRentalCreatePayload = {
            "node_id": node_id,
            "disk_size": disk_size,
            "image": image,
            "app": app,
            "envs": dict(envs or {}),
            "ports": list(ports or []),
            "http_ports": list(http_ports or []),
            "start_command": start_command,
            "entrypoint": entrypoint,
        }
        # The endpoint takes a list of sessions to start; this starts one.
        item = {"id": 0, **payload}
        return self.post("/services/mr", body=[item])
