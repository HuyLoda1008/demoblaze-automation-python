import pytest

from config.environments import EnvConfig
from src.pages.home_page import HomePage


@pytest.mark.smoke
@pytest.mark.auth
def test_valid_credentials_log_the_user_in(home_page: HomePage, env: EnvConfig) -> None:
    home_page.open()
    home_page.open_login_modal()
    home_page.login_modal.login_expecting_success(env.test_user.username, env.test_user.password)

    # A single shared, fixed test account (no account-provisioning API)
    # means parallel cross-browser runs can race-login as the same user;
    # a generous timeout (not serialization) absorbs the contention.
    home_page.welcome_label.wait_for(state='visible', timeout=15_000)
    assert home_page.welcome_label.inner_text().startswith('Welcome')
    assert home_page.logout_nav_link.is_visible()


@pytest.mark.regression
@pytest.mark.auth
def test_wrong_password_is_rejected_via_a_native_alert(home_page: HomePage, env: EnvConfig) -> None:
    home_page.open()
    home_page.open_login_modal()
    message = home_page.login_modal.login_expecting_dialog(
        env.test_user.username, 'definitely-wrong-password'
    )

    assert message == 'Wrong password.'
    assert not home_page.is_logged_in()


@pytest.mark.regression
@pytest.mark.auth
def test_nonexistent_username_is_rejected_via_a_native_alert(home_page: HomePage) -> None:
    home_page.open()
    home_page.open_login_modal()
    message = home_page.login_modal.login_expecting_dialog('nonexistent_user_zzz', 'any-password')

    assert message == 'User does not exist.'


@pytest.mark.regression
@pytest.mark.auth
def test_empty_username_and_password_is_rejected_via_a_native_alert(home_page: HomePage) -> None:
    home_page.open()
    home_page.open_login_modal()
    message = home_page.login_modal.login_expecting_dialog('', '')

    assert message == 'Please fill out Username and Password.'


@pytest.mark.regression
@pytest.mark.auth
def test_whitespace_padded_username_is_treated_as_different_nonexistent_username(
    home_page: HomePage, env: EnvConfig
) -> None:
    # Verified live: DemoBlaze doesn't trim server-side.
    home_page.open()
    home_page.open_login_modal()
    padded_username = f'  {env.test_user.username}  '
    message = home_page.login_modal.login_expecting_dialog(padded_username, env.test_user.password)

    assert message == 'User does not exist.'


@pytest.mark.regression
@pytest.mark.auth
def test_log_out_returns_the_nav_bar_to_the_logged_out_state(home_page: HomePage, env: EnvConfig) -> None:
    home_page.open()
    home_page.open_login_modal()
    home_page.login_modal.login_expecting_success(env.test_user.username, env.test_user.password)
    home_page.welcome_label.wait_for(state='visible', timeout=15_000)

    home_page.logout()

    assert not home_page.logout_nav_link.is_visible()
    assert home_page.login_nav_link.is_visible()
