import arcpy


class ToolValidator(object):
    """Class for validating a tool's parameter values and controlling
    the behavior of the tool's dialog."""

    def __init__(self):
        """Setup arcpy and the list of tool parameters."""
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        """Refine the properties of a tool's parameters. This method is
        called when the tool is opened."""

        self.params[2].value = False
        self.params[3].enabled = False
        self.params[6].value = True
        self.params[6].enabled = False
        self.params[7].value = ""
        self.params[7].enabled = False

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""

        if self.params[1].value:
            if arcpy.Exists(self.params[1].value):
                min_value = arcpy.GetRasterProperties_management(self.params[1].value, "MINIMUM")[0]
                #                self.params[7].value = self.params[1].value

                if str(self.params[7].value) != str(self.params[1].value):
                    self.params[6].value = True
                    self.params[7].value = self.params[1].value
                else:
                    self.params[6].value = False

                if str(min_value) == "0":
                    if self.params[6].value == True:
                        self.params[2].value = True
                        self.params[3].enabled = True
                        self.params[6].value = False
                else:
                    self.params[2].value = False
                    self.params[3].enabled = False

        if self.params[2].value == True:
            self.params[3].enabled = True
        else:
            self.params[3].enabled = False

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        if self.params[3].enabled == True:
            if not self.params[3].value:
                self.params[3].setErrorMessage(
                    'DEM must be set in case of HAND raster.')