from setuptools import setup, find_packages

setup(
    name="fastapi_backend",
    version="0.1.0",
    packages=find_packages(),  # sẽ tự động include app.utils, app.models, ...
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "typing_inspect",
    ],
    entry_points={
        "console_scripts": [
            "start=app.start:main",
        ],
    },
)
