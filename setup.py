from setuptools import setup, find_packages

setup(
    name="ai-assistant",
    version="1.0.0",
    description="AI Assistant MVP with comprehensive testing",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "psycopg2-binary>=2.9.0",
        "redis>=5.0.0",
        "qdrant-client>=1.7.0",
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "asyncpg>=0.29.0",
        "python-multipart>=0.0.6",
        "bcrypt>=4.1.0",
        "passlib>=1.7.4",
        "python-jose[cryptography]>=3.3.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "pytest-xdist>=3.3.0",
            "httpx>=0.27.0",
            "faker>=25.0.0",
            "factory-boy>=3.3.0",
            "testcontainers>=3.7.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ai-assistant=app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
    ],
) 