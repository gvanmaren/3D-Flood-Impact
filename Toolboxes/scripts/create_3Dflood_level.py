import arcpy
import time
import os
import arcpy.cartography as CA

import sys
import math
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
def flood_from_polygon(input_source, input_type, no_flood_value, baseline_flood_value, flood_value, outward_buffer, output_polygons, debug):
    try:
        # Get Attributes from User
        if debug == 0:
            # script variables
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            home_directory = aprx.homeFolder
            tiff_directory = home_directory + "\\Tiffs"
            tin_directory = home_directory + "\\Tins"
            scripts_directory = aprx.homeFolder + "\\Scripts"
            rule_directory = aprx.homeFolder + "\\RulePackages"
            log_directory = aprx.homeFolder + "\\Logs"
            layer_directory = home_directory + "\\LayerFiles"
            project_ws = aprx.defaultGeodatabase

            enableLogging = True
            DeleteIntermediateData = True
            verbose = 0
            in_memory_switch = True
        else:
            # debug
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\WSE_01pct_testarea2'
#            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\MD_LWX_slr_0ft_clip'
            input_type = "raster"
            output_polygons = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\Results.gdb\FloodPolys'
            no_flood_value = "NoData"  # value or "NoData"
            baseline_flood_value = 0.72
            flood_value = 6
            outward_buffer = 0
            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact'
            tiff_directory = home_directory + "\\Tiffs"
            tin_directory = home_directory + "\\Tins"
            scripts_directory = home_directory + "\\Scripts"
            rule_directory = home_directory + "\\RulePackages"
            log_directory = home_directory + "\\Logs"
            layer_directory = home_directory + "\\LayerFiles"
            project_ws = home_directory + "\\Results.gdb"

            enableLogging = False
            DeleteIntermediateData = True
            verbose = 1
            in_memory_switch = False

        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        if not os.path.exists(tiff_directory):
            os.makedirs(tiff_directory)

        if not os.path.exists(tin_directory):
            os.makedirs(tin_directory)

        common_lib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")


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



