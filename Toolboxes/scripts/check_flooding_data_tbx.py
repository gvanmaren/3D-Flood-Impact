# -------------------------------------------------------------------------------
# Name:        check_flooding_data_tbx
# Purpose:     wrapper for check_flooding_data
#
# Author:      Dan Hedges, Chris Wilkins, Gert van Maren
#
# Created:     27/04/12/2017
# Copyright:   (c) Esri 2017
# updated:
# updated:
# updated:

# Required:
#

# -------------------------------------------------------------------------------

import arcpy
import time
import os
import importlib
import scripts.common_lib as common_lib
importlib.reload(common_lib)  # force reload of the module
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
TOOLNAME = "ImportZoningInformation"

# error classes


class LicenseError3D(Exception):
    pass


class LicenseErrorSpatial(Exception):
    pass


class SchemaLock(Exception):
    pass


class NotSupported(Exception):
    pass


class NoInputLayer(Exception):
    pass


class NotProjected(Exception):
    pass


class NoOutput(Exception):
    pass


class FunctionError(Exception):

    """
    Raised when a function fails to run.
    """

    pass


# ----------------------------Main Function---------------------------- #

def main():
    try:
        # Get Attributes from User
        if debugging == 0:
            ## User input
            input_source = arcpy.GetParameterAsText(0)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            log_directory = aprx.homeFolder + "\\Logs"

        else:
            # debug
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\WSE_01pct_testarea2'
            home_directory = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\DevelopmentCapacity\work1.4\DevelopmentCapacity'
            log_directory = home_directory + "\\Logs"

        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        common_lib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            """The source code of the tool."""
            arcpy.AddMessage("Input layer: " + input_source)

            # check if input exists
            if arcpy.Exists(input_source):
                full_path_source = common_lib.get_full_path_from_layer(input_source)
                data_type, shape_type = common_lib.get_raster_featuretype_from_layer(full_path_source)

                if data_type == "FeatureClass":
                    if shape_type == "Polygon":
                        arcpy.AddWarning("Please convert polygons to raster.")
                    else:
                        arcpy.AddWarning("Only polygon feature classes are supported.")

                cs_name, cs_vcs_name, projected = common_lib.get_cs_info(full_path_source, 0)

                if not projected:
                    arcpy.AddWarning("Please re-project your input layer to a projected coordinate system.")

                if not cs_vcs_name:
                    arcpy.AddWarning("Please define a vertical coordinate system.")
            else:
                raise NoInputLayer
        else:
            raise LicenseError3D

        arcpy.ClearWorkspaceCache_management()

        end_time = time.clock()
        msg_body = create_msg_body("check_flooding_data_tbx completed successfully.", start_time, end_time)
        msg(msg_body)

        # end main code

    except NoInputLayer:
        print("Can't find Input layer. Exiting...")
        arcpy.AddError("Can't find Input layer. Exiting...")

    except NotProjected:
        print("Input layer does not have a projected coordinate system. Exiting...")
        arcpy.AddWarning("Input layer does not have a projected coordinate system. Exiting...")

    except NoOutput:
        print("Can't create output. Exiting...")
        arcpy.AddError("Can't create output. Exiting...")

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

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
