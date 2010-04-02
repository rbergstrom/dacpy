from setuptools import setup, find_packages
import sys, os

version = '0.1'

classifiers = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Natural Language :: English
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Multimedia :: Sound/Audio
Topic :: Home Automation
"""

setup(name='dacpy',
      version=version,
      description="Python DACP Implementation",
      long_description="""Implementation of Apple's Digital Audio Control Protocol in Python""",
      classifiers=classifiers,
      keywords='dacp',
      author='Ryan Bergstrom',
      author_email='ryan@bergstrom.ca',
      url='http://www.github.com/rbergstrom/dacpy',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
