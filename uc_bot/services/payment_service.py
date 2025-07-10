"""
Payment Service - Сервис для работы с платежами
"""
import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from database.models import Payment, Order, PaymentStatus, PaymentMethod, OrderStatus
from config.settings import settings
from utils.logger import logger


class PaymentService:
    """Сервис для работы с платежами"""
    
    def __init__(self):
        self._stripe = None
        self._paypal = None
        self._crypto_provider = None
    
    async def create_payment(
        self,
        session: AsyncSession,
        order: Order,
        method: str
    ) -> Optional[str]:
        """Создать платеж и вернуть URL для оплаты"""
        try:
            # Создаем запись о платеже
            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                method=PaymentMethod(method),
                amount=order.final_amount,
                currency=order.currency,
                status=PaymentStatus.PENDING
            )
            
            session.add(payment)
            await session.flush()
            
            # Обновляем статус заказа
            await session.execute(
                update(Order)
                .where(Order.id == order.id)
                .values(status=OrderStatus.PROCESSING)
            )
            
            # Создаем платеж в зависимости от метода
            payment_url = None
            
            if method == "stripe":
                payment_url = await self._create_stripe_payment(session, payment, order)
            elif method == "paypal":
                payment_url = await self._create_paypal_payment(session, payment, order)
            elif method == "crypto":
                payment_url = await self._create_crypto_payment(session, payment, order)
            elif method == "qiwi":
                payment_url = await self._create_qiwi_payment(session, payment, order)
            elif method == "yoomoney":
                payment_url = await self._create_yoomoney_payment(session, payment, order)
            
            if payment_url:
                await session.commit()
                logger.info(f"Payment {payment.id} created for order {order.id}")
                return payment_url
            else:
                await session.rollback()
                return None
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            await session.rollback()
            return None
    
    async def _create_stripe_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        order: Order
    ) -> Optional[str]:
        """Создать платеж через Stripe"""
        try:
            import stripe
            
            if not settings.STRIPE_SECRET_KEY:
                logger.error("Stripe not configured")
                return None
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Создаем Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': order.currency.lower(),
                        'product_data': {
                            'name': f'{order.total_uc} UC for PUBG Mobile',
                            'description': f'PUBG ID: {order.pubg_id}',
                        },
                        'unit_amount': int(payment.amount * 100),  # Stripe uses cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{settings.TELEGRAM_WEBHOOK_URL}/payment/success/{payment.uuid}',
                cancel_url=f'{settings.TELEGRAM_WEBHOOK_URL}/payment/cancel/{payment.uuid}',
                metadata={
                    'payment_id': str(payment.id),
                    'order_id': str(order.id),
                    'user_id': str(order.user_id),
                }
            )
            
            # Сохраняем ID сессии
            payment.external_id = checkout_session.id
            payment.external_data = {
                'checkout_session_id': checkout_session.id,
                'payment_intent_id': checkout_session.payment_intent
            }
            
            return checkout_session.url
            
        except Exception as e:
            logger.error(f"Error creating Stripe payment: {e}")
            return None
    
    async def _create_paypal_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        order: Order
    ) -> Optional[str]:
        """Создать платеж через PayPal"""
        try:
            import requests
            import base64
            
            if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
                logger.error("PayPal not configured")
                return None
            
            # Получаем токен доступа
            auth_url = "https://api.sandbox.paypal.com/v1/oauth2/token" if settings.PAYPAL_SANDBOX else "https://api.paypal.com/v1/oauth2/token"
            auth_data = base64.b64encode(f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}".encode()).decode()
            
            auth_response = requests.post(
                auth_url,
                headers={
                    "Authorization": f"Basic {auth_data}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data="grant_type=client_credentials"
            )
            
            if auth_response.status_code != 200:
                logger.error("Failed to get PayPal access token")
                return None
            
            access_token = auth_response.json()["access_token"]
            
            # Создаем платеж
            payment_url = "https://api.sandbox.paypal.com/v2/checkout/orders" if settings.PAYPAL_SANDBOX else "https://api.paypal.com/v2/checkout/orders"
            
            payment_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": order.currency,
                        "value": str(payment.amount)
                    },
                    "description": f"{order.total_uc} UC for PUBG Mobile (ID: {order.pubg_id})"
                }],
                "application_context": {
                    "return_url": f"{settings.TELEGRAM_WEBHOOK_URL}/payment/paypal/success/{payment.uuid}",
                    "cancel_url": f"{settings.TELEGRAM_WEBHOOK_URL}/payment/paypal/cancel/{payment.uuid}"
                }
            }
            
            payment_response = requests.post(
                payment_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=payment_data
            )
            
            if payment_response.status_code != 201:
                logger.error("Failed to create PayPal payment")
                return None
            
            payment_result = payment_response.json()
            payment.external_id = payment_result["id"]
            payment.external_data = payment_result
            
            # Находим approve URL
            for link in payment_result.get("links", []):
                if link["rel"] == "approve":
                    return link["href"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {e}")
            return None
    
    async def _create_crypto_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        order: Order
    ) -> Optional[str]:
        """Создать криптоплатеж"""
        try:
            import requests
            
            if not settings.CRYPTOPAY_API_TOKEN:
                logger.error("CryptoPay not configured")
                return None
            
            # Создаем инвойс через CryptoPay API
            response = requests.post(
                "https://pay.crypt.bot/api/createInvoice",
                headers={
                    "Crypto-Pay-API-Token": settings.CRYPTOPAY_API_TOKEN
                },
                json={
                    "asset": "USDT",
                    "amount": str(payment.amount),
                    "description": f"{order.total_uc} UC for PUBG Mobile",
                    "payload": f"order_{order.id}_payment_{payment.id}",
                    "return_url": f"{settings.TELEGRAM_WEBHOOK_URL}/payment/crypto/success/{payment.uuid}",
                    "cancel_url": f"{settings.TELEGRAM_WEBHOOK_URL}/payment/crypto/cancel/{payment.uuid}"
                }
            )
            
            if response.status_code != 200:
                logger.error("Failed to create crypto payment")
                return None
            
            result = response.json()
            if not result.get("ok"):
                logger.error(f"CryptoPay error: {result.get('error')}")
                return None
            
            invoice = result["result"]
            payment.external_id = str(invoice["invoice_id"])
            payment.external_data = invoice
            
            return invoice["pay_url"]
            
        except Exception as e:
            logger.error(f"Error creating crypto payment: {e}")
            return None
    
    async def _create_qiwi_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        order: Order
    ) -> Optional[str]:
        """Создать платеж через QIWI"""
        try:
            import requests
            
            if not settings.QIWI_SECRET_KEY:
                logger.error("QIWI not configured")
                return None
            
            # Создаем счет в QIWI
            bill_id = f"order_{order.id}_{payment.id}"
            
            response = requests.put(
                f"https://api.qiwi.com/partner/bill/v1/bills/{bill_id}",
                headers={
                    "Authorization": f"Bearer {settings.QIWI_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "amount": {
                        "currency": "RUB",
                        "value": str(payment.amount * 90)  # Convert USD to RUB
                    },
                    "comment": f"{order.total_uc} UC для PUBG Mobile",
                    "expirationDateTime": (datetime.now(timezone.utc).isoformat()),
                    "customFields": {
                        "order_id": str(order.id),
                        "payment_id": str(payment.id)
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error("Failed to create QIWI payment")
                return None
            
            result = response.json()
            payment.external_id = bill_id
            payment.external_data = result
            
            return result["payUrl"]
            
        except Exception as e:
            logger.error(f"Error creating QIWI payment: {e}")
            return None
    
    async def _create_yoomoney_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        order: Order
    ) -> Optional[str]:
        """Создать платеж через YooMoney"""
        try:
            # Placeholder для YooMoney интеграции
            logger.warning("YooMoney payment not implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"Error creating YooMoney payment: {e}")
            return None
    
    async def check_payment_status(
        self,
        session: AsyncSession,
        order: Order
    ) -> str:
        """Проверить статус платежа"""
        try:
            # Получаем последний платеж для заказа
            result = await session.execute(
                select(Payment)
                .where(Payment.order_id == order.id)
                .order_by(Payment.created_at.desc())
                .limit(1)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                return "not_found"
            
            # Если статус уже финальный, возвращаем его
            if payment.status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
                return payment.status.value
            
            # Проверяем статус в зависимости от метода
            if payment.method == PaymentMethod.STRIPE:
                return await self._check_stripe_payment(session, payment)
            elif payment.method == PaymentMethod.PAYPAL:
                return await self._check_paypal_payment(session, payment)
            elif payment.method == PaymentMethod.CRYPTO:
                return await self._check_crypto_payment(session, payment)
            elif payment.method == PaymentMethod.QIWI:
                return await self._check_qiwi_payment(session, payment)
            
            return payment.status.value
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return "error"
    
    async def _check_stripe_payment(
        self,
        session: AsyncSession,
        payment: Payment
    ) -> str:
        """Проверить статус Stripe платежа"""
        try:
            import stripe
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            session_data = stripe.checkout.Session.retrieve(payment.external_id)
            
            if session_data.payment_status == "paid":
                await self._complete_payment(session, payment)
                return "completed"
            elif session_data.payment_status == "unpaid":
                return "pending"
            else:
                await self._fail_payment(session, payment, "Payment failed")
                return "failed"
                
        except Exception as e:
            logger.error(f"Error checking Stripe payment: {e}")
            return "error"
    
    async def _check_paypal_payment(
        self,
        session: AsyncSession,
        payment: Payment
    ) -> str:
        """Проверить статус PayPal платежа"""
        try:
            # Placeholder для проверки PayPal платежа
            return payment.status.value
            
        except Exception as e:
            logger.error(f"Error checking PayPal payment: {e}")
            return "error"
    
    async def _check_crypto_payment(
        self,
        session: AsyncSession,
        payment: Payment
    ) -> str:
        """Проверить статус криптоплатежа"""
        try:
            import requests
            
            response = requests.get(
                f"https://pay.crypt.bot/api/getInvoices",
                headers={
                    "Crypto-Pay-API-Token": settings.CRYPTOPAY_API_TOKEN
                },
                params={
                    "invoice_ids": payment.external_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") and result["result"]["items"]:
                    invoice = result["result"]["items"][0]
                    status = invoice["status"]
                    
                    if status == "paid":
                        await self._complete_payment(session, payment)
                        return "completed"
                    elif status == "expired":
                        await self._fail_payment(session, payment, "Expired")
                        return "failed"
            
            return payment.status.value
            
        except Exception as e:
            logger.error(f"Error checking crypto payment: {e}")
            return "error"
    
    async def _check_qiwi_payment(
        self,
        session: AsyncSession,
        payment: Payment
    ) -> str:
        """Проверить статус QIWI платежа"""
        try:
            import requests
            
            response = requests.get(
                f"https://api.qiwi.com/partner/bill/v1/bills/{payment.external_id}",
                headers={
                    "Authorization": f"Bearer {settings.QIWI_SECRET_KEY}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result["status"]["value"]
                
                if status == "PAID":
                    await self._complete_payment(session, payment)
                    return "completed"
                elif status in ["EXPIRED", "REJECTED"]:
                    await self._fail_payment(session, payment, f"Status: {status}")
                    return "failed"
            
            return payment.status.value
            
        except Exception as e:
            logger.error(f"Error checking QIWI payment: {e}")
            return "error"
    
    async def _complete_payment(
        self,
        session: AsyncSession,
        payment: Payment
    ) -> bool:
        """Завершить платеж"""
        try:
            # Обновляем статус платежа
            await session.execute(
                update(Payment)
                .where(Payment.id == payment.id)
                .values(
                    status=PaymentStatus.COMPLETED,
                    paid_at=datetime.now(timezone.utc)
                )
            )
            
            # Обновляем статус заказа
            await session.execute(
                update(Order)
                .where(Order.id == payment.order_id)
                .values(
                    status=OrderStatus.PAID,
                    paid_at=datetime.now(timezone.utc)
                )
            )
            
            await session.commit()
            
            logger.info(f"Payment {payment.id} completed")
            
            # Обрабатываем доставку
            await self._process_delivery(session, payment.order_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing payment: {e}")
            await session.rollback()
            return False
    
    async def _fail_payment(
        self,
        session: AsyncSession,
        payment: Payment,
        reason: str
    ) -> bool:
        """Провалить платеж"""
        try:
            await session.execute(
                update(Payment)
                .where(Payment.id == payment.id)
                .values(
                    status=PaymentStatus.FAILED,
                    failure_reason=reason
                )
            )
            
            await session.execute(
                update(Order)
                .where(Order.id == payment.order_id)
                .values(status=OrderStatus.CANCELLED)
            )
            
            await session.commit()
            
            logger.info(f"Payment {payment.id} failed: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error failing payment: {e}")
            await session.rollback()
            return False
    
    async def _process_delivery(self, session: AsyncSession, order_id: int):
        """Обработать доставку UC"""
        try:
            # Здесь должна быть интеграция с PUBG API для автоматической доставки
            # Пока что просто генерируем код доставки
            import random
            import string
            
            delivery_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            
            # Обновляем заказ с кодом доставки
            from services.order_service import OrderService
            order_service = OrderService()
            
            await order_service.set_delivery_code(session, order_id, delivery_code)
            
            logger.info(f"Delivery processed for order {order_id}")
            
        except Exception as e:
            logger.error(f"Error processing delivery: {e}")
    
    async def get_payment_statistics(
        self,
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Получить статистику платежей"""
        try:
            from sqlalchemy import func
            from datetime import timedelta
            
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Общее количество платежей
            total_payments_result = await session.execute(
                select(func.count(Payment.id))
                .where(Payment.created_at >= since_date)
            )
            total_payments = total_payments_result.scalar() or 0
            
            # Успешные платежи
            successful_payments_result = await session.execute(
                select(func.count(Payment.id))
                .where(
                    Payment.created_at >= since_date,
                    Payment.status == PaymentStatus.COMPLETED
                )
            )
            successful_payments = successful_payments_result.scalar() or 0
            
            # Доход
            revenue_result = await session.execute(
                select(func.sum(Payment.amount))
                .where(
                    Payment.created_at >= since_date,
                    Payment.status == PaymentStatus.COMPLETED
                )
            )
            total_revenue = revenue_result.scalar() or 0
            
            # Статистика по методам платежа
            method_stats = {}
            for method in PaymentMethod:
                result = await session.execute(
                    select(func.count(Payment.id))
                    .where(
                        Payment.created_at >= since_date,
                        Payment.method == method,
                        Payment.status == PaymentStatus.COMPLETED
                    )
                )
                method_stats[method.value] = result.scalar() or 0
            
            success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
            
            return {
                "total_payments": total_payments,
                "successful_payments": successful_payments,
                "total_revenue": float(total_revenue),
                "success_rate": round(success_rate, 2),
                "method_stats": method_stats,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting payment statistics: {e}")
            return {}