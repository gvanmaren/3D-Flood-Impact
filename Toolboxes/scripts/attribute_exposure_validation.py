import arcpy
from openpyxl import load_workbook
import os

RISKTABLENAME = "riskTypeTable.xlsx"
RISKTABLERINSHEET = "riskLevels"

aprx = arcpy.mp.ArcGISProject("CURRENT")
home_directory = aprx.homeFolder
table_directory = home_directory + "\\tables"
inRiskTable = os.path.join(table_directory, RISKTABLENAME)


class ToolValidator(object):
    """Class for validating a tool's parameter values and controlling
    the behavior of the tool's dialog."""

    def __init__(self):
        """Setup arcpy and the list of tool parameters."""
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        """Refine the properties of a tool's parameters. This method is
        called when the tool is opened."""

        self.params[1].enabled = False
        self.params[8].value = 1
        self.params[14].value = False
        self.params[16].value = False
        self.params[24].value = False
        self.params[25].value = False
        self.params[26].value = False

        self.params[2].enabled = False
        self.params[8].enabled = False
        self.params[14].enabled = False
        self.params[16].enabled = False
        self.params[24].enabled = False
        self.params[25].enabled = False
        self.params[26].enabled = False

        # load riskType table
        workbook = load_workbook(inRiskTable)
        worksheet = workbook[RISKTABLERINSHEET]
        riskList = []

        first_column = worksheet['A']

        # add A column to UI
        for x in range(len(first_column)):
            if first_column[x].value != "riskType":
                riskList.append((first_column[x].value))

        self.params[0].filter.list = riskList

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""

        self.params[1].enabled = False

        if self.params[3].value:
            self.params[21].value = True

        if self.params[10].value:
            self.params[27].value = True

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        if not self.params[3].value and self.params[21].value == True:
            self.params[21].setErrorMessage('Water Surface Geodatabase must be set.')

        if not self.params[9].value and self.params[22].value == True:
            self.params[22].setErrorMessage('DEM raster must be set.')

        if not self.params[9].value and self.params[23].value == True:
            self.params[23].setErrorMessage('DEM raster must be set.')

        if not self.params[10].value and self.params[27].value == True:
            self.params[27].setErrorMessage('Flood Loss Potential table must be set.')