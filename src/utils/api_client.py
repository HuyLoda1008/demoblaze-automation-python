"""Typed, Pydantic-validated wrapper around every api.demoblaze.com call.

Live-verified DemoBlaze API behavior (does NOT use conventional HTTP status
codes for most business-logic errors):

- GET /entries -> 200 {Items: [{id,title,price,cat,desc,img}, ...]}
- POST /view {id} -> 200 with product for a known id; 200
  {errorMessage: "Not found."} for an unknown id (NOT 404); 200
  {errorMessage: "Product not found."} for a missing `id` field (a
  DIFFERENT message than the unknown-id case -- verified not a typo); 500
  unhandled server exception (HTML, non-JSON body) when `id` isn't
  numeric-parseable, e.g. "abc" -- a real DemoBlaze bug, asserted on
  directly rather than avoided.
- GET /view?id=1 -> 405 Method Not Allowed (POST required).
- POST /login {username, password: base64(password)} -> 200 with a
  JSON-encoded STRING token on success, e.g. "Auth_token: <base64>" (not an
  object -- easy to misdiagnose); 200 {errorMessage} object on failure; a
  missing field ALWAYS reports "Bad parameter, missing username" even when
  password (not username) is what's actually missing -- a real DemoBlaze
  message-labeling bug, not a client mistake.
- GET /<nonexistent> -> 404 plain HTML (Werkzeug default) -- the one
  conventional case.
"""

import base64
from dataclasses import dataclass
from typing import Annotated, Optional

from playwright.sync_api import APIRequestContext
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, ValidationError


class Product(BaseModel):
    id: int
    title: str
    price: float
    cat: str
    desc: str
    img: str


class ProductCatalog(BaseModel):
    Items: list[Product]


class ApiError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    error_message: str = Field(alias='errorMessage')


# Zod's z.string().regex(/^Auth_token: /) validates a bare string, not an
# object -- can't be a normal BaseModel.
AuthTokenSchema = Annotated[str, StringConstraints(pattern=r'^Auth_token: ')]
_auth_token_adapter: TypeAdapter[str] = TypeAdapter(AuthTokenSchema)


def try_validate_auth_token(value: object) -> tuple[bool, Optional[str]]:
    try:
        return True, _auth_token_adapter.validate_python(value)
    except ValidationError:
        return False, None


def try_validate_api_error(value: object) -> tuple[bool, Optional[str]]:
    try:
        return True, ApiError.model_validate(value).error_message
    except ValidationError:
        return False, None


@dataclass
class LoginResult:
    status: int
    # True only when the response has a VALID auth token (business-logic
    # success) -- DemoBlaze returns 200 for failed logins too, so a
    # status/res.ok()-based flag would be wrong.
    ok: bool
    auth_token: Optional[str]
    error_message: Optional[str]


@dataclass
class GetProductResult:
    status: int
    ok: bool  # True only when the body validates against Product
    product: Optional[Product]
    error_message: Optional[str]
    raw_body: Optional[str]  # populated only for the non-JSON 500 case


class DemoblazeApiClient:
    def __init__(self, request: APIRequestContext, base_url: str) -> None:
        self._request = request
        self._base_url = base_url

    def get_product_catalog(self) -> ProductCatalog:
        response = self._request.get(f'{self._base_url}/entries')
        body = response.json()
        # Raises via Pydantic on shape mismatch -- every caller gets
        # validation for free.
        return ProductCatalog.model_validate(body)

    def get_product(self, product_id: 'int | str') -> GetProductResult:
        response = self._request.post(f'{self._base_url}/view', data={'id': str(product_id)})
        status = response.status
        try:
            body = response.json()
        except Exception:
            # Non-numeric-id 500 case: HTML body, not JSON.
            return GetProductResult(
                status=status, ok=False, product=None, error_message=None, raw_body=response.text()
            )

        try:
            product = Product.model_validate(body)
            return GetProductResult(
                status=status, ok=True, product=product, error_message=None, raw_body=None
            )
        except ValidationError:
            error_ok, error_message = try_validate_api_error(body)
            return GetProductResult(
                status=status,
                ok=False,
                product=None,
                error_message=error_message if error_ok else None,
                raw_body=None,
            )

    def get_product_via_get(self, product_id: 'int | str') -> tuple[int, str]:
        # Exercises the documented "GET is rejected" negative case.
        response = self._request.get(f'{self._base_url}/view?id={product_id}')
        return response.status, response.text()

    def get_raw(self, path: str) -> tuple[int, str]:
        response = self._request.get(f'{self._base_url}{path}')
        return response.status, response.text()

    def login(self, username: str, password: str) -> LoginResult:
        encoded_password = base64.b64encode(password.encode()).decode()
        response = self._request.post(
            f'{self._base_url}/login', data={'username': username, 'password': encoded_password}
        )
        status = response.status
        body = response.json()

        token_ok, token = try_validate_auth_token(body)
        if token_ok:
            return LoginResult(status=status, ok=True, auth_token=token, error_message=None)

        error_ok, error_message = try_validate_api_error(body)
        return LoginResult(
            status=status,
            ok=False,
            auth_token=None,
            error_message=error_message if error_ok else None,
        )
