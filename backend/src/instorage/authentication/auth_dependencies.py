from uuid import UUID

from fastapi import Depends, Security

from instorage.authentication.auth_factory import get_auth_service
from instorage.authentication.auth_service import AuthService
from instorage.main.logging import get_logger
from instorage.server.dependencies.auth_definitions import API_KEY_HEADER, OAUTH2_SCHEME
from instorage.users.user import UserInDB
from instorage.users.user_factory import get_user_service
from instorage.users.user_service import UserService

logger = get_logger(__name__)


async def get_current_active_user(
    token: str = Security(OAUTH2_SCHEME),
    api_key: str = Security(API_KEY_HEADER),
    user_service: UserService = Depends(get_user_service),
) -> UserInDB:
    return await user_service.authenticate(token, api_key)


async def get_current_active_user_with_quota(
    token: str = Security(OAUTH2_SCHEME),
    api_key: str = Security(API_KEY_HEADER),
    user_service: UserService = Depends(get_user_service),
) -> UserInDB:
    return await user_service.authenticate(token, api_key, with_quota_used=True)


async def get_user_from_token_or_assistant_api_key(
    id: UUID,
    token: str = Security(OAUTH2_SCHEME),
    api_key: str = Security(API_KEY_HEADER),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.authenticate_with_assistant_api_key(
        api_key, token, assistant_id=id
    )


async def get_user_from_token_or_assistant_api_key_without_assistant_id(
    token: str = Security(OAUTH2_SCHEME),
    api_key: str = Security(API_KEY_HEADER),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.authenticate_with_assistant_api_key(api_key, token)


def get_api_key(hashed: bool = True):
    async def _get_api_key(
        api_key: str = Security(API_KEY_HEADER),
        auth_service: AuthService = Depends(get_auth_service),
    ):
        return await auth_service.get_api_key(api_key, hash_key=hashed)

    return _get_api_key
