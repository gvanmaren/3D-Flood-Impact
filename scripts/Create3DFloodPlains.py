# -------------------------------------------------------------------------------
# Name:        Create3DFloodPlains
# Purpose:     Convert flood raster into 3D polygons representing the raster values
#
# Author:      Gert van Maren
#
# Created:     27/01/12/2018
# Copyright:   (c) Esri 2018
# updated:
# updated:
# updated:

# Required:     CommonLib.py
# Limitations:  Input flood level raster: must have values for flooded areas and NODATA or single value for none flooded areas

# -------------------------------------------------------------------------------

import arcpy
import arcpy.cartography as CA
import CommonLib
import time
import os
from CommonLib import create_msg_body, msg, trace


# debugging switches
debugging = 1
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
TOOLNAME = "Create3DFloodPlains"

# error classes

class NoNoDataError(Exception):
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

        msg_prefix = "Function create_volumes completed successfully."
        failed = False
        return 0

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "template_function",
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
            input_var1 = arcpy.GetParameter(0)
            output_var1 = arcpy.GetParameterAsText(1)

            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            scripts_directory = aprx.homeFolder + "\\Scripts"
            rule_directory = aprx.homeFolder + "\\RulePackages"
            log_directory = aprx.homeFolder + "\\Logs"
            project_ws = aprx.defaultGeodatabase

        else:
            # debug
            input_raster = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\WSE_01pct_testarea2'
            output_polygons = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact\Testing130218.gdb\FloodPolys'
            non_flood_value = "NoData"   # value or "NoData"
            default_buffer = 6
            home_directory = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact'
            tiff_directory = home_directory + "\\Tiffs"
            tin_directory = home_directory + "\\Tins"
            scripts_directory = home_directory + "\\Scripts"
            rule_directory = home_directory + "\\RulePackages"
            log_directory = home_directory + "\\Logs"
            project_ws = home_directory + "\\Testing130218.gdb"

        scratch_ws = CommonLib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        if not os.path.exists(tiff_directory):
            os.makedirs(tiff_directory)

        if not os.path.exists(tin_directory):
            os.makedirs(tin_directory)

        CommonLib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")

                # use numeric value for determining non flooded areas: set these values to NoData. We need NoData for clippng later on
                if non_flood_value != "NoData":
                    msg_body = create_msg_body("Setting non flood value: " + non_flood_value + " to NoData in copy of " + input_raster + "...", 0, 0)
                    msg(msg_body)
                    null_for_non_flooded_areas_raster = os.path.join(scratch_ws, "null_for_flooded")
                    if arcpy.Exists(null_for_non_flooded_areas_raster):
                        arcpy.Delete_management(null_for_non_flooded_areas_raster)

                    whereClause = "VALUE = " + non_flood_value

                    # Execute SetNull
                    outSetNull_temp = arcpy.sa.SetNull(input_raster, input_raster, whereClause)
                    outSetNull_temp.save(null_for_non_flooded_areas_raster)

                    input_raster = null_for_non_flooded_areas_raster
                else:
                     pass # we use NoData values for determining flooded areas

                has_nodata = arcpy.GetRasterProperties_management(input_raster, "ANYNODATA")[0]

                if int(has_nodata) == 1:
                    # 1. get the outline of the raster as polygon via RasterDomain
                    xy_unit = CommonLib.get_xy_unit(input_raster, 0)
                    cell_size = arcpy.GetRasterProperties_management(input_raster, "CELLSIZEX")

                    msg_body = create_msg_body("Creating 3D polygons...", 0, 0)
                    msg(msg_body)

                    raster_polygons = os.path.join(scratch_ws, "raster_polygons")
                    if arcpy.Exists(raster_polygons):
                        arcpy.Delete_management(raster_polygons)

                    out_geom = "POLYGON"  # output geometry type
                    arcpy.RasterDomain_3d(input_raster, raster_polygons, out_geom)

                    # 2. buffer it inwards so that we have a polygon only of the perimeter plus a few “cells inward”.
                    polygons_inward = os.path.join(scratch_ws, "inward_buffer")
                    if arcpy.Exists(polygons_inward):
                        arcpy.Delete_management(polygons_inward)

                    if xy_unit == "Feet":
                        buffer_text = "-" + str(default_buffer) + " Feet"
                    else:
                        buffer_text = "-" + str(default_buffer) + " Meters"

                    sideType = "OUTSIDE_ONLY"
                    arcpy.Buffer_analysis(raster_polygons, polygons_inward, buffer_text, sideType)

                    msg_body = create_msg_body("Buffering flood edges...", 0, 0)
                    msg(msg_body)

                    # 3. mask in ExtractByMask: gives just boundary raster with a few cells inwards
                    extract_mask_raster = os.path.join(scratch_ws, "extract_mask")
                    if arcpy.Exists(extract_mask_raster):
                        arcpy.Delete_management(extract_mask_raster)

                    extract_temp_raster = arcpy.sa.ExtractByMask(input_raster, polygons_inward)
                    extract_temp_raster.save(extract_mask_raster)

                    # 4. convert the output to points
                    extract_mask_points = os.path.join(scratch_ws, "extract_points")
                    if arcpy.Exists(extract_mask_points):
                        arcpy.Delete_management(extract_mask_points)

                    arcpy.RasterToPoint_conversion(extract_mask_raster, extract_mask_points, "VALUE")

                    msg_body = create_msg_body("Create flood points...", 0, 0)
                    msg(msg_body)

                    # 5. Interpolate: this will also interpolate outside the flood boundary which is
                    # what we need so we get a nice 3D poly that extends into the surrounding DEM
                    interpolated_raster = os.path.join(scratch_ws, "interpolate_raster")
                    if arcpy.Exists(interpolated_raster):
                        arcpy.Delete_management(interpolated_raster)

                    zField = "grid_code"
                    power = 2
                    searchRadius = arcpy.sa.RadiusVariable(12, 150000)

                    msg_body = create_msg_body("Interpolating flood points...", 0, 0)
                    msg(msg_body)

                    # Execute IDW
                    out_IDW = arcpy.sa.Idw(extract_mask_points, zField, cell_size, power)

                    # Save the output
                    out_IDW.save(interpolated_raster)

                    extent_poly = CommonLib.get_extent_feature(scratch_ws, polygons_inward)

                    msg_body = create_msg_body("Clipping terrain...", 0, 0)
                    msg(msg_body)

                    # clip the input surface
                    extent_clip_idwraster = os.path.join(scratch_ws, "extent_clip_idw")
                    if arcpy.Exists(extent_clip_idwraster):
                        arcpy.Delete_management(extent_clip_idwraster)

                    # clip terrain to extent
                    arcpy.Clip_management(interpolated_raster, "#", extent_clip_idwraster, extent_poly)

                    # 6. clip the interpolated raster by (outward buffered) outline polygon
                    polygons_outward = os.path.join(scratch_ws, "outward_buffer")
                    if arcpy.Exists(polygons_outward):
                        arcpy.Delete_management(polygons_outward)

                    if default_buffer > 0:
                        if xy_unit == "Feet":
                            buffer_text = str(default_buffer) + " Feet"
                        else:
                            buffer_text = str(default_buffer) + " Meters"

                        sideType = "FULL"
                        arcpy.Buffer_analysis(raster_polygons, polygons_outward, buffer_text, sideType)

                        raster_polygons = polygons_outward

                    # clip the input surface
                    flood_clip_raster = os.path.join(scratch_ws, "flood_clip_raster")
                    if arcpy.Exists(flood_clip_raster):
                        arcpy.Delete_management(flood_clip_raster)

                    msg_body = create_msg_body("Clipping flood raster...", 0, 0)
                    msg(msg_body)

                    # clip terrain to extent
                    arcpy.Clip_management(interpolated_raster, "#", flood_clip_raster, raster_polygons)

                    # 7. Isnull, and Con to grab values from flood_clip_raster for
                    # create NUll mask
                    is_Null = os.path.join(scratch_ws, "is_Null")
                    if arcpy.Exists(is_Null):
                        arcpy.Delete_management(is_Null)

                    is_Null_raster = arcpy.sa.IsNull(input_raster)
                    is_Null_raster.save(is_Null)

                    # Con
                    con_raster = os.path.join(scratch_ws, "con_raster")
                    if arcpy.Exists(con_raster):
                        arcpy.Delete_management(con_raster)
                    temp_con_raster = arcpy.sa.Con(is_Null, interpolated_raster, input_raster)
                    temp_con_raster.save(con_raster)

                    msg_body = create_msg_body("Merging rasters...", 0, 0)
                    msg(msg_body)

                    # 8. focal stats on raster to smooth?

                    # 9. copy raster to geotiff
                    con_raster_tif = os.path.join(tiff_directory, "con_raster.tif")
                    if arcpy.Exists(con_raster_tif):
                        arcpy.Delete_management(con_raster_tif)

                    arcpy.CopyRaster_management(con_raster, con_raster_tif, "#", "#", "#", "#", "#", "16_BIT_SIGNED")

                    msg_body = create_msg_body("Copying to tiff...", 0, 0)
                    msg(msg_body)

                    # 10. raster to TIN
                    zTol = 0.1
                    maxPts = 1500000
                    zFactor = 1
                    con_tin = os.path.join(tin_directory, "con_tin")
                    if arcpy.Exists(con_tin):
                        arcpy.Delete_management(con_tin)

                    # Execute RasterTin
                    arcpy.RasterTin_3d(con_raster_tif, con_tin, zTol, maxPts, zFactor)

                    msg_body = create_msg_body("Creating TIN...", 0, 0)
                    msg(msg_body)

                    # 11. TIN triangles
                    con_triangles = os.path.join(scratch_ws, "con_triangles")
                    if arcpy.Exists(con_triangles):
                        arcpy.Delete_management(con_triangles)

                    arcpy.TinTriangle_3d(con_tin, con_triangles)

                    msg_body = create_msg_body("Creating polygons...", 0, 0)
                    msg(msg_body)

                    # 12. make 2D polygons feature to feature class
                    arcpy.FeatureClassToFeatureClass_conversion(con_triangles, project_ws, "con_triangles_2D")

                    # 12. clip with smooth polygon
                    smooth_polygons = os.path.join(scratch_ws, "smooth_raster_polygons")
                    if arcpy.Exists(smooth_polygons):
                        arcpy.Delete_management(smooth_polygons)

                    msg_body = create_msg_body("Smoothing edges...", 0, 0)
                    msg(msg_body)

                    CA.SmoothPolygon(os.path.join(raster_polygons), smooth_polygons, "PAEK", 8, "", "FLAG_ERRORS")

                    clip_smooth_triangles = os.path.join(scratch_ws, "clip_smooth_triangles")
                    if arcpy.Exists(clip_smooth_triangles):
                        arcpy.Delete_management(clip_smooth_triangles)

                    msg_body = create_msg_body("Clipping smooth edges...", 0, 0)
                    msg(msg_body)

                    # clip terrain to extent
                    arcpy.Clip_analysis(con_triangles, smooth_polygons, clip_smooth_triangles)

                    # 13. interpolate on TIN
                    # 13. to multipatch
                    # 14. adjust 3D Z ???
                    # 15. Layer 3D to multipatchhere goes all the other if/else
                else:
                    raise NoNoDataError


                end_time = time.clock()
                msg_body = create_msg_body("script_template completed successfully.", start_time, end_time)

            else:
                raise LicenseErrorSpatial
        else:
            raise LicenseError3D

        arcpy.ClearWorkspaceCache_management()

        # end main code

        msg(msg_body)

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

    except LicenseErrorSpatial:
        print("Spatial Analyst license is unavailable")
        arcpy.AddError("Spatial Analyst license is unavailable")

    except NoNoDataError:
        print("Input raster does not have NODATA values")
        arcpy.AddError("Input raster does not have NODATA values")

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
