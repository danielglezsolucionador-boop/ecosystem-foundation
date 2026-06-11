from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.social_identity import SocialIdentityAccount, SocialIdentityStatus
from app.services.auth import get_current_user, require_control_center_user
from app.services.social_identity import (
    SocialIdentityError,
    get_social_identity_account,
    get_social_identity_status,
    list_social_identity_accounts,
    list_social_identity_approval_needed,
    list_social_identity_risks,
)

router = APIRouter(
    prefix="/api/v1/social-identity",
    tags=["social-identity"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_social_identity_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "social_identity_role_not_authorized", "role": user.role.value},
        )


def raise_social_identity_error(error: SocialIdentityError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=SocialIdentityStatus)
def read_social_identity_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SocialIdentityStatus:
    require_social_identity_read(current_user)
    return get_social_identity_status()


@router.get("/accounts", response_model=list[SocialIdentityAccount])
def read_social_identity_accounts(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SocialIdentityAccount]:
    require_social_identity_read(current_user)
    return list_social_identity_accounts()


@router.get("/accounts/{account_id}", response_model=SocialIdentityAccount)
def read_social_identity_account(
    account_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SocialIdentityAccount:
    require_social_identity_read(current_user)
    try:
        return get_social_identity_account(account_id)
    except SocialIdentityError as error:
        raise_social_identity_error(error)


@router.get("/approval-needed", response_model=list[SocialIdentityAccount])
def read_social_identity_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SocialIdentityAccount]:
    require_social_identity_read(current_user)
    return list_social_identity_approval_needed()


@router.get("/risks", response_model=list[SocialIdentityAccount])
def read_social_identity_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SocialIdentityAccount]:
    require_social_identity_read(current_user)
    return list_social_identity_risks()
