"""setup_keys.py – Interactive API key manager for markdrop providers."""

import getpass
import os

from dotenv import load_dotenv

from .config_paths import get_config_dir, get_env_file_path

# Keys managed per provider
_PROVIDER_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "litellm": "LITELLM_API_KEY",  # used when litellm is configured with a proxy
}


def _prompt_key(key_name: str) -> str:
    return getpass.getpass(f"Enter {key_name}: ").strip()


def setup_keys(provider: str) -> bool:
    """Interactive function to set up API keys and save them in the user config .env."""

    provider = provider.lower()
    if provider not in _PROVIDER_KEYS:
        print(f"Unknown provider '{provider}'. Valid options: {', '.join(_PROVIDER_KEYS)}")
        return False

    key_name = _PROVIDER_KEYS[provider]
    config_dir = get_config_dir()
    env_file = get_env_file_path()
    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing keys
    existing_keys: dict[str, str] = {}
    if env_file.exists():
        try:
            load_dotenv(env_file)
            for k in _PROVIDER_KEYS.values():
                val = os.getenv(k)
                if val:
                    existing_keys[k] = val
        except Exception as e:
            print(f"Warning: could not read existing .env – {e}")

    print(f"\nMarkdrop Setup — {provider.capitalize()} API Key")
    print("=" * 44)

    if key_name in existing_keys:
        masked = existing_keys[key_name][:4] + "****"
        print(f"Current key: {masked}")
        change = input("Modify existing key? [y/N]: ").strip().lower()
        if change in ("y", "yes"):
            new_val = _prompt_key(key_name)
            if new_val:
                existing_keys[key_name] = new_val
            else:
                print("No value entered – keeping existing key.")
        else:
            print("Keeping existing key.")
    else:
        new_val = _prompt_key(key_name)
        if new_val:
            existing_keys[key_name] = new_val
        else:
            print("No value entered. Setup skipped.")
            return False

    try:
        with open(env_file, "w") as f:
            for k, v in existing_keys.items():
                f.write(f"{k}={v}\n")
        try:
            os.chmod(env_file, 0o600)
        except (AttributeError, NotImplementedError, OSError):
            pass
        print(f"Configuration saved to {env_file}.")
    except Exception as e:
        print(f"Error saving keys: {e}")
        return False

    try:
        load_dotenv(env_file, override=True)
    except Exception as e:
        print(f"Warning: could not reload .env – {e}")

    return True
