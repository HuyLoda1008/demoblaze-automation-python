"""DemoBlaze mostly returns 200 + an errorMessage field instead of real HTTP
error codes for business-logic errors -- see src/utils/api_client.py's
module docstring for the full live-verified inventory.
"""

import pytest
from playwright.sync_api import APIRequestContext

from config.environments import EnvConfig
from src.utils.api_client import DemoblazeApiClient, ProductCatalog

pytestmark = pytest.mark.api


class TestGetEntries:
    @pytest.mark.smoke
    def test_returns_the_product_catalog(self, api_client: DemoblazeApiClient) -> None:
        # The call itself raises via Pydantic if the shape mismatches
        # ProductCatalog, so reaching this assertion is implicit schema
        # validation.
        catalog = api_client.get_product_catalog()
        assert len(catalog.Items) > 0

    @pytest.mark.regression
    def test_response_validates_against_product_catalog_schema_explicit_check(
        self, api_client: DemoblazeApiClient
    ) -> None:
        # Intentionally redundant with the smoke test's internal validation,
        # made explicit as its own named case for reviewers.
        catalog = api_client.get_product_catalog()
        ProductCatalog.model_validate(catalog.model_dump())


class TestPostView:
    @pytest.mark.regression
    def test_returns_the_matching_product_for_a_known_id(self, api_client: DemoblazeApiClient) -> None:
        result = api_client.get_product(1)
        assert result.status == 200
        assert result.ok is True
        assert result.product is not None
        assert result.product.id == 1
        assert result.product.title == 'Samsung galaxy s6'
        assert result.product.price == 360

    @pytest.mark.regression
    def test_a_nonexistent_id_returns_200_with_an_error_message_not_a_404(
        self, api_client: DemoblazeApiClient
    ) -> None:
        result = api_client.get_product(999_999)
        assert result.status == 200
        assert result.ok is False
        assert result.product is None
        assert result.error_message == 'Not found.'

    @pytest.mark.regression
    def test_a_missing_id_field_returns_a_different_error_message_than_the_nonexistent_id_case(
        self, api_request_context: APIRequestContext, env: EnvConfig
    ) -> None:
        # Bypasses the client with a raw POST -- deliberately sends a
        # malformed payload (id field omitted entirely) that the client's
        # own methods don't construct, since they always build well-formed
        # requests.
        response = api_request_context.post(f'{env.api_base_url}/view', data={})
        body = response.json()
        assert body['errorMessage'] == 'Product not found.'

    @pytest.mark.regression
    def test_a_non_numeric_id_crashes_the_server_with_a_500_a_real_demoblaze_bug(
        self, api_client: DemoblazeApiClient
    ) -> None:
        result = api_client.get_product('abc')
        assert result.status == 500
        assert result.product is None
        # The 500 response body is HTML, not JSON, hence raw_body (not a
        # parsed product/error).
        assert result.raw_body is not None
        assert 'Internal Server Error' in result.raw_body


class TestOtherViewRouting:
    @pytest.mark.regression
    def test_get_view_is_rejected_the_endpoint_requires_post(self, api_client: DemoblazeApiClient) -> None:
        status, body = api_client.get_product_via_get(1)
        assert status == 405
        assert 'Method Not Allowed' in body

    @pytest.mark.regression
    def test_an_unknown_route_returns_a_conventional_404(self, api_client: DemoblazeApiClient) -> None:
        status, body = api_client.get_raw('/this-route-does-not-exist')
        assert status == 404
        assert 'Not Found' in body


class TestPostLogin:
    @pytest.mark.auth
    def test_valid_credentials_succeed(self, api_client: DemoblazeApiClient, env: EnvConfig) -> None:
        result = api_client.login(env.test_user.username, env.test_user.password)
        assert result.status == 200
        # Status alone can't distinguish pass/fail here (both return 200);
        # `ok` (business-logic-derived) is the real signal.
        assert result.ok is True
        assert result.auth_token is not None
        assert 'Auth_token' in result.auth_token
        assert result.error_message is None

    @pytest.mark.auth
    def test_wrong_password_returns_an_error_message(
        self, api_client: DemoblazeApiClient, env: EnvConfig
    ) -> None:
        result = api_client.login(env.test_user.username, 'definitely-wrong-password')
        assert result.status == 200
        assert result.ok is False
        assert result.error_message == 'Wrong password.'
        assert result.auth_token is None

    @pytest.mark.auth
    def test_a_nonexistent_username_returns_an_error_message(self, api_client: DemoblazeApiClient) -> None:
        result = api_client.login('nonexistent_user_zzz', 'any-password')
        assert result.status == 200
        assert result.ok is False
        assert result.error_message == 'User does not exist.'

    @pytest.mark.auth
    def test_a_missing_password_reports_missing_username_a_real_demoblaze_bug(
        self, api_request_context: APIRequestContext, env: EnvConfig
    ) -> None:
        # Bypasses the client with a raw POST -- only `username`, no
        # `password` -- documenting a confirmed real bug where the message
        # wrongly blames username when password is what's actually missing.
        response = api_request_context.post(
            f'{env.api_base_url}/login', data={'username': env.test_user.username}
        )
        body = response.json()
        assert body['errorMessage'] == 'Bad parameter, missing username'
