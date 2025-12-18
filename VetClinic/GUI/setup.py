from setuptools import setup, find_packages

setup(
    name="vetclinic_gui",
    version="0.1.0",
    author="PSK Proj",
    description="VetClinic PyQt6 client application",
    packages=find_packages(include=["vetclinic_gui", "vetclinic_gui.*"]),
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.7.0",
        "vetclinic_api>=0.1.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: PyQt6",
        "License :: OSI Approved :: MIT License"
    ],
    entry_points={
        "gui_scripts": [
            "vetclinic-gui = vetclinic_gui.main:main"
        ]
    }
)
