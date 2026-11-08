from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class AccountsResource(Resource):
    """Your OctaSpace account: profile, balance and deposit wallet."""

    def profile(self) -> APIResponse:
        """Return the account profile.

        ``GET /accounts``. The data includes ``account_uuid``, ``email``, ``uid``,
        ``wallet`` and ``balance`` (in Wei).
        """
        return self.get("/accounts")

    def balance(self) -> APIResponse:
        """Return the account balance.

        ``GET /accounts/balance``. ``data["balance"]`` is an integer in Wei;
        1 OCTA is 10**18 Wei.
        """
        return self.get("/accounts/balance")

    def generate_wallet(self) -> APIResponse:
        """Generate the deposit wallet of the account.

        ``POST /accounts``. ``data["address"]`` is the wallet address.
        """
        return self.post("/accounts")
