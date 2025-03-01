from setuptools import setup, find_packages

setup(
    name="portfolio_manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo==4.5.0",
        "dnspython==2.4.2",
        "python-dotenv==1.0.0",
        "fastapi==0.100.0",
        "uvicorn==0.23.1",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "python-multipart==0.0.6",
        "pydantic==2.4.2",
        "pandas==2.0.3",
        "numpy==1.24.4",
    ],
    author="AI Hedge Fund Team",
    description="Portfolio Manager Agent for AI Hedge Fund",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)