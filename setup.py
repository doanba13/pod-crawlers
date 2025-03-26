from setuptools import setup, find_packages

setup(
    name="pod-crawl",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "schedule==1.2.1",
        "pydantic>=2.5.3",
        "python-dateutil==2.8.2",
    ],
) 