"""
Order Service - Бизнес-логика для работы с заказами
"""
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.orm import selectinload

from database.models import Order, OrderItem, UCProduct, OrderStatus, User
from config.settings import UC_PRODUCTS
from utils.logger import logger


class OrderService:
    """Сервис для работы с заказами"""
    
    async def create_order(
        self,
        session: AsyncSession,
        user_id: int,
        uc_amount: int,
        price: float,
        pubg_id: str,
        pubg_nickname: str,
        currency: str = "USD"
    ) -> Order:
        """Создать новый заказ"""
        try:
            # Ищем соответствующий продукт
            product_info = None
            for product in UC_PRODUCTS:
                if product["amount"] == uc_amount and product["price"] == price:
                    product_info = product
                    break
            
            if not product_info:
                raise ValueError(f"Product not found: {uc_amount} UC for ${price}")
            
            # Создаем заказ
            order = Order(
                user_id=user_id,
                pubg_id=pubg_id,
                pubg_nickname=pubg_nickname,
                total_amount=Decimal(str(price)),
                currency=currency,
                final_amount=Decimal(str(price)),
                status=OrderStatus.PENDING
            )
            
            session.add(order)
            await session.flush()  # Получаем ID заказа
            
            # Создаем элемент заказа
            order_item = OrderItem(
                order_id=order.id,
                product_id=None,  # У нас пока нет продуктов в БД
                quantity=1,
                unit_price=Decimal(str(price)),
                total_price=Decimal(str(price)),
                uc_amount=uc_amount,
                bonus_uc_amount=product_info.get("bonus", 0)
            )
            
            session.add(order_item)
            await session.commit()
            await session.refresh(order)
            
            logger.info(f"Created order {order.id} for user {user_id}: {uc_amount} UC")
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            await session.rollback()
            raise
    
    async def get_order_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def get_order_by_uuid(self, session: AsyncSession, order_uuid: str) -> Optional[Order]:
        """Получить заказ по UUID"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.uuid == order_uuid)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting order by UUID {order_uuid}: {e}")
            return None
    
    async def update_order_status(
        self,
        session: AsyncSession,
        order_id: int,
        status: OrderStatus,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Обновить статус заказа"""
        try:
            update_data = {"status": status}
            
            if admin_notes:
                update_data["admin_notes"] = admin_notes
            
            # Устанавливаем время оплаты или доставки
            if status == OrderStatus.PAID:
                update_data["paid_at"] = datetime.now(timezone.utc)
            elif status == OrderStatus.DELIVERED:
                update_data["delivered_at"] = datetime.now(timezone.utc)
            
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(**update_data)
            )
            await session.commit()
            
            logger.info(f"Order {order_id} status updated to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            await session.rollback()
            return False
    
    async def set_delivery_code(
        self,
        session: AsyncSession,
        order_id: int,
        delivery_code: str
    ) -> bool:
        """Установить код доставки UC"""
        try:
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(
                    delivery_code=delivery_code,
                    delivery_status="completed",
                    status=OrderStatus.DELIVERED,
                    delivered_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
            
            logger.info(f"Delivery code set for order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting delivery code: {e}")
            await session.rollback()
            return False
    
    async def cancel_order(
        self,
        session: AsyncSession,
        order_id: int,
        reason: str = ""
    ) -> bool:
        """Отменить заказ"""
        try:
            order = await self.get_order_by_id(session, order_id)
            if not order:
                return False
            
            # Можно отменить только ожидающие или обрабатывающиеся заказы
            if order.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
                return False
            
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(
                    status=OrderStatus.CANCELLED,
                    admin_notes=reason
                )
            )
            await session.commit()
            
            logger.info(f"Order {order_id} cancelled. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            await session.rollback()
            return False
    
    async def get_user_orders(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Order]:
        """Получить заказы пользователя"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.user_id == user_id)
                .order_by(desc(Order.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []
    
    async def get_orders_by_status(
        self,
        session: AsyncSession,
        status: OrderStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Получить заказы по статусу"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items), selectinload(Order.user))
                .where(Order.status == status)
                .order_by(desc(Order.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting orders by status: {e}")
            return []
    
    async def get_pending_orders(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[Order]:
        """Получить ожидающие заказы"""
        return await self.get_orders_by_status(session, OrderStatus.PENDING, limit)
    
    async def get_paid_orders(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[Order]:
        """Получить оплаченные заказы, ожидающие доставки"""
        return await self.get_orders_by_status(session, OrderStatus.PAID, limit)
    
    async def search_orders(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 50
    ) -> List[Order]:
        """Поиск заказов"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items), selectinload(Order.user))
                .where(
                    or_(
                        Order.pubg_id.ilike(f"%{query}%"),
                        Order.pubg_nickname.ilike(f"%{query}%"),
                        Order.uuid.cast(str).ilike(f"%{query}%")
                    )
                )
                .order_by(desc(Order.created_at))
                .limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            return []
    
    async def get_order_statistics(
        self,
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Получить статистику заказов"""
        try:
            from sqlalchemy import func
            from datetime import timedelta
            
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Общее количество заказов
            total_orders_result = await session.execute(
                select(func.count(Order.id))
                .where(Order.created_at >= since_date)
            )
            total_orders = total_orders_result.scalar() or 0
            
            # Общий доход
            total_revenue_result = await session.execute(
                select(func.sum(Order.final_amount))
                .where(
                    and_(
                        Order.created_at >= since_date,
                        Order.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED])
                    )
                )
            )
            total_revenue = total_revenue_result.scalar() or 0
            
            # Статистика по статусам
            status_stats = {}
            for status in OrderStatus:
                result = await session.execute(
                    select(func.count(Order.id))
                    .where(
                        and_(
                            Order.created_at >= since_date,
                            Order.status == status
                        )
                    )
                )
                status_stats[status.value] = result.scalar() or 0
            
            return {
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "status_stats": status_stats,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {}
    
    async def apply_promo_code(
        self,
        session: AsyncSession,
        order_id: int,
        promo_code: str
    ) -> Dict[str, Any]:
        """Применить промокод к заказу"""
        try:
            from database.models import PromoCode, PromoCodeUse, PromoCodeType
            
            # Получаем заказ
            order = await self.get_order_by_id(session, order_id)
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Получаем промокод
            promo_result = await session.execute(
                select(PromoCode).where(PromoCode.code == promo_code.upper())
            )
            promo = promo_result.scalar_one_or_none()
            
            if not promo:
                return {"success": False, "error": "Promo code not found"}
            
            if not promo.is_valid():
                return {"success": False, "error": "Promo code is not valid"}
            
            # Проверяем минимальную сумму заказа
            if order.total_amount < promo.min_order_amount:
                return {
                    "success": False,
                    "error": f"Minimum order amount: ${promo.min_order_amount}"
                }
            
            # Проверяем, не использовал ли пользователь этот промокод
            existing_use = await session.execute(
                select(PromoCodeUse).where(
                    and_(
                        PromoCodeUse.promo_code_id == promo.id,
                        PromoCodeUse.user_id == order.user_id
                    )
                )
            )
            if existing_use.scalar_one_or_none():
                if promo.max_uses_per_user <= 1:
                    return {"success": False, "error": "Promo code already used"}
            
            # Вычисляем скидку
            discount_amount = 0
            if promo.discount_type == PromoCodeType.PERCENTAGE:
                discount_amount = order.total_amount * (promo.discount_value / 100)
            elif promo.discount_type == PromoCodeType.FIXED_AMOUNT:
                discount_amount = min(promo.discount_value, order.total_amount)
            
            # Применяем скидку
            new_final_amount = max(0, order.total_amount - discount_amount)
            
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(
                    discount_amount=discount_amount,
                    final_amount=new_final_amount
                )
            )
            
            # Создаем запись об использовании промокода
            promo_use = PromoCodeUse(
                promo_code_id=promo.id,
                user_id=order.user_id,
                order_id=order.id,
                discount_amount=discount_amount
            )
            session.add(promo_use)
            
            # Обновляем счетчик использований
            await session.execute(
                update(PromoCode)
                .where(PromoCode.id == promo.id)
                .values(current_uses=PromoCode.current_uses + 1)
            )
            
            await session.commit()
            
            logger.info(f"Promo code {promo_code} applied to order {order_id}, discount: ${discount_amount}")
            
            return {
                "success": True,
                "discount_amount": float(discount_amount),
                "final_amount": float(new_final_amount)
            }
            
        except Exception as e:
            logger.error(f"Error applying promo code: {e}")
            await session.rollback()
            return {"success": False, "error": "Internal error"}
    
    async def get_recent_orders(
        self,
        session: AsyncSession,
        limit: int = 20
    ) -> List[Order]:
        """Получить последние заказы"""
        try:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.user), selectinload(Order.items))
                .order_by(desc(Order.created_at))
                .limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []