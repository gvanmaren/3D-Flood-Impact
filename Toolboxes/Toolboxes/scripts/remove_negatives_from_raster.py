import arcpy
import time
import os

import re
import common_lib
from common_lib import create_msg_body, msg, trace
from settings import *

debug = 0

# error classes
class NotProjected(Exception):
    pass


class NoNoDataError(Exception):
    pass


class LicenseError3D(Exception):
    pass


class LicenseErrorSpatial(Exception):
    pass


class NoUnits(Exception):
    pass


class NoPolygons(Exception):
    pass


class SchemaLock(Exception):
    pass


class NotSupported(Exception):
    pass


class NoLayerFile(Exception):
    pass


class FunctionError(Exception):
    pass


# MAIN
try:
    # Get Attributes from User
    if debug == 0:
        # script variables
        input_raster = arcpy.GetParameterAsText(0)
        replace_value = arcpy.GetParameterAsText(1)
        output_raster = arcpy.GetParameterAsText(2)

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        home_directory = aprx.homeFolder
        tiff_directory = home_directory + "\\Tiffs"
        tin_directory = home_directory + "\\Tins"
        scripts_directory = aprx.homeFolder + "\\Scripts"
        rule_directory = aprx.homeFolder + "\\rule_packages"
        log_directory = aprx.homeFolder + "\\Logs"
        layer_directory = home_directory + "\\layer_files"
        project_ws = aprx.defaultGeodatabase

        enableLogging = True
        DeleteIntermediateData = True
        verbose = 0
        in_memory_switch = True
    else:
        # debug
        input_raster = r''
        replace_value = str(0)
        output_raster = r'D:\\Gert\\Work\\Esri\\Solutions\\3DFloodImpact\\work2.2\\3DFloodImpact\\Testing.gdb\\DepthNoNegsRaster'
        home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.2\3DFloodImpact'
        log_directory = home_directory + "\\Logs"
        layer_directory = home_directory + "\\LayerFiles"
        project_ws = home_directory + "\\Testing.gdb"

        enableLogging = False
        DeleteIntermediateData = True
        verbose = 1
        in_memory_switch = False

    scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
    arcpy.env.workspace = scratch_ws
    arcpy.env.overwriteOutput = True

    common_lib.set_up_logging(log_directory, TOOLNAME)
    start_time = time.clock()

    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")

        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")

            arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(input_raster))

            if replace_value != "NoData":
                if not common_lib.is_number(replace_value):
                    raise ValueError
                else:
                    txt_replace_value = str(replace_value)
            else:
                txt_replace_value = "NoData"
                replace_value = ""

            msg_body = create_msg_body(
                    "Setting replacement value for negative raster values to: " + txt_replace_value + " in " + output_raster + "...", 0, 0)
            msg(msg_body)

            # con on mosaic
            myConRaster = arcpy.sa.Con(input_raster, input_raster, replace_value, "VALUE >= 0")
            myConRaster.save(output_raster)

            if arcpy.Exists(output_raster):
#                output_layer = common_lib.get_name_from_feature_class(output_raster) + "no_negative"
#                arcpy.MakeRasterLayer_management(output_raster, output_layer)

#                arcpy.SetParameter(3, output_layer)

                end_time = time.clock()
                msg_body = create_msg_body("Remove negative values from raster completed successfully.", start_time, end_time)
                msg(msg_body)
            else:
                end_time = time.clock()
                msg_body = create_msg_body("Error in Remove negative values from raster.", start_time, end_time)
                msg(msg_body)

            arcpy.ClearWorkspaceCache_management()

        else:
            raise LicenseErrorSpatial
    else:
        raise LicenseError3D

    arcpy.ClearWorkspaceCache_management()


except NotProjected:
    print("Input data needs to be in a projected coordinate system. Exiting...")
    arcpy.AddError("Input data needs to be in a projected coordinate system. Exiting...")

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

except NoUnits:
    print("No units detected on input data")
    arcpy.AddError("No units detected on input data")

except NoPolygons:
    print("Input data can only be polygon features or raster datasets.")
    arcpy.AddError("Input data can only be polygon features or raster datasets.")

except ValueError:
    print("Input no flood value is not a number.")
    arcpy.AddError("Input no flood value is not a number.")

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
