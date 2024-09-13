from setuptools import setup, find_packages

setup(
    name="mqtt_flow",
    version="1.0.14",
    author="Dishant Arora",
    author_email="dishant.arora1996@gmail.com",
    description="A scalable & modular framework for MQTT message processing in Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rOY369/py-mqtt-data-flow",
    packages=find_packages(),
    install_requires=[
        "paho-mqtt==1.6.1",
        "PyYAML>=5.4",
        "retry",
        "persistqueue",
        # Add other dependencies as needed
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "check-manifest",
            "twine",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
