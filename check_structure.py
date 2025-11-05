import os

def check_project_structure():
    base_dir = os.path.dirname(__file__)
    app_dir = os.path.join(base_dir, 'app')
    
    print("📁 Checking project structure...")
    print(f"Base: {base_dir}")
    print(f"App: {app_dir}")
    
    required_structure = {
        'app/__init__.py': 'Main app package',
        'app/main.py': 'FastAPI app',
        'app/core/__init__.py': 'Core package', 
        'app/core/config.py': 'Configuration',
        'app/core/security.py': 'Security utilities',
        'app/core/encryption.py': 'Encryption utilities',
        'app/database/__init__.py': 'Database package',
        'app/database/supabase_client.py': 'Supabase client',
        'app/models/__init__.py': 'Models package',
        'app/models/user_models.py': 'User models',
        'app/models/chat_models.py': 'Chat models',
        'app/models/message_models.py': 'Message models',
        'app/services/__init__.py': 'Services package',
        'app/services/auth_service.py': 'Auth service',
        'app/services/chat_service.py': 'Chat service', 
        'app/services/encryption_service.py': 'Encryption service',
        'app/api/__init__.py': 'API package',
        'app/api/auth.py': 'Auth routes',
        'app/api/users.py': 'User routes',
        'app/api/chats.py': 'Chat routes',
        'app/api/messages.py': 'Message routes',
    }
    
    missing_files = []
    for file_path, description in required_structure.items():
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} - {description}")
        else:
            print(f"❌ {file_path} - {description} - MISSING!")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} files missing!")
        return False
    else:
        print(f"\n🎉 All {len(required_structure)} files exist!")
        return True

if __name__ == "__main__":
    check_project_structure()