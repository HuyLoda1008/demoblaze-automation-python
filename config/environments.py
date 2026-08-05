import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / 'env' / 'prod.env')


@dataclass
class TestUser:
    username: str
    password: str


@dataclass
class EnvConfig:
    env_name: str
    base_url: str
    api_base_url: str
    test_user: TestUser


def _build_environments() -> dict[str, EnvConfig]:
    return {
        'demoblaze_prod': EnvConfig(
            env_name='demoblaze_prod',
            base_url=os.environ.get('BASE_URL', 'https://www.demoblaze.com'),
            api_base_url=os.environ.get('API_BASE_URL', 'https://api.demoblaze.com'),
            test_user=TestUser(
                username=os.environ.get('TEST_USER', ''),
                password=os.environ.get('TEST_PASSWORD', ''),
            ),
        ),
    }


def get_env_config() -> EnvConfig:
    env_name = os.environ.get('TEST_ENV', 'demoblaze_prod')
    environments = _build_environments()
    config = environments.get(env_name)
    if config is None:
        available = ', '.join(environments.keys())
        raise ValueError(f"Unknown TEST_ENV '{env_name}'. Available environments: {available}")
    return config
