# -------------------------------------------------------------------------------
# Name:        set_flood_elevation_value_raster_tbx.py
# Purpose:     wrapper for set_flood_elevation_value_raster.py
#
# Author:      Gert van Maren
#
# Created:     04/04/12/2018
# Copyright:   (c) Esri 2018
# updated:
# updated:
# updated:

# Required:
#

# -------------------------------------------------------------------------------

import arcpy
import importlib
import scripts.set_flood_elevation_value_raster as set_flood_elevation_value_raster
importlib.reload(set_flood_elevation_value_raster)
import scripts.common_lib as common_lib
importlib.reload(common_lib)  # force reload of the module
import time
from scripts.common_lib import create_msg_body, msg, trace

# debugging switches
debugging = 0
if debugging:
    enableLogging = True
    DeleteIntermediateData = False
    verbose = 1
    in_memory_switch = False
else:
    enableLogging = False
    DeleteIntermediateData = True
    verbose = 0
    in_memory_switch = False


# constants
ERROR = "error"
TOOLNAME = "SetFloodElevationValueRaster"
WARNING = "warning"

# error classes

class NoLayerFile(Exception):
    pass


class NoRasterLayer(Exception):
    pass


class NoOutput(Exception):
    pass


class LicenseError3D(Exception):
    pass


class LicenseErrorSpatial(Exception):
    pass


class SchemaLock(Exception):
    pass


class NotSupported(Exception):
    pass


class FunctionError(Exception):

    """
    Raised when a function fails to run.
    """

    pass


def template_function(local_var1, local_var2, local_verbose):

    if local_verbose == 1:
        msg("--------------------------")
        msg("Executing template_function...")

    start_time = time.clock()

    try:
        i = 0
        msg_prefix = ""
        failed = True

        # your function code

        msg_prefix = "Function create_3Dflood_level_tbx completed successfully."
        failed = False
        return 0

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "create_3Dflood_level_tbx",
                "line": line,
                "filename": filename,
                "synerror": synerror,
                "arc": str(arcpy.GetMessages(2))
            }
        )

    finally:
        end_time = time.clock()
        msg_body = create_msg_body(msg_prefix, start_time, end_time)
        if failed:
            msg(msg_body, ERROR)
        else:
            if local_verbose == 1:
                msg(msg_body)
            pass


# ----------------------------Main Function---------------------------- #

def main():
    try:
        # Get Attributes from User
        if debugging == 0:
            ## User input
            input_source = arcpy.GetParameter(0)
            no_flood_value =  arcpy.GetParameterAsText(1)
            flood_elevation_value = arcpy.GetParameterAsText(2)
            output_features = arcpy.GetParameterAsText(3)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            layer_directory = home_directory + "\\layer_files"
            rule_directory = aprx.homeFolder + "\\rule_packages"
            log_directory = aprx.homeFolder + "\\Logs"
            project_ws = aprx.defaultGeodatabase

        else:
            # debug
            input_source = r'D:\\Gert\\Work\\Esri\\Solutions\\3DFloodImpact\\work2.1\\3DFloodImpact\\3DFloodImpact.gdb\\WSE_01pct_testarea2'
            flood_elevation_value = 5
            no_flood_value = "NoData"
            output_features = r'D:\\Gert\\Work\\Esri\\Solutions\\3DFloodImpact\\work2.1\\3DFloodImpact\\Testing.gdb\\FloodElevationRaster'

            home_directory = r'D:\\Gert\Work\\Esri\\Solutions\\3DFloodImpact\\work2.1\\3DFloodImpact'
            layer_directory = home_directory + "\\layer_files"
            rule_directory = home_directory + "\\rule_packages"
            log_directory = home_directory + "\\Logs"
            project_ws = home_directory + "\\3DFloodImpact.gdb"

        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        start_time = time.clock()

        # check if input exists
        if arcpy.Exists(input_source):
            full_path_source = common_lib.get_full_path_from_layer(input_source)
        else:
            raise NoRasterLayer

        desc = arcpy.Describe(input_source)

        flood_raster = set_flood_elevation_value_raster.set_value(input_source=full_path_source,
                                    no_flood_value=no_flood_value,
                                    flood_elevation_value=flood_elevation_value,
                                    output_raster=output_features, debug=0)

        if arcpy.Exists(flood_raster):
                output_layer = common_lib.get_name_from_feature_class(flood_raster)
                arcpy.MakeRasterLayer_management(flood_raster, output_layer)

                arcpy.SetParameter(4, output_layer)

                end_time = time.clock()
                msg_body = create_msg_body("set_flood_elevation_value_raster_tbx completed successfully.", start_time, end_time)
        else:
            raise NoRasterLayer

        arcpy.ClearWorkspaceCache_management()

        # end main code

        msg(msg_body)

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

    except NoRasterLayer:
        print("Can't find Raster layer. Exiting...")
        arcpy.AddError("Can't find Raster layer. Exiting...")

    except NoOutput:
        print("Can't create output. Exiting...")
        arcpy.AddError("Can't create output. Exiting...")

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

if __name__ == '__main__':

    main()
