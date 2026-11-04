import logging

from config.settings import Settings
from repositories.user_repo import UserRepo
from utils.permissions import ROLE_ROOT


logger = logging.getLogger(__name__)


async def ensure_root_users(user_repo: UserRepo, settings: Settings) -> None:
    """
    Создаёт root-пользователей при старте бота.

    Важно:
    - роли берутся из .env;
    - регистрация через /start для root не обязательна;
    - наличие в общем чате для root не проверяется.
    """

    for root_id in settings.root_user_ids:
        user = await user_repo.get_by_id(root_id)

        if user is None:
            await user_repo.create(root_id, role=ROLE_ROOT, status="active")
            await user_repo.set_profile_complete(root_id)

            logger.info(
                "[SYSTEM] Root-пользователь %s создан при старте",
                root_id,
            )
            continue

        # Если root уже есть, убеждаемся, что роль и статус корректны.
        if user.role != ROLE_ROOT:
            await user_repo.update_role(root_id, ROLE_ROOT)

        if user.status != "active":
            await user_repo.update_status(root_id, "active")

        if not user.is_profile_complete:
            await user_repo.set_profile_complete(root_id)

        logger.info(
            "[SYSTEM] Root-пользователь %s проверен при старте",
            root_id,
        )