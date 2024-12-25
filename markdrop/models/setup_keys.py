def setup_keys():
    """Interactive function to setup API keys"""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    config_dir = Path.home() / '.markdrop'
    config_dir.mkdir(exist_ok=True)
    env_file = config_dir / '.env'
    
    # Load existing keys
    existing_keys = {}
    if env_file.exists():
        load_dotenv(env_file)
        if os.getenv('OPENAI_API_KEY'):
            existing_keys['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('GOOGLE_API_KEY'):
            existing_keys['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
    
    print("\nMarkdrop Setup: API Keys")
    print("=================")
    
    # Prompt for OpenAI key
    print("\n1. OpenAI API Key (Press Enter to skip)")
    if 'OPENAI_API_KEY' in existing_keys:
        print(f"Current: {existing_keys['OPENAI_API_KEY'][:10]}...")
    openai_key = input("Enter your OpenAI API key: ").strip()
    if openai_key:
        existing_keys['OPENAI_API_KEY'] = openai_key
        
    # Prompt for Google/Gemini key
    print("\n2. Google/Gemini API Key (Press Enter to skip)")
    if 'GOOGLE_API_KEY' in existing_keys:
        print(f"Current: {existing_keys['GOOGLE_API_KEY'][:10]}...")
    google_key = input("Enter your Google API key: ").strip()
    if google_key:
        existing_keys['GOOGLE_API_KEY'] = google_key
    
    if not existing_keys:
        print("\nNo API keys were provided.")
        return False
        
    # Write to .env file
    with open(env_file, 'w') as f:
        for key, value in existing_keys.items():
            f.write(f"{key}={value}\n")
    
    print(f"\nConfiguration saved to {env_file}")
    print("You can modify these keys anytime by editing this file.")
    
    # Reload environment variables
    load_dotenv(env_file)
    
    return True