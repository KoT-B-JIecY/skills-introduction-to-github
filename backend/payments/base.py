"""Common base classes for payment providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class PaymentProviderError(Exception):
    """Raised when communication with provider fails."""


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    name: str

    @abstractmethod
    async def create_invoice(self, amount: float, currency: str, order_id: int) -> Dict[str, Any]:
        """Create invoice and return provider-specific data (address, amount to pay, id, etc.)."""

    @abstractmethod
    async def parse_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse webhook payload and return dict with keys: payment_id, status, tx_hash(optional), amount, currency"""