
from setuptools import setup, find_packages
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
import chimg

def long_desc():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

setup(name="cloud-hypervisor-tools",
      version=chimg.__version__,
      description="Cloud Hypervisor Tools",
      long_description=long_desc(),
      long_description_content_type="text/markdown",
      url="https://github.com/weltling/cloud-hypervisor-tools",
      author="Anatol Belski",
      author_email="anbelski@linux.microsoft.com",
      license="BSD-2-Clause",
      package_dir={"": "src"},
      packages=find_packages("src"),
      entry_points={
      "console_scripts":[
          "chimg = chimg.cli:main",
      ]},
      install_requires=[
          "parse",
      ],
      zip_safe=False)
