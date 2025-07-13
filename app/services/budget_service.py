"""
Budget Management Service

Сервис для управления бюджетами пользователей с автоматическим пополнением.
Включает функции пополнения, мониторинга и аудита бюджетов.
"""

import asyncio
import logging
import os
import yaml
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from croniter import croniter

logger = logging.getLogger(__name__)


class RefillType(Enum):
    """Типы пополнения бюджета"""
    RESET = "reset"  # Сброс до лимита
    ADD = "add"  # Добавление к текущему


class RefillStatus(Enum):
    """Статусы пополнения"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"


@dataclass
class BudgetRefillRecord:
    """Запись о пополнении бюджета"""
    user_id: str
    email: str
    amount: float
    refill_type: RefillType
    previous_balance: float
    new_balance: float
    status: RefillStatus
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BudgetConfig:
    """Конфигурация бюджета пользователя"""
    user_id: str
    email: str
    role: str
    enabled: bool
    amount: float
    reset_usage: bool
    custom_schedule: Optional[str] = None
    last_refill: Optional[datetime] = None
    refill_count: int = 0
    total_refilled: float = 0.0


class BudgetService:
    """Сервис управления бюджетами"""
    
    def __init__(self, config_path: str = "config/budget_config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.refill_history: List[BudgetRefillRecord] = []
        self.user_configs: Dict[str, BudgetConfig] = {}
        self._running = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    logger.info(f"✅ Budget config loaded from {self.config_path}")
                    return config
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Error loading budget config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            "auto_refill": {
                "enabled": True,
                "schedule": {
                    "cron": "0 0 * * *",
                    "interval_type": "daily",
                    "interval_value": 1,
                    "timezone": "Europe/Moscow"
                },
                "refill_settings": {
                    "refill_type": "reset",
                    "by_role": {
                        "admin": {"enabled": True, "amount": 10000.0, "reset_usage": True},
                        "user": {"enabled": True, "amount": 1000.0, "reset_usage": True},
                        "basic": {"enabled": True, "amount": 100.0, "reset_usage": True}
                    },
                    "individual_users": {},
                    "minimum_balance": {
                        "enabled": True,
                        "threshold": 10.0,
                        "emergency_refill": 50.0
                    }
                },
                "notifications": {
                    "enabled": True,
                    "email": {"enabled": True, "send_on_refill": True}
                }
            },
            "monitoring": {"enabled": True},
            "security": {
                "max_limits": {"single_refill": 100000.0},
                "audit": {"enabled": True}
            }
        }
    
    async def start_auto_refill_scheduler(self):
        """Запуск планировщика автоматического пополнения"""
        if not self.config["auto_refill"]["enabled"]:
            logger.info("🔄 Auto-refill disabled in config")
            return
            
        self._running = True
        logger.info("🚀 Starting budget auto-refill scheduler")
        
        # Запуск в фоновом режиме
        asyncio.create_task(self._scheduler_loop())
    
    async def stop_auto_refill_scheduler(self):
        """Остановка планировщика"""
        self._running = False
        logger.info("🛑 Stopping budget auto-refill scheduler")
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        try:
            schedule_config = self.config["auto_refill"]["schedule"]
            cron_expr = schedule_config.get("cron", "0 0 * * *")
            
            # Создаем croniter для определения следующего времени выполнения
            cron = croniter(cron_expr)
            
            while self._running:
                try:
                    # Получаем следующее время выполнения
                    next_run = cron.get_next(datetime)
                    current_time = datetime.now()
                    
                    # Время до следующего выполнения
                    sleep_time = (next_run - current_time).total_seconds()
                    
                    if sleep_time > 0:
                        logger.info(f"⏰ Next budget refill scheduled for: {next_run}")
                        await asyncio.sleep(sleep_time)
                    
                    if self._running:
                        await self._execute_auto_refill()
                        
                except Exception as e:
                    logger.error(f"❌ Error in scheduler loop: {e}")
                    await asyncio.sleep(60)  # Ждем минуту перед повторной попыткой
                    
        except Exception as e:
            logger.error(f"❌ Scheduler loop failed: {e}")
    
    async def _execute_auto_refill(self):
        """Выполнение автоматического пополнения"""
        logger.info("🔄 Starting automatic budget refill")
        
        start_time = datetime.now()
        total_refilled = 0.0
        successful_refills = 0
        failed_refills = 0
        
        try:
            # Получаем список пользователей для пополнения
            users_to_refill = await self._get_users_for_refill()
            
            logger.info(f"📋 Found {len(users_to_refill)} users for refill")
            
            # Пополняем бюджеты пользователей
            for user_info in users_to_refill:
                try:
                    result = await self._refill_user_budget(user_info)
                    
                    if result.status == RefillStatus.SUCCESS:
                        successful_refills += 1
                        total_refilled += result.amount
                        logger.info(f"✅ Refilled budget for {user_info['email']}: ${result.amount}")
                    else:
                        failed_refills += 1
                        logger.error(f"❌ Failed to refill budget for {user_info['email']}: {result.error_message}")
                        
                except Exception as e:
                    failed_refills += 1
                    logger.error(f"❌ Error refilling budget for {user_info.get('email', 'unknown')}: {e}")
            
            # Логируем результаты
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"🎉 Auto-refill completed in {duration:.2f}s")
            logger.info(f"   • Total refilled: ${total_refilled:.2f}")
            logger.info(f"   • Successful: {successful_refills}")
            logger.info(f"   • Failed: {failed_refills}")
            
            # Отправляем уведомления
            await self._send_refill_notifications(successful_refills, failed_refills, total_refilled)
            
        except Exception as e:
            logger.error(f"❌ Auto-refill execution failed: {e}")
    
    async def _get_users_for_refill(self) -> List[Dict[str, Any]]:
        """Получение списка пользователей для пополнения"""
        try:
            # Получаем пользователей из auth системы
            from app.security.auth import USERS_DB
            
            users_to_refill = []
            refill_settings = self.config["auto_refill"]["refill_settings"]
            
            for email, user_data in USERS_DB.items():
                user_id = user_data["user_id"]
                
                # Проверяем индивидуальные настройки
                if email in refill_settings.get("individual_users", {}):
                    individual_config = refill_settings["individual_users"][email]
                    if individual_config.get("enabled", True):
                        users_to_refill.append({
                            "user_id": user_id,
                            "email": email,
                            "role": "individual",
                            "config": individual_config
                        })
                    continue
                
                # Проверяем настройки по ролям
                user_scopes = user_data.get("scopes", ["basic"])
                role = self._determine_user_role(user_scopes)
                
                role_config = refill_settings["by_role"].get(role, {})
                if role_config.get("enabled", False):
                    users_to_refill.append({
                        "user_id": user_id,
                        "email": email,
                        "role": role,
                        "config": role_config
                    })
            
            return users_to_refill
            
        except Exception as e:
            logger.error(f"❌ Error getting users for refill: {e}")
            return []
    
    def _determine_user_role(self, scopes: List[str]) -> str:
        """Определение роли пользователя по скопам"""
        if "admin" in scopes:
            return "admin"
        elif "generate" in scopes:
            return "user"
        else:
            return "basic"
    
    async def _refill_user_budget(self, user_info: Dict[str, Any]) -> BudgetRefillRecord:
        """Пополнение бюджета пользователя"""
        try:
            from app.security.auth import USERS_DB
            
            user_id = user_info["user_id"]
            email = user_info["email"]
            config = user_info["config"]
            
            # Получаем текущий баланс
            user_data = USERS_DB.get(email)
            if not user_data:
                return BudgetRefillRecord(
                    user_id=user_id,
                    email=email,
                    amount=0.0,
                    refill_type=RefillType.RESET,
                    previous_balance=0.0,
                    new_balance=0.0,
                    status=RefillStatus.FAILED,
                    timestamp=datetime.now(),
                    error_message="User not found"
                )
            
            previous_balance = user_data.get("current_usage", 0.0)
            budget_limit = user_data.get("budget_limit", 100.0)
            
            # Определяем тип пополнения
            refill_type = RefillType(config.get("refill_type", "reset"))
            refill_amount = config.get("amount", 100.0)
            
            # Проверяем минимальный баланс
            remaining_balance = budget_limit - previous_balance
            min_balance_config = self.config["auto_refill"]["refill_settings"].get("minimum_balance", {})
            
            if min_balance_config.get("enabled", False):
                threshold = min_balance_config.get("threshold", 10.0)
                if remaining_balance < threshold:
                    # Экстренное пополнение
                    emergency_amount = min_balance_config.get("emergency_refill", 50.0)
                    refill_amount = max(refill_amount, emergency_amount)
            
            # Выполняем пополнение
            if refill_type == RefillType.RESET:
                # Сбрасываем usage до 0 (фактически устанавливаем новый лимит)
                if config.get("reset_usage", True):
                    user_data["current_usage"] = 0.0
                
                # Обновляем лимит
                user_data["budget_limit"] = refill_amount
                new_balance = refill_amount
                
            else:  # ADD
                # Добавляем к текущему лимиту
                user_data["budget_limit"] = budget_limit + refill_amount
                new_balance = user_data["budget_limit"] - previous_balance
            
            # Создаем запись о пополнении
            refill_record = BudgetRefillRecord(
                user_id=user_id,
                email=email,
                amount=refill_amount,
                refill_type=refill_type,
                previous_balance=remaining_balance,
                new_balance=new_balance,
                status=RefillStatus.SUCCESS,
                timestamp=datetime.now()
            )
            
            # Сохраняем в историю
            self.refill_history.append(refill_record)
            
            return refill_record
            
        except Exception as e:
            logger.error(f"❌ Error refilling budget for user {user_info.get('email', 'unknown')}: {e}")
            return BudgetRefillRecord(
                user_id=user_info.get("user_id", "unknown"),
                email=user_info.get("email", "unknown"),
                amount=0.0,
                refill_type=RefillType.RESET,
                previous_balance=0.0,
                new_balance=0.0,
                status=RefillStatus.FAILED,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def _send_refill_notifications(self, successful: int, failed: int, total_amount: float):
        """Отправка уведомлений о пополнении"""
        try:
            if not self.config["auto_refill"]["notifications"]["enabled"]:
                return
            
            # Логируем результаты
            logger.info(f"📧 Sending refill notifications: {successful} successful, {failed} failed, ${total_amount:.2f} total")
            
            # В реальной системе здесь была бы отправка email/webhook уведомлений
            # Пока что просто логируем
            
        except Exception as e:
            logger.error(f"❌ Error sending refill notifications: {e}")
    
    async def get_user_budget_info(self, user_id: str) -> Dict[str, Any]:
        """Получение информации о бюджете пользователя"""
        try:
            from app.security.auth import USERS_DB
            
            # Найдем пользователя по ID
            user_data = None
            for email, data in USERS_DB.items():
                if data.get("user_id") == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return {"error": "User not found"}
            
            current_usage = user_data.get("current_usage", 0.0)
            budget_limit = user_data.get("budget_limit", 100.0)
            remaining_balance = budget_limit - current_usage
            usage_percentage = (current_usage / budget_limit * 100) if budget_limit > 0 else 0
            
            # Получаем историю пополнений для пользователя
            user_refills = [r for r in self.refill_history if r.user_id == user_id]
            last_refill = user_refills[-1] if user_refills else None
            
            return {
                "user_id": user_id,
                "email": user_data.get("email"),
                "current_usage": current_usage,
                "budget_limit": budget_limit,
                "remaining_balance": remaining_balance,
                "usage_percentage": usage_percentage,
                "budget_status": self._get_budget_status(usage_percentage),
                "last_refill": {
                    "amount": last_refill.amount if last_refill else 0.0,
                    "timestamp": last_refill.timestamp.isoformat() if last_refill else None,
                    "type": last_refill.refill_type.value if last_refill else None
                } if last_refill else None,
                "total_refills": len(user_refills),
                "total_refilled": sum(r.amount for r in user_refills)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting budget info for user {user_id}: {e}")
            return {"error": f"Failed to get budget info: {str(e)}"}
    
    def _get_budget_status(self, usage_percentage: float) -> str:
        """Определение статуса бюджета"""
        if usage_percentage >= 100:
            return "EXCEEDED"
        elif usage_percentage >= 95:
            return "CRITICAL"
        elif usage_percentage >= 80:
            return "WARNING"
        else:
            return "ACTIVE"
    
    async def manual_refill(self, user_id: str, amount: float, refill_type: str = "add") -> Dict[str, Any]:
        """Ручное пополнение бюджета"""
        try:
            from app.security.auth import USERS_DB
            
            # Проверяем безопасность
            max_single_refill = self.config["security"]["max_limits"]["single_refill"]
            if amount > max_single_refill:
                return {"error": f"Amount exceeds maximum limit: {max_single_refill}"}
            
            # Найдем пользователя
            user_data = None
            email = None
            for email_key, data in USERS_DB.items():
                if data.get("user_id") == user_id:
                    user_data = data
                    email = email_key
                    break
            
            if not user_data:
                return {"error": "User not found"}
            
            previous_balance = user_data.get("budget_limit", 100.0) - user_data.get("current_usage", 0.0)
            
            # Выполняем пополнение
            if refill_type == "reset":
                user_data["current_usage"] = 0.0
                user_data["budget_limit"] = amount
                new_balance = amount
            else:  # add
                user_data["budget_limit"] += amount
                new_balance = user_data["budget_limit"] - user_data.get("current_usage", 0.0)
            
            # Создаем запись
            refill_record = BudgetRefillRecord(
                user_id=user_id,
                email=email,
                amount=amount,
                refill_type=RefillType(refill_type),
                previous_balance=previous_balance,
                new_balance=new_balance,
                status=RefillStatus.SUCCESS,
                timestamp=datetime.now(),
                metadata={"manual": True}
            )
            
            self.refill_history.append(refill_record)
            
            logger.info(f"✅ Manual refill completed for {email}: ${amount}")
            
            return {
                "success": True,
                "amount": amount,
                "new_balance": new_balance,
                "refill_type": refill_type,
                "timestamp": refill_record.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Manual refill failed for user {user_id}: {e}")
            return {"error": f"Manual refill failed: {str(e)}"}
    
    async def get_refill_history(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение истории пополнений"""
        try:
            history = self.refill_history
            
            if user_id:
                history = [r for r in history if r.user_id == user_id]
            
            # Сортируем по времени (новые первыми)
            history = sorted(history, key=lambda x: x.timestamp, reverse=True)
            
            # Ограничиваем количество
            history = history[:limit]
            
            return [
                {
                    "user_id": r.user_id,
                    "email": r.email,
                    "amount": r.amount,
                    "refill_type": r.refill_type.value,
                    "previous_balance": r.previous_balance,
                    "new_balance": r.new_balance,
                    "status": r.status.value,
                    "timestamp": r.timestamp.isoformat(),
                    "error_message": r.error_message,
                    "metadata": r.metadata
                }
                for r in history
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting refill history: {e}")
            return []
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Получение статистики системы"""
        try:
            total_refills = len(self.refill_history)
            successful_refills = len([r for r in self.refill_history if r.status == RefillStatus.SUCCESS])
            failed_refills = total_refills - successful_refills
            
            total_amount = sum(r.amount for r in self.refill_history if r.status == RefillStatus.SUCCESS)
            
            # Статистика за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            recent_refills = [r for r in self.refill_history if r.timestamp > yesterday]
            
            return {
                "total_refills": total_refills,
                "successful_refills": successful_refills,
                "failed_refills": failed_refills,
                "success_rate": successful_refills / total_refills if total_refills > 0 else 0,
                "total_amount_refilled": total_amount,
                "average_refill_amount": total_amount / successful_refills if successful_refills > 0 else 0,
                "recent_refills_24h": len(recent_refills),
                "recent_amount_24h": sum(r.amount for r in recent_refills if r.status == RefillStatus.SUCCESS),
                "last_refill": self.refill_history[-1].timestamp.isoformat() if self.refill_history else None,
                "scheduler_running": self._running
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {"error": f"Failed to get stats: {str(e)}"}


# Глобальный экземпляр сервиса
budget_service = BudgetService()


# Функции для совместимости с существующим кодом
async def get_user_budget_info(user_id: str) -> Dict[str, Any]:
    """Получение информации о бюджете пользователя"""
    return await budget_service.get_user_budget_info(user_id)


async def manual_refill_user_budget(user_id: str, amount: float, refill_type: str = "add") -> Dict[str, Any]:
    """Ручное пополнение бюджета пользователя"""
    return await budget_service.manual_refill(user_id, amount, refill_type)


async def get_budget_refill_history(user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Получение истории пополнений"""
    return await budget_service.get_refill_history(user_id, limit)


async def get_budget_system_stats() -> Dict[str, Any]:
    """Получение статистики системы бюджетов"""
    return await budget_service.get_system_stats()


# Запуск планировщика при импорте модуля
async def init_budget_service():
    """Инициализация сервиса бюджетов"""
    try:
        await budget_service.start_auto_refill_scheduler()
        logger.info("✅ Budget service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize budget service: {e}") 