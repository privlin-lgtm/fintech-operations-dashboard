from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import UserRepoDep, require_roles
from app.core.user_permissions import ASSIGNABLE_ROLES, ASSIGNABLE_USERS_READ_ROLES
from app.models.user import User
from app.schemas.user import AssignableUser

router = APIRouter(prefix="/users", tags=["users"])

AssignableUsersReaderDep = Annotated[User, Depends(require_roles(*ASSIGNABLE_USERS_READ_ROLES))]


@router.get("/assignable", response_model=list[AssignableUser])
async def list_assignable_users(
    current_user: AssignableUsersReaderDep,
    user_repo: UserRepoDep,
) -> list[AssignableUser]:
    """Active people a case or alert can be handed to, by name — for the
    Reassign and Assign pickers. Only id, name and role: no email or login data."""
    users = await user_repo.list_active_by_roles(ASSIGNABLE_ROLES)
    return [AssignableUser(id=user.id, full_name=user.full_name, role=user.role.name) for user in users]
