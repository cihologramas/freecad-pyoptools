from setuptools import setup
import os
# from freecad.workbench_starterkit.version import __version__
# name: this is the name of the distribution.
# Packages using the same name here cannot be installed together

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                            "version.py")
with open(version_path) as fp:
    exec(fp.read())

setup(name='freecad.pyoptools',
      version=str(__version__),
      packages=['freecad',
                'freecad.pyoptools'],
      maintainer="Ricardo Amézquita Orozco",
      maintainer_email="ramezquitao@cihologramas.com",
      #url="https://github.com/FreeCAD/Workbench-Starterkit",
      description="Workbenck for pyOpTools",
      install_requires=['numpy'], # should be satisfied by FreeCAD's system dependencies already
      include_package_data=True)
