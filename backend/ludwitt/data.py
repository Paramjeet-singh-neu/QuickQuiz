"""Ludwitt hosted-data CRUD client."""

from __future__ import annotations

from typing import Any, Dict, Optional

from config import AppConfig
from backend.ludwitt.client import LudwittHTTPClient


class LudwittDataClient(LudwittHTTPClient):
    def put_document(
        self,
        access_token: str,
        collection: str,
        doc_id: str,
        data: Dict[str, Any],
        *,
        if_match: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"If-Match": f'"{if_match}"'} if if_match else None
        response = self.request(
            "PUT",
            f"/api/v1/data/{collection}/{doc_id}",
            access_token=access_token,
            json_body={"data": data},
            headers=headers,
        )
        return response.json()

    def get_document(
        self,
        access_token: str,
        collection: str,
        doc_id: str,
    ) -> Dict[str, Any]:
        response = self.request(
            "GET",
            f"/api/v1/data/{collection}/{doc_id}",
            access_token=access_token,
        )
        return response.json()

    def delete_document(
        self,
        access_token: str,
        collection: str,
        doc_id: str,
    ) -> Dict[str, Any]:
        response = self.request(
            "DELETE",
            f"/api/v1/data/{collection}/{doc_id}",
            access_token=access_token,
        )
        return response.json()

    def list_documents(
        self,
        access_token: str,
        collection: str,
        *,
        limit: int = 50,
        cursor: Optional[str] = None,
        where: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if where:
            params["where"] = where
        if order_by:
            params["orderBy"] = order_by

        response = self.request(
            "GET",
            f"/api/v1/data/{collection}",
            access_token=access_token,
            params=params,
        )
        return response.json()

    def usage(self, access_token: str) -> Dict[str, Any]:
        response = self.request(
            "GET",
            "/api/v1/data/_meta/usage",
            access_token=access_token,
        )
        return response.json()
