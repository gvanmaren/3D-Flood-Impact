import arcpy
import time
import os
import re

import sys
import common_lib
from common_lib import create_msg_body, msg, trace
from settings import *

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


class MixOfSR(Exception):
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

                    no_initial_depth_raster = False

                    # create isnull from input source
                    if use_in_memory:
                        is_null = "in_memory/isnull_copy"
                    else:
                        is_null = os.path.join(scratch_ws, "isnull_copy")

                        if arcpy.Exists(is_null):
                            arcpy.Delete_management(is_null)

                    is_Null_raster = arcpy.sa.IsNull(input_source)
                    is_Null_raster.save(is_null)

                    if depth_raster:
                        if arcpy.Exists(depth_raster):
                            # Check if same spatial reference!!!
                            if common_lib.check_same_spatial_reference([input_source], [depth_raster]) == 1:
                                depth_raster = None
                                raise MixOfSR
                            else:
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
                                    no_initial_depth_raster = False

                                    # if depth_value > 0:
                                    #     # grab set all values > 2 to default depth value
                                    #     if use_in_memory:
                                    #         depth_push = "in_memory/depth_push"
                                    #     else:
                                    #         depth_push = os.path.join(scratch_ws, "depth_push")
                                    #
                                    #         if arcpy.Exists(depth_push):
                                    #             arcpy.Delete_management(depth_push)
                                    #
                                    #     msg_body = create_msg_body("Pushing depth > 2 to: " + str(depth_value), 0, 0)
                                    #     msg(msg_body)
                                    #
                                    #     depth_pushRaster = arcpy.sa.Con(clip_raster, depth_value, clip_raster, "VALUE > 2")
                                    #     depth_pushRaster.save(depth_push)
                                    #
                                    #     depth_raster = depth_push
                                    # else:
                                    #     depth_raster = clip_raster
                        else:
                            depth_raster = None
                            raise NoDepthRaster

                    if not depth_raster:
                        if depth_value != 0:
                            no_initial_depth_raster = True

                            arcpy.AddMessage("Using default depth value of: " + str(depth_value))

                            # create raster from default depth value
                            if use_in_memory:
                                depth_raster = "in_memory/depth_copy"
                            else:
                                depth_raster = os.path.join(scratch_ws, "depth_copy")

                                if arcpy.Exists(depth_raster):
                                    arcpy.Delete_management(depth_raster)

                            # create raster from default depth value
                            msg_body = create_msg_body("Create depth raster from default depth value.", 0, 0)
                            msg(msg_body)

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

                            # create raster from depth values
                            if use_in_memory:
                                clip_depth = "in_memory/clip_depth"
                            else:
                                clip_depth = os.path.join(scratch_ws, "clip_depth")

                                if arcpy.Exists(clip_depth):
                                    arcpy.Delete_management(clip_depth)

                            # create raster from default depth value
                            msg_body = create_msg_body("Create clip depth raster...", 0, 0)
                            msg(msg_body)

                            # grab depth elevation values where not null and null where is null (clip using flooding raster)
                            outConRaster = arcpy.sa.Con(is_null, input_source, depth_raster)
                            outConRaster.save(clip_depth)

                            msg_body = create_msg_body("Subtracting depth raster from input flooding raster.", 0, 0)
                            msg(msg_body)

                            if use_in_memory:
                                minus_raster = "in_memory/minus_3D"
                            else:
                                minus_raster = os.path.join(scratch_ws, "minus_3D")
                                if arcpy.Exists(minus_raster):
                                    arcpy.Delete_management(minus_raster)

                            # actual subtract
                            arcpy.Minus_3d(input_source, clip_depth, minus_raster)

                            # now we want just the outside cells (3x cellsize)
                            if use_in_memory:
                                raster_polygons = "in_memory/raster_polygons"
                            else:
                                raster_polygons = os.path.join(scratch_ws, "raster_polygons")
                                if arcpy.Exists(raster_polygons):
                                    arcpy.Delete_management(raster_polygons)

                            out_geom = "POLYGON"  # output geometry type
                            arcpy.RasterDomain_3d(minus_raster, raster_polygons, out_geom)

                            # buffer it outwards first
                            if use_in_memory:
                                polygons_outward = "in_memory/outward_buffer"
                            else:
                                polygons_outward = os.path.join(scratch_ws, "outward_buffer")
                                if arcpy.Exists(polygons_outward):
                                    arcpy.Delete_management(polygons_outward)

                            x = cell_size_source.getOutput(0)

                            buffer_out = int(x)

                            xy_unit = common_lib.get_xy_unit(minus_raster, 0)

                            if xy_unit == "Feet":
                                buffer_text = str(buffer_out) + " Feet"
                            else:
                                buffer_text = str(buffer_out) + " Meters"

                            sideType = "FULL"
                            arcpy.Buffer_analysis(raster_polygons, polygons_outward, buffer_text, sideType)

                            # buffer it inwards so that we have a polygon only of the perimeter plus a 2 cells inward.
                            if use_in_memory:
                                polygons_inward = "in_memory/inward_buffer"
                            else:
                                polygons_inward = os.path.join(scratch_ws, "inward_buffer")
                                if arcpy.Exists(polygons_inward):
                                    arcpy.Delete_management(polygons_inward)

                            x = cell_size_source.getOutput(0)

                            buffer_in = 4 * int(x)

                            xy_unit = common_lib.get_xy_unit(minus_raster, 0)

                            if xy_unit == "Feet":
                                buffer_text = "-" + str(buffer_in) + " Feet"
                            else:
                                buffer_text = "-" + str(buffer_in) + " Meters"

                            sideType = "OUTSIDE_ONLY"
                            arcpy.Buffer_analysis(polygons_outward, polygons_inward, buffer_text, sideType)

                            msg_body = create_msg_body("Buffering depth edges...", 0, 0)
                            msg(msg_body)

                            if use_in_memory:
                                extract_mask_raster = "in_memory/extract_mask"
                            else:
                                extract_mask_raster = os.path.join(scratch_ws, "extract_mask")
                                if arcpy.Exists(extract_mask_raster):
                                    arcpy.Delete_management(extract_mask_raster)

                            extract_temp_raster = arcpy.sa.ExtractByMask(minus_raster, polygons_inward)
                            extract_temp_raster.save(extract_mask_raster)

                            if no_initial_depth_raster == True:
                                if use_in_memory:
                                    plus_mask = "in_memory/plus_mask"
                                else:
                                    plus_mask = os.path.join(scratch_ws, "plus_mask")
                                    if arcpy.Exists(plus_mask):
                                        arcpy.Delete_management(plus_mask)

                                arcpy.Plus_3d(extract_mask_raster, (depth_value - 1), plus_mask)
                                extract_mask_raster = plus_mask

                            if use_in_memory:
                                minus_raster2 = "in_memory/minus_3D2"
                            else:
                                minus_raster2 = os.path.join(scratch_ws, "minus_3D2")
                                if arcpy.Exists(minus_raster2):
                                    arcpy.Delete_management(minus_raster2)

                            # push depth elevation raster down by default depth value
                            if depth_value > 0 and no_initial_depth_raster == False:
                                msg_body = create_msg_body("Pushing inner depth down by: " + str(depth_value) + " to prevent z-fighting.", 0, 0)
                                msg(msg_body)
                                arcpy.Minus_3d(minus_raster, depth_value, minus_raster2)
                            else:
                                minus_raster2 = minus_raster

                            if 0: #use_in_memory:
                                mosaic_raster = "in_memory/mosaic"
                            else:
                                mosaic_raster = os.path.join(scratch_ws, "mosaic")
                                if arcpy.Exists(mosaic_raster):
                                    arcpy.Delete_management(mosaic_raster)

                            listRasters = []
                            listRasters.append(extract_mask_raster)
                            listRasters.append(minus_raster2)

                            desc = arcpy.Describe(listRasters[0])

                            # grab the original outside cells and the pushed down depth elevation raster
                            arcpy.MosaicToNewRaster_management(listRasters, os.path.dirname(mosaic_raster), os.path.basename(mosaic_raster),
                                                               desc.spatialReference,
                                                               "32_BIT_FLOAT", x, 1, "FIRST", "")

                            # now we do an isnull on raster domain poly
                            assignmentType = "CELL_CENTER"
                            priorityField = "#"

                            # Execute PolygonToRaster
                            calc_field = "value_field"
                            common_lib.delete_add_field(raster_polygons, calc_field, "DOUBLE")
                            arcpy.CalculateField_management(raster_polygons, calc_field, 1, "PYTHON_9.3")

                            if use_in_memory:
                                poly_raster = "in_memory/poly_raster"
                            else:
                                poly_raster = os.path.join(scratch_ws, "poly_raster")
                                if arcpy.Exists(poly_raster):
                                    arcpy.Delete_management(poly_raster)

                            arcpy.PolygonToRaster_conversion(raster_polygons, calc_field, poly_raster, assignmentType, priorityField, x)

                            # create isnull
                            if use_in_memory:
                                is_null2 = "in_memory/isnull_copy2"
                            else:
                                is_null2 = os.path.join(scratch_ws, "isnull_copy2")

                                if arcpy.Exists(is_null2):
                                    arcpy.Delete_management(is_null2)

                            is_Null_raster2 = arcpy.sa.IsNull(poly_raster)
                            is_Null_raster2.save(is_null2)

                            # con on mosaic
                            finalRaster = arcpy.sa.Con(is_null2, poly_raster, mosaic_raster)
                            finalRaster.save(output_raster)
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
                msg(msg_body)

                arcpy.ClearWorkspaceCache_management()

                return output_raster
            else:
                raise LicenseErrorSpatial
        else:
            raise LicenseError3D

        arcpy.ClearWorkspaceCache_management()


    except MixOfSR:
        # The input has mixed SR
        #
        print(('Input data has mixed spatial references. Ensure all input is in the same spatial reference, including the same vertical units.'))
        arcpy.AddError('Input data has mixed spatial references. Ensure all input is in the same spatial reference, including the same vertical units.')

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