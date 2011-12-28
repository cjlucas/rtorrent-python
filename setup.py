from setuptools import setup, find_packages
import os, sys

version = __import__('rtorrent').__version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

required_pkgs = []

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Communications :: File Sharing",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

setup(
    name="rtorrent-python",
    version=version,
    url='https://github.com/cjlucas/rtorrent-python',
    author='Chris Lucas',
    author_email='chris@chrisjlucas.com',
    maintainer='Chris Lucas',
    maintainer_email='chris@chrisjlucas.com',
    description='A simple rTorrent interface written in Python',
    long_description=read("README.md"),
    keywords="rtorrent p2p",
    license="MIT",
    packages=find_packages(),
    scripts=[],
    install_requires=required_pkgs,
    classifiers=classifiers,
    include_package_data=True,
)
