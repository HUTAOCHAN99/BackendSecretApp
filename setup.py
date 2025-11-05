from setuptools import setup, find_packages

setup(
    name="secret_chat_backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "supabase==2.3.1",
        "python-jose[cryptography]==3.3.0",
        "cryptography==41.0.7",
        "python-dotenv==1.0.0",
        "python-multipart==0.0.6",
        "pydantic==2.5.0",
    ],
    python_requires=">=3.8",
)