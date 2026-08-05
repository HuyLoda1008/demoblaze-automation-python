"""Pure logic, no network/browser. A regression here silently weakens every
API test that imports these schemas.
"""

import pytest
from pydantic import ValidationError

from src.utils.api_client import (
    ApiError,
    Product,
    ProductCatalog,
    try_validate_auth_token,
)

VALID_PRODUCT = {
    'id': 1,
    'title': 'Samsung galaxy s6',
    'price': 360,
    'cat': 'phone',
    'desc': 'some description',
    'img': 'img/s6.jpg',
}


class TestProductSchema:
    def test_accepts_a_well_formed_product(self) -> None:
        Product.model_validate(VALID_PRODUCT)

    def test_rejects_a_product_missing_a_required_field(self) -> None:
        payload = {k: v for k, v in VALID_PRODUCT.items() if k != 'img'}
        with pytest.raises(ValidationError):
            Product.model_validate(payload)

    def test_rejects_a_product_with_the_wrong_type_for_price(self) -> None:
        payload = {**VALID_PRODUCT, 'price': '360'}
        with pytest.raises(ValidationError):
            Product.model_validate(payload, strict=True)


class TestProductCatalogSchema:
    def test_accepts_an_items_array_of_valid_products(self) -> None:
        ProductCatalog.model_validate({'Items': [VALID_PRODUCT]})

    def test_accepts_an_empty_items_array(self) -> None:
        ProductCatalog.model_validate({'Items': []})

    def test_rejects_a_payload_missing_the_items_field_entirely(self) -> None:
        with pytest.raises(ValidationError):
            ProductCatalog.model_validate({})

    def test_rejects_a_payload_where_one_item_in_items_is_malformed(self) -> None:
        malformed = {'id': 2, 'title': 'Nokia lumia 1520'}  # missing price/cat/desc/img
        with pytest.raises(ValidationError):
            ProductCatalog.model_validate({'Items': [VALID_PRODUCT, malformed]})


class TestApiErrorSchema:
    def test_accepts_error_message_string(self) -> None:
        ApiError.model_validate({'errorMessage': 'Not found.'})

    def test_rejects_a_payload_without_error_message(self) -> None:
        with pytest.raises(ValidationError):
            ApiError.model_validate({'message': 'Not found.'})

    def test_rejects_error_message_with_the_wrong_type(self) -> None:
        with pytest.raises(ValidationError):
            ApiError.model_validate({'errorMessage': 404}, strict=True)


class TestAuthTokenSchema:
    def test_accepts_a_string_with_the_auth_token_prefix(self) -> None:
        ok, _ = try_validate_auth_token('Auth_token: abc123')
        assert ok is True

    def test_rejects_a_plain_string_without_the_prefix(self) -> None:
        # This is the exact regression this schema exists to catch (see the
        # JSON-string-token note in api_client.py).
        ok, _ = try_validate_auth_token('abc123')
        assert ok is False

    def test_rejects_a_non_string_value(self) -> None:
        ok, _ = try_validate_auth_token({'token': 'Auth_token: abc123'})
        assert ok is False
