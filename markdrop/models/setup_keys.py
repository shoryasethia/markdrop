def setup_keys(key):
    """Interactive function to setup API keys and save them in markdrop/models/.env."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv

    # Dynamically determine the package's root directory
    package_dir = Path(__file__).resolve().parent.parent  # Adjust path to locate 'markdrop'
    models_dir = package_dir / "models"
    env_file = models_dir / ".env"

    # Ensure the models directory exists
    models_dir.mkdir(parents=True, exist_ok=True)

    # Load existing keys
    existing_keys = {}
    if env_file.exists():
        try:
            load_dotenv(env_file)  # Load environment variables
            # Collect existing keys
            for key_name in ["OPENAI_API_KEY", "GOOGLE_API_KEY"]:
                if os.getenv(key_name):
                    existing_keys[key_name] = os.getenv(key_name)
        except Exception as e:
            print(f"Error loading existing keys: {e}")

    print("\nMarkdrop Setup: API Keys")
    print("=========================")

    # Helper function to save all keys to the .env file
    def save_keys_to_env():
        """Save all keys to the .env file with single quotes."""
        try:
            with open(env_file, 'w') as f:
                for item, value in existing_keys.items():
                    f.write(f"{item}='{value}'\n")  # Add single quotes around the value
            print(f"Configuration saved to {env_file}.")
        except Exception as e:
            print(f"Error saving keys: {e}")
            
    # Prompt for OpenAI key
    if key.lower() == 'openai':
        print("OpenAI API Key (Press Enter to skip)")
        if 'OPENAI_API_KEY' in existing_keys:
            print(f"Current: {existing_keys['OPENAI_API_KEY'][:10]}...")
            change = input("Do you want to modify the existing OPENAI_API_KEY [y/n]: ").strip().lower()
            if change in ["y", "yes"]:
                openai_key = input("Enter your OpenAI API key: ").strip()
                if openai_key:
                    existing_keys['OPENAI_API_KEY'] = openai_key
                else:
                    print("No API key provided. Skipping OpenAI setup.")
            else:
                print("Keeping the existing OpenAI API key.")
        else:
            openai_key = input("Enter your OpenAI API key: ").strip()
            if openai_key:
                existing_keys['OPENAI_API_KEY'] = openai_key
            else:
                print("No API key provided. Skipping OpenAI setup.")

    # Prompt for Google/Gemini key
    elif key.lower() == 'google':
        print("\nGoogle/Gemini API Key (Press Enter to skip)")
        if 'GOOGLE_API_KEY' in existing_keys:
            print(f"Current: {existing_keys['GOOGLE_API_KEY'][:10]}...")
            change = input("Do you want to modify the existing GOOGLE_API_KEY [y/n]: ").strip().lower()
            if change in ["y", "yes"]:
                google_key = input("Enter your Google/Gemini API key: ").strip()
                if google_key:
                    existing_keys['GOOGLE_API_KEY'] = google_key
                else:
                    print("No API key provided. Skipping Google setup.")
            else:
                print("Keeping the existing Google API key.")
        else:
            google_key = input("Enter your Google/Gemini API key: ").strip()
            if google_key:
                existing_keys['GOOGLE_API_KEY'] = google_key
            else:
                print("No API key provided. Skipping Google setup.")

    else:
        print("Invalid key type specified. Please choose 'openai' or 'google'.")
        return False

    # Save all keys to the .env file
    save_keys_to_env()

    # Reload environment variables
    try:
        load_dotenv(env_file)
    except Exception as e:
        print(f"Error reloading environment variables: {e}")
        return False

    return True
