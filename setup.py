from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="maaps-auditor",
    version="1.0.0",
    author="Scott Mills",
    author_email="scott@sgmstudios.ca",
    description="MAAPS Auditor Agent: Local DSP audio analysis and quality gatekeeper.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sgm-audio/auditor-agent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "librosa>=0.10.0",
        "pyloudnorm>=0.1.1",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "maaps-auditor=auditor_agent.cli:main",
        ],
    },
)
