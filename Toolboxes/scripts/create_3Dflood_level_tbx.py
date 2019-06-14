# -------------------------------------------------------------------------------
# Name:        create_3Dflood_level_tbx.py
# Purpose:     wrapper for create_3Dflood_level.py
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
import create_3Dflood_level
importlib.reload(create_3Dflood_level)
import common_lib
importlib.reload(common_lib)  # force reload of the module
import time
from common_lib import create_msg_body, msg, trace

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
TOOLNAME = "Create3DFloodLevelFromRaster"
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
            no_flood_value = arcpy.GetParameterAsText(1)
            baseline_elevation_raster = arcpy.GetParameter(2)
            baseline_elevation_value = arcpy.GetParameterAsText(3)
            smooth_factor = arcpy.GetParameter(4)
            output_features = arcpy.GetParameterAsText(5)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            layer_directory = home_directory + "\\layer_files"
            rule_directory = aprx.homeFolder + "\\rule_packages"
            log_directory = aprx.homeFolder + "\\Logs"
            project_ws = aprx.defaultGeodatabase
        else:
            # debug
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\3DFloodImpact.gdb\slr_6_ProjectRaster'
            no_flood_value = "NoData"
            baseline_elevation_raster = r''
            baseline_elevation_value = "0"
            smooth_factor = 0
            output_features = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\3DFloodImpact.gdb\FloodPolys'

            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact'
            layer_directory = home_directory + "\\layer_files"
            rule_directory = home_directory + "\\rule_packages"
            log_directory = home_directory + "\\Logs"
            project_ws = home_directory + "\\3DFloodImpact.gdb"

        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            # check if input exists
            if arcpy.Exists(input_source):
                full_path_source = common_lib.get_full_path_from_layer(input_source)
            else:
                raise NoRasterLayer

            # check if input exists
            if arcpy.Exists(baseline_elevation_raster):
                full_path_baseline_raster = common_lib.get_full_path_from_layer(baseline_elevation_raster)
            else:
                full_path_baseline_raster = None

            desc = arcpy.Describe(input_source)

            flood_polygons = create_3Dflood_level.flood_from_raster(input_source=full_path_source,
                                        input_type=desc.dataType,
                                        no_flood_value=no_flood_value,
                                        baseline_elevation_raster=full_path_baseline_raster,
                                        baseline_elevation_value=baseline_elevation_value,
                                        outward_buffer=0,
                                        output_polygons=output_features,
                                        smoothing=smooth_factor,
                                        debug=debugging)

            # create layer, set layer file
            # apply transparency here // checking if symbology layer is present
            z_unit = common_lib.get_z_unit(flood_polygons, verbose)

            if z_unit == "Feet":
                floodSymbologyLayer = layer_directory + "\\flood3Dfeet.lyrx"
            else:
                floodSymbologyLayer = layer_directory + "\\flood3Dmeter.lyrx"

            output_layer = common_lib.get_name_from_feature_class(flood_polygons)
            arcpy.MakeFeatureLayer_management(flood_polygons, output_layer)

            if arcpy.Exists(floodSymbologyLayer):
                arcpy.ApplySymbologyFromLayer_management(output_layer, floodSymbologyLayer)
            else:
                msg_body = create_msg_body("Can't find" + floodSymbologyLayer + " in " + layer_directory, 0, 0)
                msg(msg_body, WARNING)

            if output_layer:
                if z_unit == "Feet":
                    arcpy.SetParameter(6, output_layer)
                else:
                    arcpy.SetParameter(7, output_layer)
            else:
                raise NoOutput

            end_time = time.clock()
            msg_body = create_msg_body("create_3Dflood_level_tbx completed successfully.", start_time, end_time)

        else:
            raise LicenseError3D

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
