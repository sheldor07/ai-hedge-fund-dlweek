from setuptools import setup, find_packages

setup(
    name="stock_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo>=4.5.0",
        "dnspython>=2.4.2",
        "python-dotenv>=1.0.0",
        "pandas>=2.0.3",
        "numpy>=1.24.4",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "matplotlib>=3.7.2",
        "seaborn>=0.12.2",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.1",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "python-multipart>=0.0.6",
        "yfinance>=0.2.28",
        "sec-api>=1.0.17",
        "newsapi-python>=0.2.7",
        "fredapi>=0.5.1",
        "jinja2>=3.1.2",
        "pydantic>=2.4.2",
    ],
    author="Shrivardhan Goenka",
    author_email="shrivardhangoenka@example.com",
    description="A fundamental analysis agent for analyzing US stocks",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)