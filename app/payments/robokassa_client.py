from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
from urllib.parse import urlencode

from app.config import Settings

ROBOKASSA_FORM_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"


def _format_amount(value: Decimal | float | str) -> str:
    if isinstance(value, Decimal):
        return format(value.quantize(Decimal("0.01")))
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


@dataclass(slots=True)
class RobokassaPaymentRequest:
    url: str
    signature: str


class RobokassaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = ROBOKASSA_FORM_URL
        self.algo = settings.robokassa_signature_algo.lower()

    def build_payment_url(
        self,
        inv_id: int,
        amount: Decimal | float | str,
        description: str,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> RobokassaPaymentRequest:
        out_sum = _format_amount(amount)
        params: Dict[str, str] = {
            "MerchantLogin": self.settings.robokassa_merchant_login or "",
            "OutSum": out_sum,
            "InvId": str(inv_id),
            "Description": description,
            "IsTest": "1" if self.settings.robokassa_is_test else "0",
            "Culture": self.settings.robokassa_culture,
        }
        if extra_params:
            params.update(extra_params)
        signature = self._build_signature(out_sum, str(inv_id), self.settings.robokassa_password1 or "", params, include_login=True)
        params["SignatureValue"] = signature
        return RobokassaPaymentRequest(url=f"{self.base_url}?{urlencode(params)}", signature=signature)

    def verify_success(self, params: Dict[str, str]) -> bool:
        return self._verify(params, self.settings.robokassa_password1 or "", include_login=False)

    def verify_result(self, params: Dict[str, str]) -> bool:
        return self._verify(params, self.settings.robokassa_password2 or "", include_login=False)

    def _verify(self, params: Dict[str, str], password: str, include_login: bool) -> bool:
        signature = params.get("SignatureValue", "").upper()
        out_sum = params.get("OutSum") or ""
        inv_id = params.get("InvId") or ""
        expected = self._build_signature(out_sum, inv_id, password, params, include_login)
        return signature == expected

    def _build_signature(
        self,
        out_sum: str,
        inv_id: str,
        password: str,
        params: Dict[str, str],
        include_login: bool,
    ) -> str:
        parts = []
        if include_login:
            parts.append(self.settings.robokassa_merchant_login or "")
        parts.extend([out_sum, inv_id, password])
        for key, value in sorted(self._collect_shp(params).items()):
            parts.append(f"{key}={value}")
        payload = ":".join(parts)
        digest = hashlib.new(self.algo, payload.encode("utf-8")).hexdigest()
        return digest.upper()

    def _collect_shp(self, params: Dict[str, str]) -> Dict[str, str]:
        return {k: v for k, v in params.items() if k.startswith("Shp_")}


__all__ = ["RobokassaClient", "RobokassaPaymentRequest"]
