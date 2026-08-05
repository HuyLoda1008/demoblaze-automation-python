"""Pure branching logic, no browser/network. baseUrl/apiBaseUrl/testUser are
NOT retested here since asserting a specific default would depend on
config/env/prod.env's load order, making the test env-dependent rather than
code-dependent (same rationale as the TypeScript sibling suite).
"""

import re

import pytest

from config.environments import get_env_config


def test_defaults_to_demoblaze_prod_when_test_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('TEST_ENV', raising=False)
    config = get_env_config()
    assert config.env_name == 'demoblaze_prod'
    assert re.match(r'^https?://', config.base_url)
    assert re.match(r'^https?://', config.api_base_url)


def test_explicit_test_env_demoblaze_prod_resolves_same_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TEST_ENV', 'demoblaze_prod')
    config = get_env_config()
    assert config.env_name == 'demoblaze_prod'


def test_unknown_test_env_raises_listing_available_environments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TEST_ENV', 'nonexistent_env_zzz')
    with pytest.raises(ValueError) as exc_info:
        get_env_config()
    assert str(exc_info.value) == (
        "Unknown TEST_ENV 'nonexistent_env_zzz'. Available environments: demoblaze_prod"
    )
