
import xml.etree.ElementTree as ET
import os

def get_version():
	pkg_path = os.path.join(os.path.dirname(__file__), "package.xml")
	tree = ET.parse(pkg_path)
	root = tree.getroot()
	version_tag = root.find("{https://wiki.freecad.org/Package_Metadata}version")
	return version_tag.text if version_tag is not None else "unknown"

__version__ = get_version()
