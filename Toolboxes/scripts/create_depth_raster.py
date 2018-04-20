import arcpy
import time
import os
import re

import sys
import scripts.common_lib as common_lib
from scripts.common_lib import create_msg_body, msg, trace
from scripts.settings import *

use_in_memory = True

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


class NoInputLayer(Exception):
    pass


class NoDepthRaster(Exception):
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

WARNING = "warning"

# used functions

def create_raster(input_source, depth_raster, depth_value, output_raster, debug):
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
            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact'
            tiff_directory = home_directory + "\\Tiffs"
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

        # fail safe for Eurpose's comma's
        depth_value = float(re.sub("[,.]", ".", depth_value))

        bail = 0

        common_lib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")

                # check if input exists
                if arcpy.Exists(input_source):
                    arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(input_source))

                    if depth_raster:
                        if arcpy.Exists(depth_raster):

                            if use_in_memory:
                                clip_raster = "in_memory/clip_copy"
                            else:
                                clip_raster = os.path.join(scratch_ws, "clip_copy")

                                if arcpy.Exists(clip_raster):
                                    arcpy.Delete_management(clip_raster)

                            # check extents
                            # clip terrain to extent
                            msg_body = create_msg_body("Clipping depth raster to input flooding layer extent", 0, 0)
                            msg(msg_body)

                            arcpy.Clip_management(depth_raster, "#", clip_raster, input_source, "#", "#", "MAINTAIN_EXTENT")

                            all_nodata = arcpy.GetRasterProperties_management(clip_raster, "ALLNODATA")[0]

                            if int(all_nodata) == 1:
                                msg_body = create_msg_body("Input rasters do not overlap.", 0, 0)
                                msg(msg_body, WARNING)
                                depth_raster = None
                            else:
                                depth_raster = clip_raster
                        else:
                            depth_raster = None
                            raise NoDepthRaster

                    if not depth_raster:
                        if depth_value != 0:
                            arcpy.AddMessage("Using default depth value of: " + str(depth_value))

                            # create raster from default depth value

                            if use_in_memory:
                                temp_copy = "in_memory/temp_copy"
                                depth_raster = "in_memory/depth_copy"
                                is_null = "in_memory/isnull_copy"
                            else:
                                temp_copy = os.path.join(scratch_ws, "temp_copy")

                                if arcpy.Exists(temp_copy):
                                    arcpy.Delete_management(temp_copy)

                                depth_raster = os.path.join(scratch_ws, "depth_copy")

                                if arcpy.Exists(depth_raster):
                                    arcpy.Delete_management(depth_raster)

                                is_null = os.path.join(scratch_ws, "isnull_copy")

                                if arcpy.Exists(is_null):
                                    arcpy.Delete_management(is_null)

                            # create raster from default depth value
                            msg_body = create_msg_body("Create depth raster from default depth value.", 0, 0)
                            msg(msg_body)
                            arcpy.CopyRaster_management(input_source, temp_copy)

                            is_Null_raster = arcpy.sa.IsNull(input_source)
                            is_Null_raster.save(is_null)

                            outConRaster = arcpy.sa.Con(is_null, depth_value, depth_value)
                            outConRaster.save(depth_raster)
                        else:
                            bail = 1
                            msg_body = create_msg_body("No depth raster and default depth value is 0. No point continuing.", 0, 0)
                            msg(msg_body, WARNING)

                    if bail == 0:
                        # subtract depth raster from flood elevation raster
                        cell_size_source = arcpy.GetRasterProperties_management(input_source, "CELLSIZEX")
                        cell_size_depth = arcpy.GetRasterProperties_management(depth_raster, "CELLSIZEX")

                        if cell_size_source.getOutput(0) == cell_size_depth.getOutput(0):
                            if arcpy.Exists(output_raster):
                                arcpy.Delete_management(output_raster)

                            msg_body = create_msg_body("Subtracting depth raster from input flooding raster.", 0, 0)
                            msg(msg_body)

                            arcpy.Minus_3d(input_source, depth_raster, output_raster)
                        else:
                            arcpy.AddWarning(
                                "Cell size of " + input_source + " is different than " + depth_raster + ". Exiting...")

                            output_raster = None

                    if use_in_memory:
                        arcpy.Delete_management("in_memory")

                else:   # use default depth value
                    raise NoInputLayer

                end_time = time.clock()
                msg_body = create_msg_body("Set Flood Elevation Value for Raster completed successfully.", start_time, end_time)

                return output_raster
            else:
                raise LicenseErrorSpatial
        else:
            raise LicenseError3D

        arcpy.ClearWorkspaceCache_management()

        msg(msg_body)


    except NoInputLayer:
        print("Can't find Input layer. Exiting...")
        arcpy.AddError("Can't find Input layer. Exiting...")

    except NoDepthRaster:
        print("Can't find Depth raster. Exiting...")
        arcpy.AddError("Can't find depth raster. Exiting...")

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
    create_raster("", "", "", "", 1)