# -------------------------------------------------------------------------------
# Name:        calculate_height_above_surface_tbx.py
# Purpose:     wrapper for calculate_height_above_surface.py
#
# Author:      Gert van Maren
#
# Created:     04/03/2019
# Copyright:   (c) Esri 2019
# updated:
# updated:
# updated:

# Required:
#

# -------------------------------------------------------------------------------

import arcpy
import sys
import importlib
import calculate_height_above_water_surface
import os
import time
import common_lib
from common_lib import create_msg_body, msg, trace

if 'calculate_height_above_water_surface' in sys.modules:
    importlib.reload(calculate_height_above_water_surface)

if 'common_lib' in sys.modules:
    importlib.reload(common_lib)  # force reload of the module


# debugging switches
debugging = 0
if debugging == 1:
    enableLogging = True
    DeleteIntermediateData = False
    verbose = 1
    in_memory_switch = False
else:
    enableLogging = False
    DeleteIntermediateData = True
    verbose = 0
    in_memory_switch = True


# constants
TOOLNAME = "calculate_height_above_surface"
WARNING = "warning"
ERROR = "error"


# error classes
class MoreThan1Selected(Exception):
    pass


class NoLayerFile(Exception):
    pass


class NoPointLayer(Exception):
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
    pass


class No3DFeatures(Exception):
    pass


class NoRaster(Exception):
    pass


# ----------------------------Main Function---------------------------- #

def main():
    try:
        # Get Attributes from User
        if debugging == 0:
            # User input
            input_features = arcpy.GetParameterAsText(0)
            input_surface = arcpy.GetParameter(1)
            output_features = arcpy.GetParameterAsText(2)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            project_ws = aprx.defaultGeodatabase
            tin_directory = home_directory + "\TINs"
        else:
            input_features = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\Testing.gdb\bridges_test_surfaces'
            input_surface = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\ArcHydro\TSDepth\wse_28'
            output_features = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\Testing.gdb\bridges_HAS'

            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact'
            project_ws = home_directory + "\\3DFloodImpact.gdb"
            tin_directory = home_directory + "\TINs"

        if os.path.exists(home_directory + "\\p20"):  # it is a package
            home_directory = home_directory + "\\p20"
        if not os.path.exists(tin_directory):
            os.makedirs(tin_directory)

        arcpy.AddMessage("Project Home Directory is: " + home_directory)

        # set directories
        layer_directory = home_directory + "\\layer_files"
        log_directory = home_directory + "\\Logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # rename layer files (for packaging)
        if os.path.exists(layer_directory):
            common_lib.rename_file_extension(layer_directory, ".txt", ".lyrx")

        # Create folders and intermediate gdb, if needed
        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        start_time = time.clock()

        # check if input exists
        if arcpy.Exists(input_features):
            if arcpy.Exists(input_surface):

                z_values = arcpy.Describe(input_features).hasZ

                if z_values:
                    # extract the elevation layers
                    bridges, bridge_points = calculate_height_above_water_surface.calculate_height(lc_input_features=input_features,
                                                                              lc_ws=scratch_ws,
                                                                              lc_tin_dir=tin_directory,
                                                                              lc_input_surface=input_surface,
                                                                              lc_output_features=output_features,
                                                                              lc_log_dir=log_directory,
                                                                              lc_debug=verbose,
                                                                              lc_memory_switch=in_memory_switch)

                    if bridges and bridge_points:
                        # add symbology to points and add layer
                        output_layer1 = common_lib.get_name_from_feature_class(bridges)
                        arcpy.MakeFeatureLayer_management(bridges, output_layer1)

                        output_layer2 = common_lib.get_name_from_feature_class(bridge_points)
                        arcpy.MakeFeatureLayer_management(bridge_points, output_layer2)

                        symbology_layer = layer_directory + "\\has_labels.lyrx"

                        if arcpy.Exists(symbology_layer):
                            arcpy.ApplySymbologyFromLayer_management(output_layer2, symbology_layer)
                        else:
                            msg_body = create_msg_body("Can't find" + symbology_layer + " in " + layer_directory, 0,
                                                       0)
                            msg(msg_body, WARNING)

                        arcpy.SetParameter(3, output_layer1)
                        arcpy.SetParameter(4, output_layer2)

                        end_time = time.clock()
                        msg_body = create_msg_body("calculate_height_above_water_surface completed successfully.",
                                                   start_time, end_time)
                        msg(msg_body)
                    else:
                        end_time = time.clock()
                        msg_body = create_msg_body("No bridge surfaces and points created. Exiting...", start_time, end_time)
                        msg(msg_body, WARNING)

                    arcpy.ClearWorkspaceCache_management()

                    if DeleteIntermediateData:
                        fcs = common_lib.listFcsInGDB(scratch_ws)
                        rs = common_lib.list_rasters_in_gdb(scratch_ws, verbose)

                        msg_prefix = "Deleting intermediate data..."

                        msg_body = common_lib.create_msg_body(msg_prefix, 0, 0)
                        common_lib.msg(msg_body)

                        for fc in fcs:
                            arcpy.Delete_management(fc)

                        for r in rs:
                            arcpy.Delete_management(r)
                else:
                    raise NoRaster
            else:
                raise No3DFeatures

            # end main code

    except No3DFeatures:
            # The input has no 3D features
            #
            print('2D features are not supported. Make sure the input layer is a PolygonZ feature class.')
            arcpy.AddError('2D features are not supported. Make sure the input layer is a PolygonZ feature class.')

    except NoRaster:
        # Can't find input raster
        #
        print("Can't find input raster.")
        arcpy.AddError("Can't find input raster.")

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

    except NoPointLayer:
        print("Can't find attachment points layer. Exiting...")
        arcpy.AddError("Can't find attachment points layer. Exiting...")

    except MoreThan1Selected:
        print("More than 1 line selected. Please select 1 guide line only. Exiting...")
        arcpy.AddError("More than 1 line selected. Please select 1 guide line only. Exiting...")

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
