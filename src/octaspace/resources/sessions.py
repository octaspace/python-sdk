from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeGuard, TypeVar, cast

from ..errors import NotFoundError, SessionStoppedError, WaitTimeoutError
from ..types import ComputeSession, RenderSession, Session, SessionLogs, StartResult, VpnSession
from .base import Resource, segment

DEFAULT_WAIT_INTERVAL = 3.0

_T = TypeVar("_T")


def is_compute_session(session: Session) -> TypeGuard[ComputeSession]:
    """Whether a session is a compute session."""
    return session.get("service") == "compute"


def is_render_session(session: Session) -> TypeGuard[RenderSession]:
    """Whether a session is a render session."""
    return session.get("service") == "render"


def is_vpn_session(session: Session) -> TypeGuard[VpnSession]:
    """Whether a session is a VPN session."""
    return session.get("service") == "vpn"


class SessionsResource(Resource):
    """Your running sessions: compute, render and VPN.

    Once a session has stopped, ``get()``, ``logs()`` and ``stop()`` raise
    ``NotFoundError``.
    """

    def list(self) -> list[Session]:
        """Return your running sessions, oldest first (``GET /sessions``)."""
        return cast("list[Session]", self._request("GET", "/sessions"))

    def get(self, uuid: str) -> Session:
        """Return a running session (``GET /services/{uuid}/info``).

        Raises:
            NotFoundError: The session has stopped or never existed.
            ValidationError: The UUID is malformed.
        """
        return cast(Session, self._request("GET", f"/services/{segment(uuid)}/info"))

    def logs(self, uuid: str, *, tail: int | None = None) -> SessionLogs:
        """Return the system log and latest container output of a compute session.

        ``GET /services/{uuid}/logs``. Render and VPN sessions have no logs.

        Args:
            uuid: The session.
            tail: Number of latest container lines, 1 to 1000 (200 by default).

        Raises:
            NotFoundError: The session has stopped, or is a render or VPN session.
        """
        params = {"tail": tail}
        return cast(
            SessionLogs, self._request("GET", f"/services/{segment(uuid)}/logs", params=params)
        )

    def stop(self, uuid: str) -> StartResult:
        """Stop a session (``POST /services/{uuid}/stop``).

        Stopping takes a few seconds; use ``wait_stopped()`` to wait until the
        session is gone. Stopping twice is safe, so the call is retried like a
        GET. A session stopped before its minimum rent (``min_rent_minutes``)
        is charged as if it ran that long.
        """
        data = self._request("POST", f"/services/{segment(uuid)}/stop", idempotent=True)
        return cast(StartResult, data) if data else {"uuid": uuid}

    def wait_ready(
        self,
        uuid: str,
        *,
        interval: float = DEFAULT_WAIT_INTERVAL,
        timeout: float | None = None,
        on_progress: Callable[[Session], Any] | None = None,
    ) -> Session:
        """Poll a session until its ``status`` is ``ready`` and return it.

        After ``compute.restart()`` the session can still report ``ready`` for
        a moment: to see the restart finish, wait until it leaves ``ready``
        first.

        Args:
            uuid: The session.
            interval: Seconds between checks; keep it at 2 or more to stay
                within the rate limit.
            timeout: Give up after this many seconds; wait forever by default.
            on_progress: Called with the session after each check, for
                example to show ``progress`` and ``pull_percent``.

        Raises:
            SessionStoppedError: The session stopped while it was starting,
                for example because SSH could not be set up.
            WaitTimeoutError: ``timeout`` passed.
        """

        def check() -> Session | None:
            try:
                session = self.get(uuid)
            except NotFoundError as exc:
                raise SessionStoppedError(
                    f"Session {uuid} stopped before it became ready: {exc.message}",
                    response=exc.response,
                ) from exc
            if on_progress is not None:
                on_progress(session)
            return session if session.get("status") == "ready" else None

        return cast(Session, _poll(check, interval, timeout))

    def wait_stopped(
        self,
        uuid: str,
        *,
        interval: float = DEFAULT_WAIT_INTERVAL,
        timeout: float | None = None,
    ) -> None:
        """Poll a session until it is gone; return at once if it already is.

        Raises:
            WaitTimeoutError: ``timeout`` passed.
        """

        def check() -> bool | None:
            try:
                self.get(uuid)
            except NotFoundError:
                return True
            return None

        _poll(check, interval, timeout)


def _poll(check: Callable[[], _T | None], interval: float, timeout: float | None) -> _T:
    deadline = time.monotonic() + timeout if timeout is not None else None
    while True:
        result = check()
        if result is not None:
            return result
        if deadline is not None and time.monotonic() + interval > deadline:
            raise WaitTimeoutError(f"Gave up waiting after {timeout} seconds")
        time.sleep(interval)
