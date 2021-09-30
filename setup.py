
from setuptools import setup

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
      packages=["vmimg"],
      scripts=[
        "bin/vmimg",
      ],
      zip_safe=False)
