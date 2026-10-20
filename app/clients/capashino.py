from urllib.parse import urljoin

import httpx

from app.config import settings


class CapashinoClient:
    def __init__(self) -> None:
        self.base_url = settings.capashino_url.rstrip("/")
        self.api_key = settings.capashino_api_key

    async def send_notification(
        self,
        message: str,
        reference_id: str,
        idempotency_key: str,
    ) -> None:
        url = urljoin(
            f"{self.base_url.rstrip('/')}/",
            "api/notifications",
        )

        headers = {
            "X-API-Key": self.api_key,
        }

        payload = {
            "message": message,
            "reference_id": reference_id,
            "idempotency_key": idempotency_key,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
