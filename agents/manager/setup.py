from setuptools import setup, find_packages

setup(
    name="manager_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo==4.5.0",
        "dnspython==2.4.2",
        "python-dotenv==1.0.0",
        "pandas==2.0.3",
        "numpy==1.24.4",
        "requests==2.31.0",
        "fastapi==0.100.0",
        "uvicorn==0.23.1",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "python-multipart==0.0.6",
        "yfinance==0.2.28",
        "jinja2==3.1.2",
        "pydantic==2.4.2",
        "anthropic==0.19.1",
        "matplotlib==3.7.2",
        "seaborn==0.12.2",
        "httpx==0.24.1",
    ],
    author="AI Hedge Fund Team",
    description="Manager Agent for AI Hedge Fund",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)