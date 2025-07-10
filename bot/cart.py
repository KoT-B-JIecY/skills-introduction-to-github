"""Very simple in-memory cart mapping per Telegram user id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CartItem:
    product_id: int
    uc_amount: int
    price_usd: float
    qty: int = 1

    @property
    def total(self) -> float:
        return self.price_usd * self.qty


_cart: Dict[int, CartItem] = {}


def set_cart(user_id: int, item: CartItem) -> None:
    _cart[user_id] = item


def get_cart(user_id: int) -> Optional[CartItem]:
    return _cart.get(user_id)


def clear_cart(user_id: int) -> None:
    _cart.pop(user_id, None)