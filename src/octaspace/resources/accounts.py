from __future__ import annotations

from typing import cast

from ..types import AccountBalance
from .base import Resource


class AccountsResource(Resource):
    """The account the API key belongs to."""

    def balance(self) -> AccountBalance:
        """Return the account balance (``GET /accounts/balance``).

        ``balance`` is in micro-USD; format it with ``octaspace.format_usd()``.
        It already includes what running sessions have used and can be
        negative. Also a quick way to check that an API key works.
        """
        return cast(AccountBalance, self._request("GET", "/accounts/balance"))
