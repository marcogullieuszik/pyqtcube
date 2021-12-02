from setuptools import setup, find_packages
import re

package = "pyqtcube"

with open("README.rst", "r") as readme_file:
    readme = readme_file.read()

requirements = [
    "astropy>=4",
    "PyQt5",
    "pyqtgraph",
    "spectral_cube",
    ]

def find_version(package):
    version_file = open(package + "/__init__.py").read()
    rex = r'__version__\s*=\s*"([^"]+)"'
    return re.search(rex, version_file).group(1)

setup(
    name=package,
    version=find_version(package),
    author="Marco Gullieuszik",
    author_email="marco.gullieuszik@inaf.it",
    description="A spectral datacube visualizer",
    long_description=readme,
    long_description_content_type= 'text/x-rst',
    url="https://github.com/marcogullieuszik/pyqtcube",
    packages=find_packages(),
    python_requires='>3',
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    scripts=['pycube'],
    include_package_data=True,
    package_data={package:["linelist_vacuum_air.txt"]},
)

