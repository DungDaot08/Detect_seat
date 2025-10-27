from setuptools import setup, find_packages

setup(
    name="fastapi_backend",
    version="0.1.0",
    packages=find_packages(include=["app", "app.*"]),
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
    include_package_data=True,
    package_data={
        "app": [
            "utils/TTS/counter_audio/*.mp3",
            "utils/TTS/numbers/*.mp3",
            "utils/TTS/prefix/*.mp3",
        ],
    },
)
