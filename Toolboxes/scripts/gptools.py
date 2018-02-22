import arcpy
import arcpy.cartography as CA
import time
import os
import scripts.CommonLib as CommonLib
from scripts.CommonLib import create_msg_body, msg, trace
from scripts.settings import *

class Create3DFloodLevel(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create 3D Flood Level"
        self.description = "Creates a 3D Flood Level layer using a " + \
                            "Water Surface elevation as input."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_raster = arcpy.Parameter(displayName="Water Surface Elevation",
                                  name="WaterSurfaceElevation",
                                  datatype="GPRasterLayer",
                                  parameterType="Required",
                                  direction="Input")

        output_fc = arcpy.Parameter(displayName="Output Features",
                                  name="Output Features",
                                  datatype="DEFeatureClass",
                                  parameterType="Required",
                                  direction="Output")

        params = [input_raster, output_fc]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # error classes

        class NoNoDataError(Exception):
            pass

        class LicenseError3D(Exception):
            pass

        class LicenseErrorSpatial(Exception):
            pass

        class SchemaLock(Exception):
            pass

        class NotSupported(Exception):
            pass

        class NoLayerFile(Exception):
            pass

        class FunctionError(Exception):

            pass

        try:

            debugging = 1

            # Get Attributes from User
            if debugging == 0:
                ## User input
                input_var1 = arcpy.GetParameter(0)
                output_var1 = arcpy.GetParameterAsText(1)

                # script variables
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                home_directory = aprx.homeFolder
                tiff_directory = home_directory + "\\Tiffs"
                tin_directory = home_directory + "\\Tins"
                scripts_directory = aprx.homeFolder + "\\Scripts"
                rule_directory = aprx.homeFolder + "\\RulePackages"
                log_directory = aprx.homeFolder + "\\Logs"
                layer_directory = home_directory + "\\LayerFiles"
                project_ws = aprx.defaultGeodatabase

            else:
                # debug
                input_raster = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\WSE_01pct_testarea2'
                output_polygons = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact\Testing130218.gdb\FloodPolys'
                non_flood_value = "NoData"  # value or "NoData"
                outward_buffer = 0
                home_directory = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact'
                tiff_directory = home_directory + "\\Tiffs"
                tin_directory = home_directory + "\\Tins"
                scripts_directory = home_directory + "\\Scripts"
                rule_directory = home_directory + "\\RulePackages"
                log_directory = home_directory + "\\Logs"
                layer_directory = home_directory + "\\LayerFiles"
                project_ws = home_directory + "\\Results.gdb"

            scratch_ws = CommonLib.create_gdb(home_directory, "Intermediate.gdb")
            arcpy.env.workspace = scratch_ws
            arcpy.env.overwriteOutput = True

            if not os.path.exists(tiff_directory):
                os.makedirs(tiff_directory)

            if not os.path.exists(tin_directory):
                os.makedirs(tin_directory)

            CommonLib.set_up_logging(log_directory, TOOLNAME)
            start_time = time.clock()

            if arcpy.CheckExtension("3D") == "Available":
                arcpy.CheckOutExtension("3D")

                if arcpy.CheckExtension("Spatial") == "Available":
                    arcpy.CheckOutExtension("Spatial")

                    # use numeric value for determining non flooded areas: set these values to NoData. We need NoData for clippng later on
                    if non_flood_value != "NoData":
                        msg_body = create_msg_body(
                            "Setting non flood value: " + non_flood_value + " to NoData in copy of " + input_raster + "...",
                            0, 0)
                        msg(msg_body)
                        null_for_non_flooded_areas_raster = os.path.join(scratch_ws, "null_for_flooded")
                        if arcpy.Exists(null_for_non_flooded_areas_raster):
                            arcpy.Delete_management(null_for_non_flooded_areas_raster)

                        whereClause = "VALUE = " + non_flood_value

                        # Execute SetNull
                        outSetNull_temp = arcpy.sa.SetNull(input_raster, input_raster, whereClause)
                        outSetNull_temp.save(null_for_non_flooded_areas_raster)

                        input_raster = null_for_non_flooded_areas_raster
                    else:
                        pass  # we use NoData values for determining flooded areas

                    end_time = time.clock()
                    msg_body = create_msg_body("Create 3D Flood Leveles completed successfully.", start_time, end_time)

                else:
                    raise LicenseErrorSpatial
            else:
                raise LicenseError3D

            arcpy.ClearWorkspaceCache_management()

            msg(msg_body)

        except NoLayerFile:
            print("Can't find Layer file. Exiting...")
            arcpy.AddError("Can't find Layer file. Exiting...")

        except LicenseError3D:
            print("3D Analyst license is unavailable")
            arcpy.AddError("3D Analyst license is unavailable")

        except LicenseErrorSpatial:
            print("Spatial Analyst license is unavailable")
            arcpy.AddError("Spatial Analyst license is unavailable")

        except NoNoDataError:
            print("Input raster does not have NODATA values")
            arcpy.AddError("Input raster does not have NODATA values")

        except arcpy.ExecuteError:
            line, filename, synerror = trace()
            msg("Error on %s" % line, ERROR)
            msg("Error in file name:  %s" % filename, ERROR)
            msg("With error message:  %s" % synerror, ERROR)
            msg("ArcPy Error Message:  %s" % arcpy.GetMessages(2), ERROR)

        except FunctionError as f_e:
            messages = f_e.args[0]
            msg("Error in function:  %s" % messages["function"], ERROR)
            msg("Error on %s" % messages["line"], ERROR)
            msg("Error in file name:  %s" % messages["filename"], ERROR)
            msg("With error message:  %s" % messages["synerror"], ERROR)
            msg("ArcPy Error Message:  %s" % messages["arc"], ERROR)

        except:
            line, filename, synerror = trace()
            msg("Error on %s" % line, ERROR)
            msg("Error in file name:  %s" % filename, ERROR)
            msg("with error message:  %s" % synerror, ERROR)

        finally:
            arcpy.CheckInExtension("3D")
            arcpy.CheckInExtension("Spatial")
        return

class CreateDepthRaster(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Depth Raster"
        self.description = "Create Depth Raster"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        return

# for debug only!
def main():
    tool = Create3DFloodLevel()
    tool.execute(tool.getParameterInfo(),None)

if __name__ == "__main__":
    main()
