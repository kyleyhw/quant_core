from setuptools import setup, find_packages

setup(
    name="ibkr_quant_core",
    version="1.0.0",
    description="A market-agnostic algorithmic trading framework with an initial implementation for Interactive Brokers.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/your_username/ibkr_quant_core",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pandas",
        "numpy",
        "backtesting",
        "xgboost",
        "scikit-learn",
        "python-dotenv",
        "requests",
        "tabulate",
        "statsmodels",
        "matplotlib",
        "seaborn",
        "ta-lib",
        "yfinance",
        "hmmlearn"
    ],
    extras_require={
        "ibkr": ["ib_insync"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Scrapy",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires='>=3.8',
)
