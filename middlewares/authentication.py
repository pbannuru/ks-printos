from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, EmailStr
import requests
from app.config import app_config
from app.services.core_tenant_service import CoreTenantService
from app.services.isearchui_users_service import ISearchUIUsersService
from app.sql_app.database import DbDepends
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
)

from app.sql_app.dbmodels.core_tenant import CoreTenant

app_configs = app_config.AppConfig.get_all_configs()


import requests
from jwt.algorithms import RSAAlgorithm
public_key_url = app_configs['public_key_url']
response=requests.get(public_key_url)

# Parse the JSON content correctly
data = response.json()['keys'][0]
 
jwk_data = {
      "kty": data['kty'],
      "kid": data['kid'],
      "use": data['use'],
      "n": data['n'],
      "e": data['e']
}

# Convert JWK to public key
public_key = RSAAlgorithm.from_jwk(jwk_data)

class VerifiedTokenBody(BaseModel):
    client_id: str
    # scope: list[str]
    # authorization_details: list[str]
    iss: str
    exp: int


def verify_tenant_service_token(token: str) -> VerifiedTokenBody:
    print("token:",token)
    decoded_payload = jwt.decode(
        token,
        public_key,
        algorithms=[
            "RS256",
        ],
    )
    print("decoded_payload",decoded_payload)
    return VerifiedTokenBody(**decoded_payload)


def verify_tenant_jwt(jwtoken: str) -> list[bool | VerifiedTokenBody]:
    is_token_valid: bool = False
    payload = None

    try:
        payload = verify_tenant_service_token(jwtoken)
    except Exception as e:
        print("TokenError: ", e)
        payload = None
        raise AuthenticationError(f"TokenError while verifying service token: {e}")
    if payload:
        is_token_valid = True

    return is_token_valid, payload


class BearerTokenTenantAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]

        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return
            is_token_valid, payload = verify_tenant_jwt(token)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AuthenticationError("Invalid JWT Token.")

        if not is_token_valid:
            raise HTTPException(
                status_code=403, detail="Invalid token or expired token."
            )

        with DbDepends() as db:
            tenant = CoreTenantService(db).get_by_client_id(payload.client_id)
            if not tenant:
                raise HTTPException(status_code=403, detail="Tenant Not Found.")

        return auth, tenant


# ISearch UI


class VerifiedTokenBodyISearchUI(BaseModel):
    uid: EmailStr
    sub: EmailStr
    ntUserDomainId: str
    givenName: str
    employeeNumber: int


def verify_isearch_user_service_token(token: str) -> VerifiedTokenBodyISearchUI:
    headers = {"Authorization": f"Bearer {token}"}
    url = app_configs['user_service_token_url']
    response = requests.get(
        url, headers=headers
    )
    response.raise_for_status()
    return VerifiedTokenBodyISearchUI(**response.json())


def verify_isearch_user_jwt(jwtoken: str) -> list[bool | VerifiedTokenBodyISearchUI]:
    is_token_valid: bool = False
    payload = None

    try:
        payload = verify_isearch_user_service_token(jwtoken)
    except Exception as e:
        print("TokenError: ", e)
        payload = None
        raise AuthenticationError(f"TokenError while verifying service token: {e}")
    if payload:
        is_token_valid = True

    return is_token_valid, payload


class BearerTokenISearchUserAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]

        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return
            is_token_valid, payload = verify_isearch_user_jwt(token)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AuthenticationError("Invalid JWT Token.")

        if not is_token_valid:
            raise HTTPException(
                status_code=403, detail="Invalid token or expired token."
            )

        with DbDepends() as db:
            user = ISearchUIUsersService(db).get_or_create_user(email=payload.uid)

            if not user:
                raise HTTPException(
                    status_code=403, detail="User Not Found, or Creation Failed."
                )

        return auth, user


# used for swagger documentation
class JWTBearerTenantApiSwaggerAuthenticated(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearerTenantApiSwaggerAuthenticated, self).__init__(
            auto_error=auto_error
        )

    async def __call__(self, request: Request) -> CoreTenant:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearerTenantApiSwaggerAuthenticated, self
        ).__call__(request)


# used for swagger documentation
class JWTBearerISearchUserSwaggerAuthenticated(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearerISearchUserSwaggerAuthenticated, self).__init__(
            auto_error=auto_error
        )

    async def __call__(self, request: Request) -> CoreTenant:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearerISearchUserSwaggerAuthenticated, self
        ).__call__(request)