def flood_from_raster(input_source, input_type, no_flood_value, baseline_elevation, baseline_flood_value, flood_value, outward_buffer, output_polygons, debug):
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
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\WSE_01pct_testarea2'
#            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\MD_LWX_slr_0ft_clip'
            input_type = "raster"
            output_polygons = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\Results.gdb\FloodPolys'
            no_flood_value = "NoData"  # value or "NoData"
            baseline_elevation = r'D:\Gert\Work\Esri\Solutions\3D FloodImpact\work2.1\3DFloodImpact\3DFloodImpact.gdb\base_elevation'
            baseline_flood_value = 0.72
            flood_value = 6
            outward_buffer = 0
            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact'
            tiff_directory = home_directory + "\\Tiffs"
            tin_directory = home_directory + "\\Tins"
            scripts_directory = home_directory + "\\Scripts"
            rule_directory = home_directory + "\\RulePackages"
            log_directory = home_directory + "\\Logs"
            layer_directory = home_directory + "\\LayerFiles"
            project_ws = home_directory + "\\Results.gdb"

            enableLogging = False
            DeleteIntermediateData = True
            verbose = 1
            in_memory_switch = False

        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        if not os.path.exists(tiff_directory):
            os.makedirs(tiff_directory)

        if not os.path.exists(tin_directory):
            os.makedirs(tin_directory)

        common_lib.set_up_logging(log_directory, TOOLNAME)
        start_time = time.clock()

        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")

            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")

                flood_level_layer_mp = None

                arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(input_source))

                spatial_ref = arcpy.Describe(input_source).spatialReference
                if spatial_ref.type == 'PROJECTED' or spatial_ref.type == 'Projected':
                    # check input source type: projected polygons and rasters ONLY!!!!
                    # check type, if polygon -> convert to raster
                    if input_type == "FeatureLayer" or input_type == "FeatureClass":
                        # check if polygon, else bail
                        if arcpy.Describe(input_source).shapetype == "polygon":
                            poly_raster = os.path.join(scratch_ws, "poly_raster")

                            if arcpy.Exists(poly_raster):
                                arcpy.Delete_management(poly_raster)

                                # Execute PolygonToRaster
    #                            arcpy.PolygonToRaster_conversion(input_source, z_field, DTMMean)
    #                            input_raster = poly_raster
                        else:
                            raise NoPolygons
                    elif input_type == "RasterLayer" or input_type == "RasterDataset" or input_type == "raster":
                        input_raster = input_source
                    else:
                        raise NotSupported

                    # use numeric value for determining non flooded areas: set these values to NoData. We need NoData for clippng later on
                    if no_flood_value != "NoData":
                        if common_lib.is_number(no_flood_value):
                            msg_body = create_msg_body(
                                "Setting no flood value: " + no_flood_value + " to NoData in copy of " + common_lib.get_name_from_feature_class(
                                    input_raster) + "...", 0, 0)
                            msg(msg_body)
                            null_for_no_flooded_areas_raster = os.path.join(scratch_ws, "null_for_flooded")
                            if arcpy.Exists(null_for_no_flooded_areas_raster):
                               arcpy.Delete_management(null_for_no_flooded_areas_raster)

                            whereClause = "VALUE = " + no_flood_value

                            # Execute SetNull
                            outSetNull_temp = arcpy.sa.SetNull(input_raster, input_raster, whereClause)
                            outSetNull_temp.save(null_for_no_flooded_areas_raster)

                            input_raster = null_for_no_flooded_areas_raster
                        else:
                            raise ValueError
                    else:
                        pass

                    has_nodata = arcpy.GetRasterProperties_management(input_raster, "ANYNODATA")[0]
                    msg_body = create_msg_body(
                       "Checking for NoData values in raster: " + common_lib.get_name_from_feature_class(
                           input_raster) + ". NoData values are considered to be non-flooded areas!", 0, 0)
                    msg(msg_body)

                    if int(has_nodata) == 1:

                        # TODO!!!
                        # 0 add baseline and flood value to raster

                        # 1. get the outline of the raster as polygon via RasterDomain
                        xy_unit = common_lib.get_xy_unit(input_raster, 0)

                        if xy_unit:
                            cell_size = arcpy.GetRasterProperties_management(input_raster, "CELLSIZEX")

                            msg_body = create_msg_body("Creating 3D polygons...", 0, 0)
                            msg(msg_body)

                            raster_polygons = os.path.join(scratch_ws, "raster_polygons")
                            if arcpy.Exists(raster_polygons):
                                arcpy.Delete_management(raster_polygons)

                            out_geom = "POLYGON"  # output geometry type
                            arcpy.RasterDomain_3d(input_raster, raster_polygons, out_geom)

                            # 2. buffer it inwards so that we have a polygon only of the perimeter plus a few ???????cells inward???????.
                            polygons_inward = os.path.join(scratch_ws, "inward_buffer")
                            if arcpy.Exists(polygons_inward):
                                arcpy.Delete_management(polygons_inward)

                            x = cell_size.getOutput(0)

                            buffer_in = 3 * int(x)

                            if xy_unit == "Feet":
                                buffer_text = "-" + str(buffer_in) + " Feet"
                            else:
                                buffer_text = "-" + str(buffer_in) + " Meters"

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

                            extent_poly = common_lib.get_extent_feature(scratch_ws, polygons_inward)

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

                            outward_buffer += 0.5 * int(x)  # we buffer out by half the raster cellsize

                            if outward_buffer > 0:
                                if xy_unit == "Feet":
                                    buffer_text = str(outward_buffer) + " Feet"
                                else:
                                    buffer_text = str(outward_buffer) + " Meters"

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

                            arcpy.CopyRaster_management(con_raster, con_raster_tif, "#", "#", "#", "#", "#",
                                                       "16_BIT_SIGNED")

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
                            arcpy.FeatureClassToFeatureClass_conversion(con_triangles, scratch_ws, "con_triangles_2D")

                            # 12. clip with smooth polygon
                            smooth_polygons = os.path.join(scratch_ws, "smooth_raster_polygons")
                            if arcpy.Exists(smooth_polygons):
                                arcpy.Delete_management(smooth_polygons)

                            msg_body = create_msg_body("Smoothing edges...", 0, 0)
                            msg(msg_body)

                            CA.SmoothPolygon(os.path.join(raster_polygons), smooth_polygons, "PAEK", x, "",
                                            "FLAG_ERRORS")

                            clip_smooth_triangles = os.path.join(scratch_ws, "clip_smooth_triangles")
                            if arcpy.Exists(clip_smooth_triangles):
                                arcpy.Delete_management(clip_smooth_triangles)

                            msg_body = create_msg_body("Clipping smooth edges...", 0, 0)
                            msg(msg_body)

                            # clip terrain to extent
                            arcpy.Clip_analysis(con_triangles, smooth_polygons, clip_smooth_triangles)

                            # clip to slightly lesser extent because of InterpolateShape fail.
                            area_extent = common_lib.get_extent_feature(scratch_ws, clip_smooth_triangles)

                            extent_inward = os.path.join(scratch_ws, "inward_extent_buffer")
                            if arcpy.Exists(extent_inward):
                                arcpy.Delete_management(extent_inward)

                            buffer_in = 3

                            if xy_unit == "Feet":
                                buffer_text = "-" + str(buffer_in) + " Feet"
                            else:
                                buffer_text = "-" + str(buffer_in) + " Meters"

                            sideType = "FULL"
                            arcpy.Buffer_analysis(area_extent, extent_inward, buffer_text, sideType)

                            clip2_smooth_triangles = os.path.join(scratch_ws, "clip2_smooth_triangles")
                            if arcpy.Exists(clip2_smooth_triangles):
                                arcpy.Delete_management(clip2_smooth_triangles)

                            msg_body = create_msg_body("Clipping smooth edges a second time...", 0, 0)
                            msg(msg_body)

                            # clip terrain to extent
                            arcpy.Clip_analysis(clip_smooth_triangles, extent_inward, clip2_smooth_triangles)

                            # 13. interpolate on TIN
                            clip_smooth_triangles3D = os.path.join(scratch_ws, "clip_smooth_triangles3D")
                            if arcpy.Exists(clip_smooth_triangles3D):
                                arcpy.Delete_management(clip_smooth_triangles3D)

                            msg_body = create_msg_body("Interpolating polygons on TIN", 0, 0)
                            msg(msg_body)
                            arcpy.InterpolateShape_3d(con_tin, clip2_smooth_triangles, clip_smooth_triangles3D, "#", 1,
                                                     "LINEAR", "VERTICES_ONLY")

                            # 13. to multipatch
                            z_unit = common_lib.get_z_unit(clip_smooth_triangles3D, verbose)

                            # temp layer
                            flood_level_layer = "flood_level_layer"
                            arcpy.MakeFeatureLayer_management(clip_smooth_triangles3D, flood_level_layer)

                            # flood_level_mp = os.path.join(project_ws, common_lib.get_name_from_feature_class(input_raster) + "_3D")
                            flood_level_mp = output_polygons + "_3D"

                            if arcpy.Exists(flood_level_mp):
                                arcpy.Delete_management(flood_level_mp)

                            arcpy.Layer3DToFeatureClass_3d(flood_level_layer, flood_level_mp)

                            # layer to be added to TOC
                            flood_level_layer_mp = common_lib.get_name_from_feature_class(flood_level_mp)
                            arcpy.MakeFeatureLayer_management(flood_level_mp, flood_level_layer_mp)

                            # apply transparency here // checking if symbology layer is present
                            if z_unit == "Feet":
                                floodSymbologyLayer = layer_directory + "\\flood3Dfeet.lyrx"
                            else:
                                floodSymbologyLayer = layer_directory + "\\flood3Dmeter.lyrx"

                            if not arcpy.Exists(floodSymbologyLayer):
                                arcpy.AddWarning("Can't find: " + floodSymbologyLayer + ". Symbolize features by error attribute to see data errors.")

                            arcpy.AddMessage("Results written to: " + output_polygons)

                            if DeleteIntermediateData:
                                fcs = common_lib.listFcsInGDB(scratch_ws)

                                msg_prefix = "Deleting intermediate data..."

                                msg_body = common_lib.create_msg_body(msg_prefix, 0, 0)
                                common_lib.msg(msg_body)

                                for fc in fcs:
                                    arcpy.Delete_management(fc)

                            return flood_level_layer_mp

                            # 14. adjust 3D Z feet to meters???
                        else:
                            raise NoUnits
                    else:
                        raise NoNoDataError

                    end_time = time.clock()
                    msg_body = create_msg_body("Create 3D Flood Leveles completed successfully.", start_time, end_time)
                else:
                    raise NotProjected
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
    flood_from_raster("", "", "", "", "", "", "", "", 1)