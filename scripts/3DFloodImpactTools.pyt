import gptools
from gptools import *
import importlib
importlib.reload(gptools)  # force reload of the module

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "3D Flood Impact Tools"
        self.alias = "3D Flood Impact "

        # List of tool classes associated with this toolbox
        self.tools = [Create3DFloodLevel, CreateDepthRaster]


