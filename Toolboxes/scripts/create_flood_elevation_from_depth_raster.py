import arcpy
import time
import os

import re
import common_lib
from common_lib import create_msg_body, msg, trace
from settings import *


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

def create_raster(depth_raster, dtm, smoothing, output_raster, use_in_memory, debug):
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
            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.2.3\3DFloodImpact'
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

                arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(depth_raster))
                arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(dtm))

                # add depth raster and DTM together
                if use_in_memory:
                    plus_raster = "in_memory/depth_plus_dtm"
                else:
                    plus_raster = os.path.join(scratch_ws, "depth_plus_dtm")
                    if arcpy.Exists(plus_raster):
                        arcpy.Delete_management(plus_raster)

                arcpy.Plus_3d(depth_raster, dtm, plus_raster)

                # smooth result using focal stats
                if use_in_memory:
                    focal_raster = "in_memory/focal_raster"
                else:
                    focal_raster = os.path.join(scratch_ws, "focal_raster")
                    if arcpy.Exists(focal_raster):
                        arcpy.Delete_management(focal_raster)

                if not (1 <= smoothing <= 100):
                    smoothing = 30

                neighborhood = arcpy.sa.NbrRectangle(smoothing, smoothing, "CELL")

                flood_elev_raster = arcpy.sa.FocalStatistics(plus_raster, neighborhood, "MEAN", "true")
                flood_elev_raster.save(focal_raster)

                # clip with IsNull from depth because we don't want DEM values where there is no depth.
                if use_in_memory:
                    is_null = "in_memory/is_null"
                else:
                    is_null = os.path.join(scratch_ws, "is_null")
                    if arcpy.Exists(is_null):
                        arcpy.Delete_management(is_null)

                is_null_raster = arcpy.sa.IsNull(depth_raster)
                is_null_raster.save(is_null)

                # con
                output = arcpy.sa.Con(is_null, depth_raster, flood_elev_raster)
                output.save(output_raster)

                end_time = time.clock()
                msg_body = create_msg_body("Create Flood Elevation Raster From Depth Raster completed successfully.", start_time, end_time)

                if use_in_memory:
                    arcpy.Delete_management("in_memory")

                arcpy.ClearWorkspaceCache_management()

#                return output_raster

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