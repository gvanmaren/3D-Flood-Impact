# -------------------------------------------------------------------------------
# Name:        create_flood_elevation_from_depth_raster_tbx.py
# Purpose:     wrapper for create_flood_elevation_from_depth_raster.py
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
import create_flood_elevation_from_depth_raster
importlib.reload(create_flood_elevation_from_depth_raster)
import common_lib
importlib.reload(common_lib)  # force reload of the module
import time
from common_lib import create_msg_body, msg, trace

# debugging switches
debugging = 1
if debugging:
    enableLogging = True
    DeleteIntermediateData = False
    verbose = 1
    in_memory_switch = True
else:
    enableLogging = False
    DeleteIntermediateData = True
    verbose = 0
    in_memory_switch = False


# constants
ERROR = "error"
TOOLNAME = "CreateFloodElevationFromDepthRaster"
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

            depth_raster = arcpy.GetParameterAsText(0)
            dtm = arcpy.GetParameterAsText(1)
            smooth_factor = arcpy.GetParameter(2)
            output_raster = arcpy.GetParameterAsText(3)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            layer_directory = home_directory + "\\layer_files"
            rule_directory = aprx.homeFolder + "\\rule_packages"
            log_directory = aprx.homeFolder + "\\Logs"
            project_ws = aprx.defaultGeodatabase

        else:
            # debug
            depth_raster = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\data\Vancouver\3DFloodImpact\depth_rasters.gdb\I_0_5pct_nodata_clip_utm'
            dtm = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\data\Vancouver\3DFloodImpact\Surrey_Buildings.gdb\DEM'
            smooth_factor = 30
            output_raster = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.2.3\3DFloodImpact\Testing.gdb\\FloodElevationRaster'

            home_directory = r'D:\\Gert\Work\\Esri\\Solutions\\3DFloodImpact\\work2.1\\3DFloodImpact'
            layer_directory = home_directory + "\\layer_files"
            rule_directory = home_directory + "\\rule_packages"
            log_directory = home_directory + "\\Logs"
            project_ws = home_directory + "\\3DFloodImpact.gdb"

        start_time = time.clock()

        # check if input exists
        if arcpy.Exists(depth_raster):
            full_path_source = common_lib.get_full_path_from_layer(depth_raster)

            flood_elevation_raster = create_flood_elevation_from_depth_raster.create_raster(
                                                depth_raster=depth_raster,
                                                dtm=dtm,
                                                smoothing=smooth_factor,
                                                output_raster=output_raster,
                                                use_in_memory=in_memory_switch,
                                                debug=debugging)

            if arcpy.Exists(flood_elevation_raster):
                    # output_layer = common_lib.get_name_from_feature_class(flood_elevation_raster)
                    # arcpy.MakeRasterLayer_management(flood_elevation_raster, output_layer)
                    #
                    # arcpy.SetParameter(3, output_layer)

                    end_time = time.clock()
                    msg_body = create_msg_body("create_flood_elevation_from_depth_raster completed successfully.", start_time, end_time)
            else:
                raise NoRasterLayer

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
