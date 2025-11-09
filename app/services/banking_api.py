from typing import Any

import httpx


class BankingAPIClient:
    """Async client for Open API."""

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def create_consent(
        self,
        access_token: str,
        client_id: str,
        permissions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create consent for accessing client data.

        Args:
            access_token: Bank token
            client_id: Test client ID
            permissions: List of permissions to request

        Returns:
            Response with consentId
        """
        url = f"{self.base_url}/account-consents/request"

        if permissions is None:
            permissions = [
                "ReadAccountsDetail",
                "ReadBalances",
                "ReadTransactionsDetail",
            ]

        payload = {
            "client_id": client_id,
            "permissions": permissions,
            "reason": "Multibank aggregation",
            "requesting_bank": self.client_id,
            "requesting_bank_name": f"{self.client_id} Aggregator",
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requesting-Bank": self.client_id,
        }

        try:
            client = await self._get_client()
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "status_code": e.response.status_code,
                "response": e.response.text,
            }
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}

    async def get_accounts(
        self,
        access_token: str,
        client_id: str,
        consent_id: str,
    ) -> dict[str, Any]:
        """
        Get accounts for a client using consent.

        Args:
            access_token: Bank token
            client_id: Test client ID
            consent_id: Consent ID from create_consent()

        Returns:
            Response with account data
        """
        url = f"{self.base_url}/accounts"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-Requesting-Bank": self.client_id,
            "X-Consent-Id": consent_id,
        }

        params = {
            "client_id": client_id,
        }

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "status_code": e.response.status_code,
                "response": e.response.text,
            }
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}

    async def get_balances(
        self,
        access_token: str,
        account_id: str,
        client_id: str,
        consent_id: str,
    ) -> dict[str, Any]:
        """
        Get balances for a specific account.

        Args:
            access_token: Bank token
            account_id: Account ID from get_accounts()
            client_id: Test client ID
            consent_id: Consent ID

        Returns:
            Response with balance data
        """
        url = f"{self.base_url}/accounts/{account_id}/balances"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-Requesting-Bank": self.client_id,
            "X-Consent-Id": consent_id,
        }

        params = {
            "client_id": client_id,
        }

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "status_code": e.response.status_code,
                "response": e.response.text,
            }
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}

    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        client_id: str,
        consent_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Get transactions for a specific account.

        Args:
            access_token: Bank token
            account_id: Account ID
            client_id: Test client ID
            consent_id: Consent ID
            from_date: Optional start date (ISO format)
            to_date: Optional end date (ISO format)

        Returns:
            Response with transaction data
        """
        url = f"{self.base_url}/accounts/{account_id}/transactions"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-Requesting-Bank": self.client_id,
            "X-Consent-Id": consent_id,
        }

        params = {
            "client_id": client_id,
        }

        if from_date:
            params["fromBookingDateTime"] = from_date
        if to_date:
            params["toBookingDateTime"] = to_date

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "status_code": e.response.status_code,
                "response": e.response.text,
            }
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}


_banking_api_client: BankingAPIClient | None = None


def init_banking_api_client(base_url: str, client_id: str, client_secret: str) -> None:
    """Initialize the global banking API client."""
    global _banking_api_client
    _banking_api_client = BankingAPIClient(base_url, client_id, client_secret)


def get_banking_api_client() -> BankingAPIClient:
    """
    Get the initialized banking API client.

    Raises:
        RuntimeError: If client not initialized
    """
    if _banking_api_client is None:
        raise RuntimeError(
            "Banking API client not initialized. Call init_banking_api_client() first."
        )
    return _banking_api_client


async def close_banking_api_client() -> None:
    """Close the banking API client."""
    if _banking_api_client is not None:
        await _banking_api_client.close()
