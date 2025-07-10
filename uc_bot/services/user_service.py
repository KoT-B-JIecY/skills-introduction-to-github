"""
User Service - Бизнес-логика для работы с пользователями
"""
import random
import string
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from database.models import User, Order, UserStatus
from utils.logger import logger


class UserService:
    """Сервис для работы с пользователями"""
    
    async def get_user_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        try:
            result = await session.execute(
                select(User).where(User.telegram_id == str(telegram_id))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
            return None
    
    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> User:
        """Получить или создать пользователя"""
        try:
            # Попытка найти существующего пользователя
            user = await self.get_user_by_telegram_id(session, telegram_id)
            
            if user:
                # Обновляем информацию пользователя
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                if language_code:
                    user.language_code = language_code
                
                await session.commit()
                return user
            
            # Создаем нового пользователя
            user = User(
                telegram_id=str(telegram_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code or "ru",
                referral_code=await self._generate_referral_code(session)
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Created new user: {telegram_id} ({username})")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            await session.rollback()
            raise
    
    async def _generate_referral_code(self, session: AsyncSession) -> str:
        """Генерировать уникальный реферальный код"""
        for _ in range(10):  # Максимум 10 попыток
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Проверяем уникальность
            result = await session.execute(
                select(User).where(User.referral_code == code)
            )
            if not result.scalar_one_or_none():
                return code
        
        raise ValueError("Unable to generate unique referral code")
    
    async def process_referral(
        self,
        session: AsyncSession,
        user: User,
        referral_code: str
    ) -> bool:
        """Обработать реферальную ссылку"""
        try:
            # Проверяем, что пользователь еще не был рефералом
            if user.referred_by_id:
                return False
            
            # Ищем пользователя с таким реферальным кодом
            result = await session.execute(
                select(User).where(User.referral_code == referral_code)
            )
            referrer = result.scalar_one_or_none()
            
            if not referrer or referrer.id == user.id:
                return False
            
            # Устанавливаем связь
            user.referred_by_id = referrer.id
            await session.commit()
            
            logger.info(f"User {user.telegram_id} referred by {referrer.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            await session.rollback()
            return False
    
    async def add_referral_bonus(
        self,
        session: AsyncSession,
        user_id: int,
        amount: float
    ) -> bool:
        """Добавить реферальный бонус"""
        try:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(referral_bonus=User.referral_bonus + amount)
            )
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding referral bonus: {e}")
            await session.rollback()
            return False
    
    async def update_user_stats(
        self,
        session: AsyncSession,
        user_id: int,
        order_amount: float,
        uc_amount: int
    ) -> bool:
        """Обновить статистику пользователя"""
        try:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    total_orders=User.total_orders + 1,
                    total_spent=User.total_spent + order_amount,
                    total_uc_purchased=User.total_uc_purchased + uc_amount
                )
            )
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
            await session.rollback()
            return False
    
    async def get_user_stats(self, session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        try:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return {
                    "total_orders": 0,
                    "total_spent": 0,
                    "total_uc": 0,
                    "referral_bonus": 0,
                    "referred_users": 0
                }
            
            # Получаем количество рефералов
            referrals_result = await session.execute(
                select(func.count(User.id)).where(User.referred_by_id == user_id)
            )
            referred_count = referrals_result.scalar() or 0
            
            return {
                "total_orders": user.total_orders,
                "total_spent": float(user.total_spent),
                "total_uc": user.total_uc_purchased,
                "referral_bonus": float(user.referral_bonus),
                "referred_users": referred_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    async def ban_user(self, session: AsyncSession, user_id: int, reason: str = "") -> bool:
        """Заблокировать пользователя"""
        try:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_banned=True,
                    status=UserStatus.BLOCKED
                )
            )
            await session.commit()
            
            logger.info(f"User {user_id} banned. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            await session.rollback()
            return False
    
    async def unban_user(self, session: AsyncSession, user_id: int) -> bool:
        """Разблокировать пользователя"""
        try:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_banned=False,
                    status=UserStatus.ACTIVE
                )
            )
            await session.commit()
            
            logger.info(f"User {user_id} unbanned")
            return True
            
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            await session.rollback()
            return False
    
    async def update_pubg_data(
        self,
        session: AsyncSession,
        user_id: int,
        pubg_id: Optional[str] = None,
        pubg_nickname: Optional[str] = None
    ) -> bool:
        """Обновить данные PUBG пользователя"""
        try:
            update_data = {}
            if pubg_id is not None:
                update_data['pubg_id'] = pubg_id
            if pubg_nickname is not None:
                update_data['pubg_nickname'] = pubg_nickname
            
            if update_data:
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data)
                )
                await session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating PUBG data for user {user_id}: {e}")
            await session.rollback()
            return False
    
    async def search_users(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 50
    ) -> list[User]:
        """Поиск пользователей"""
        try:
            result = await session.execute(
                select(User)
                .where(
                    (User.username.ilike(f"%{query}%")) |
                    (User.first_name.ilike(f"%{query}%")) |
                    (User.telegram_id.ilike(f"%{query}%"))
                )
                .limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    async def get_user_orders(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> list[Order]:
        """Получить заказы пользователя"""
        try:
            result = await session.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []