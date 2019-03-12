# -------------------------------------------------------------------------------
# Name:        extract_bridges_from_LAS_tbx.py
# Purpose:     wrapper for extract_bridges_from_LAS.py
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
import extract_bridges_from_las
import os
import re

if 'elevation_from_las' in sys.modules:
    importlib.reload(extract_bridges_from_las)
import common_lib
if 'common_lib' in sys.modules:
    importlib.reload(common_lib)  # force reload of the module
import time
from common_lib import create_msg_body, msg, trace

# debugging switches
debugging = 1
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
TOOLNAME = "extract_bridges_from_las"
WARNING = "warning"
ERROR = "error"


# error classes
class MoreThan1Selected(Exception):
    pass


class NoLayerFile(Exception):
    pass


class NoPointLayer(Exception):
    pass


class NoCatenaryLayer(Exception):
    pass


class NoCatenaryOutput(Exception):
    pass


class NoSwaySurfaceOutput(Exception):
    pass


class NoGuideLinesLayer(Exception):
    pass


class NoGuideLinesOutput(Exception):
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


# ----------------------------Main Function---------------------------- #

def main():
    try:
        # Get Attributes from User
        if debugging == 0:
            # User input
            input_las_dataset = arcpy.GetParameterAsText(0)
            class_code = arcpy.GetParameter(1)
            cell_size = arcpy.GetParameterAsText(2)
            output_features = arcpy.GetParameterAsText(3)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            project_ws = aprx.defaultGeodatabase
        else:
            input_las_dataset = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\testing.lasd'
            class_code = 13
            cell_size = str(0.5)
            output_features = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\Testing.gdb\bridges'

            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact'
            project_ws = home_directory + "\\3DFloodImpact.gdb"

        if os.path.exists(home_directory + "\\p20"):  # it is a package
            home_directory = home_directory + "\\p20"

        arcpy.AddMessage("Project Home Directory is: " + home_directory)

        # set directories
        layer_directory = home_directory + "\\layer_files"
        log_directory = home_directory + "\\Logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        #  ensure numerical input is correct
        # fail safe for Europe's comma's
        cell_size = float(re.sub("[,.]", ".", cell_size))

        # rename layer files (for packaging)
        if os.path.exists(layer_directory):
            common_lib.rename_file_extension(layer_directory, ".txt", ".lyrx")

        # Create folders and intermediate gdb, if needed
        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        start_time = time.clock()

        # check if input exists
        if arcpy.Exists(input_las_dataset):

            # extract the elevation layers
            bridges = extract_bridges_from_las.extract(lc_lasd=input_las_dataset,
                                                       lc_ws=scratch_ws,
                                                       lc_class_code=class_code,
                                                       lc_cell_size=float(cell_size),
                                                       lc_output_features=output_features,
                                                       lc_log_dir=log_directory,
                                                       lc_debug=verbose,
                                                       lc_memory_switch=in_memory_switch)

            if bridges:
                if arcpy.Exists(bridges):
                    arcpy.AddMessage("Adding Bridges")

                    output_layer1 = common_lib.get_name_from_feature_class(bridges) + "_surface"
                    arcpy.MakeFeatureLayer_management(bridges, output_layer1)

                    arcpy.SetParameter(3, output_layer1)

                    end_time = time.clock()
                    msg_body = create_msg_body("extract_bridges_from_las completed successfully.", start_time, end_time)
                    msg(msg_body)
                else:
                    end_time = time.clock()
                    msg_body = create_msg_body("No bridge surfaces created. Exiting...", start_time, end_time)
                    msg(msg_body, WARNING)

            arcpy.ClearWorkspaceCache_management()

            if DeleteIntermediateData:
                fcs = common_lib.listFcsInGDB(scratch_ws)
                rs = common_lib.list_rasters_in_gdb(scratch_ws)

                msg_prefix = "Deleting intermediate data..."

                msg_body = common_lib.create_msg_body(msg_prefix, 0, 0)
                common_lib.msg(msg_body)

                for fc in fcs:
                    arcpy.Delete_management(fc)

                for r in rs:
                    arcpy.Delete_management(r)


            # end main code

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

    except NoPointLayer:
        print("Can't find attachment points layer. Exiting...")
        arcpy.AddError("Can't find attachment points layer. Exiting...")

    except NoCatenaryLayer:
        print("Can't find Catenary layer. Exiting...")
        arcpy.AddError("Can't find Catenary layer. Exiting...")

    except NoCatenaryOutput:
        print("Can't create Catenary output. Exiting...")
        arcpy.AddError("Can't create Catenary output. Exiting...")

    except NoSwaySurfaceOutput:
        print("Can't find SwaySurface output. Exiting...")
        arcpy.AddError("Can't find SwaySurface. Exiting...")

    except NoGuideLinesLayer:
        print("Can't find GuideLines output. Exiting...")
        arcpy.AddError("Can't find GuideLines. Exiting...")

    except MoreThan1Selected:
        print("More than 1 line selected. Please select 1 guide line only. Exiting...")
        arcpy.AddError("More than 1 line selected. Please select 1 guide line only. Exiting...")

    except NoGuideLinesOutput:
        print("Can't create GuideLines output. Exiting...")
        arcpy.AddError("Can't create GuideLines. Exiting...")

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
