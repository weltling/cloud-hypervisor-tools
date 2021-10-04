
from setuptools import setup, find_packages
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
import vmimg

def long_desc():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

setup(name="vmimg",
      version=vmimg.__version__,
      description="VM disk image utils",
      long_description=long_desc(),
      long_description_content_type="text/markdown",
      url="https://github.com/weltling/vmimg",
      author="Anatol Belski",
      author_email="anbelski@linux.microsoft.com",
      license="BSD-2-Clause",
      package_dir={"": "src"},
      packages=find_packages("src"),
      entry_points={
      "console_scripts":[
          "vmimg = vmimg.cli:main",
      ]},
      install_requires=[
          "parse",
      ]
      zip_safe=False)
