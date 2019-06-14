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
        self.params[7].value = True
        self.params[7].enabled = False
        self.params[8].value = None
        self.params[8].enabled = False

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""

        if self.params[1].value:
            if arcpy.Exists(self.params[1].value):
                try:
                    min_value = arcpy.GetRasterProperties_management(self.params[1].value, "MINIMUM")[0]

                    if str(self.params[8].value) != str(self.params[1].value):
                        self.params[7].value = True
                        self.params[8].value = str(self.params[1].value)
                    else:
                        self.params[7].value = False

                    if str(min_value) == "0":
                        if self.params[7].value == True:
                            self.params[2].value = True
                            self.params[3].enabled = True
                            self.params[7].value = False
                    else:
                        self.params[2].value = False
                        self.params[3].enabled = False

                except arcpy.ExecuteError:
                    pass

        if self.params[2].value == True:
            self.params[3].enabled = True
        else:
            self.params[3].enabled = False

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        if self.params[1].value:
            if arcpy.Exists(self.params[1].value):
                try:
                    arcpy.GetRasterProperties_management(self.params[1].value, "MINIMUM")[0]
                except arcpy.ExecuteError:
                    self.params[1].setErrorMessage(
                        'No statistics exists for input surface. Please use the Calculate Statistics tool first to calculate statistics.')

        if self.params[3].enabled == True:
            if not self.params[3].value:
                self.params[3].setErrorMessage(
                    'DEM must be set in case of HAND raster.')