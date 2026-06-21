from .multi_user_config import MultiUserConfig
from .single_user_config import SingleUserConfig

type UserConfig = SingleUserConfig | MultiUserConfig
"""User configuration for single or multi mode."""
