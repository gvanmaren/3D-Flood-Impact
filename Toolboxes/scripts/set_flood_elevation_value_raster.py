import arcpy
import time
import os

import re
import scripts.common_lib as common_lib
from scripts.common_lib import create_msg_body, msg, trace
from scripts.settings import *


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


# used functions

def set_value(input_source, no_flood_value, flood_elevation_value, output_raster, debug):
    try:
        # Get Attributes from User
        if debug == 0:
            # script variables
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
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\c2ft_inundation_Clip'
            output_raster = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\Testing.gdb\RasterValue'
            no_flood_value = "0"  # value or "NoData"
            flood_elevation_value = 8
            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact'
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

        flood_elevation_value = float(re.sub("[,.]", ".", flood_elevation_value))

        common_lib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")

                arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(input_source))

                # use numeric value for determining non flooded areas: set these values to NoData. We need NoData for clippng later on
                if no_flood_value != "NoData":
                    if common_lib.is_number(no_flood_value):
                        msg_body = create_msg_body(
                            "Setting no flood value: " + no_flood_value + " to NoData in copy of " + common_lib.get_name_from_feature_class(
                                input_source) + "...", 0, 0)
                        msg(msg_body)
                        null_for_no_flooded_areas_raster = os.path.join(scratch_ws, "null_for_flooded")
                        if arcpy.Exists(null_for_no_flooded_areas_raster):
                            arcpy.Delete_management(null_for_no_flooded_areas_raster)

                        whereClause = "VALUE = " + no_flood_value

                        # Execute SetNull
                        outSetNull_temp = arcpy.sa.SetNull(input_source, input_source, whereClause)
                        outSetNull_temp.save(null_for_no_flooded_areas_raster)

                        input_source = null_for_no_flooded_areas_raster

                    else:
                        raise ValueError

                # check where there is IsNull and set the con values
                is_Null = os.path.join(scratch_ws, "is_Null")
                if arcpy.Exists(is_Null):
                    arcpy.Delete_management(is_Null)

                is_Null_raster = arcpy.sa.IsNull(input_source)
                is_Null_raster.save(is_Null)

                # Con
                if arcpy.Exists(output_raster):
                    arcpy.Delete_management(output_raster)
                temp_con_raster = arcpy.sa.Con(is_Null, input_source, flood_elevation_value)
                temp_con_raster.save(output_raster)

                msg_body = create_msg_body(
                            "Setting flood elevation value to: " + str(flood_elevation_value) + " in " + common_lib.get_name_from_feature_class(output_raster) + "...", 0, 0)
                msg(msg_body)

                return output_raster

                end_time = time.clock()
                msg_body = create_msg_body("Set Flood Elevation Value for Raster completed successfully.", start_time, end_time)
            else:
                raise LicenseErrorSpatial
        else:
            raise LicenseError3D

        arcpy.ClearWorkspaceCache_management()

        msg(msg_body)


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


# for debug only!
if __name__ == "__main__":
    set_value("", "", "", "", 1)