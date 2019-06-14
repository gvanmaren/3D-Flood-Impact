# -------------------------------------------------------------------------------
# Name:         extract_bridges_from_las
# Purpose:      Creates bridge surface from lidar lasd with bridges classified

# Author:      Gert van Maren
#
# Created:     04/03/19
# Copyright:   (c) Esri 2019
# updated:
# updated:
# updated:

# Required:
#

# -------------------------------------------------------------------------------

import arcpy
import sys
import os
import time
import importlib

import common_lib
if 'common_lib' in sys.modules:
    importlib.reload(common_lib)

from common_lib import create_msg_body, msg

# Constants
WARNING = "warning"

def extrapolate_raster(lc_ws, lc_dsm, lc_cell_size, lc_log_dir, lc_debug, lc_memory_switch):

    try:
        if lc_memory_switch:
            raster_polygons = "memory/raster_polygons"
        else:
            raster_polygons = os.path.join(lc_ws, "raster_polygons")
            if arcpy.Exists(raster_polygons):
                arcpy.Delete_management(raster_polygons)

        out_geom = "POLYGON"  # output geometry type
        arcpy.RasterDomain_3d(lc_dsm, raster_polygons, out_geom)

        # 2. buffer it inwards so that we have a polygon only of the perimeter plus a few cells inward?.
        if lc_memory_switch:
            polygons_inward = "memory/inward_buffer"
        else:
            polygons_inward = os.path.join(lc_ws, "inward_buffer")
            if arcpy.Exists(polygons_inward):
                arcpy.Delete_management(polygons_inward)

        if lc_memory_switch:
            polygons_outward = "memory/outward_buffer"
        else:
            polygons_outward = os.path.join(lc_ws, "outward_buffer")
            if arcpy.Exists(polygons_outward):
                arcpy.Delete_management(polygons_outward)

        x = float(lc_cell_size)

        if x < 0.1:
            arcpy.AddError("Raster cell size is 0. Can't continue. Please check the raster properties.")
            raise ValueError
            return None
        else:
            buffer_in = 6 * x

            xy_unit = common_lib.get_xy_unit(lc_dsm, 0)

            if xy_unit == "Feet":
                buffer_text = "-" + str(buffer_in) + " Feet"
            else:
                buffer_text = "-" + str(buffer_in) + " Meters"

            sideType = "OUTSIDE_ONLY"
            arcpy.Buffer_analysis(raster_polygons, polygons_inward, buffer_text, sideType)

            # create outside buffer for extent only.
            if xy_unit == "Feet":
                buffer_text = str(buffer_in) + " Feet"
            else:
                buffer_text = str(buffer_in) + " Meters"

            arcpy.Buffer_analysis(raster_polygons, polygons_outward, buffer_text, sideType)

            msg_body = create_msg_body("Buffering flood edges...", 0, 0)
            msg(msg_body)

            # 3. mask in ExtractByMask: gives just boundary raster with a few cells inwards
            if lc_memory_switch:
                extract_mask_raster = "in_memory/extract_mask"
            else:
                extract_mask_raster = os.path.join(lc_ws, "extract_mask")
                if arcpy.Exists(extract_mask_raster):
                    arcpy.Delete_management(extract_mask_raster)

            extract_temp_raster = arcpy.sa.ExtractByMask(lc_dsm, polygons_inward)
            extract_temp_raster.save(extract_mask_raster)

            # 4. convert the output to points
            if lc_memory_switch:
                extract_mask_points = "in_memory/extract_points"
            else:
                extract_mask_points = os.path.join(lc_ws, "extract_points")
                if arcpy.Exists(extract_mask_points):
                    arcpy.Delete_management(extract_mask_points)

            arcpy.RasterToPoint_conversion(extract_mask_raster, extract_mask_points, "VALUE")

            msg_body = create_msg_body("Create flood points...", 0, 0)
            msg(msg_body)

            # 5. Interpolate: this will also interpolate outside the bridge extent
            if lc_memory_switch:
                interpolated_raster = "in_memory/interpolate_raster"
            else:
                interpolated_raster = os.path.join(lc_ws, "interpolate_raster")
                if arcpy.Exists(interpolated_raster):
                    arcpy.Delete_management(interpolated_raster)

            zField = "grid_code"
            power = 2

            msg_body = create_msg_body("Interpolating bridge raster points...", 0, 0)
            msg(msg_body)

            arcpy.env.extent = polygons_outward

            # Execute IDW
            out_IDW = arcpy.sa.Idw(extract_mask_points, zField, lc_cell_size, power)

            # Save the output
            out_IDW.save(interpolated_raster)

            arcpy.ResetEnvironments()
            arcpy.env.workspace = lc_ws
            arcpy.env.overwriteOutput = True

            # extract the outer rim only
            extract_mask_raster2 = os.path.join(lc_ws, "extract_mask2")
            if arcpy.Exists(extract_mask_raster2):
                arcpy.Delete_management(extract_mask_raster2)

            extract_temp_raster = arcpy.sa.ExtractByMask(interpolated_raster, polygons_outward)
            extract_temp_raster.save(extract_mask_raster2)

            return extract_mask_raster2

    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddMessage("Unhandled exception: " + str(e.args[0]))


def extract(lc_lasd, lc_ws, lc_class_code, lc_cell_size, lc_min_bridge_area, lc_extrapolate,
            lc_output_features, lc_log_dir, lc_debug, lc_memory_switch):

    try:
        # create dem
        desc = arcpy.Describe(lc_lasd)
        if desc.spatialReference.linearUnitName in ['Foot_US', 'Foot']:
            unit = 'Feet'
        else:
            unit = 'Meters'

        ground_code = 2
        # get class codes
        class_code_string = desc.classCodes

        # get point spacing
        point_spacing = desc.pointSpacing

        # get lidar class code
        msg_body = create_msg_body("Looking for class code: " + str(lc_class_code), 0, 0)
        msg(msg_body)

        class_code_list = class_code_string.split(";")

        # old way
        # class_code_list = common_lib.get_las_class_codes(lc_lasd, lc_log_dir)

        # Generate raster from lasd
        if str(lc_class_code) in class_code_list:

            if arcpy.Exists(lc_output_features):
                arcpy.Delete_management(lc_output_features)

            msg_body = create_msg_body("Creating bridge surfaces using the following class codes: " +
                                       str(lc_class_code), 0, 0)
            msg(msg_body)

            bridge_ld_layer = arcpy.CreateUniqueName('bridge_ld_lyr')

            # Filter for bridge points
            arcpy.MakeLasDatasetLayer_management(lc_lasd, bridge_ld_layer, class_code=str(lc_class_code))

            # create dsm from las with just bridge codes
            if lc_memory_switch:
                dsm = "in_memory/dsm"
            else:
                dsm = os.path.join(lc_ws, "dsm")
                if arcpy.Exists(dsm):
                    arcpy.Delete_management(dsm)

            if arcpy.Exists(dsm):
                arcpy.Delete_management(dsm)

            arcpy.conversion.LasDatasetToRaster(bridge_ld_layer, dsm, 'ELEVATION',
                                                'BINNING MAXIMUM LINEAR',
                                                sampling_type='CELLSIZE',
                                                sampling_value=lc_cell_size)

            arcpy.ResetEnvironments()
            arcpy.env.workspace = lc_ws
            arcpy.env.overwriteOutput = True

            # extrapolate dsm for better interpolation
            if lc_extrapolate:
                dsm_outer = extrapolate_raster(lc_ws, dsm, lc_cell_size, lc_log_dir, lc_debug, lc_memory_switch)

                # merge rasters
                listRasters = []
                listRasters.append(dsm)
                listRasters.append(dsm_outer)
                outer_dsm_name = "dms_plus_outer"

                desc = arcpy.Describe(listRasters[0])
                arcpy.MosaicToNewRaster_management(listRasters, lc_ws, outer_dsm_name, desc.spatialReference,
                                                   "32_BIT_FLOAT", lc_cell_size, 1, "MEAN", "")

                dsm = os.path.join(lc_ws, outer_dsm_name)

            # create raster using LASPointStatisticsAsRaster
            if lc_memory_switch:
                las_point_stats = "in_memory/las_point_stats"
            else:
                las_point_stats = os.path.join(lc_ws, "las_point_stats")
                if arcpy.Exists(las_point_stats):
                    arcpy.Delete_management(las_point_stats)

            if arcpy.Exists(las_point_stats):
                arcpy.Delete_management(las_point_stats)

            msg_body = create_msg_body("Creating points statistics raster using the following class codes: " +
                                       str(lc_class_code), 0, 0)
            msg(msg_body)

            arcpy.management.LasPointStatsAsRaster(bridge_ld_layer,
                                                   las_point_stats,
                                                   "PREDOMINANT_CLASS", "CELLSIZE", 2*lc_cell_size)

            lc_memory_switch = False

            # convert to polygon
            if lc_memory_switch:
                bridge_polys = "in_memory/bridge_polys"
            else:
                bridge_polys = os.path.join(lc_ws, "bridge_polys")
                if arcpy.Exists(bridge_polys):
                    arcpy.Delete_management(bridge_polys)

            msg_body = create_msg_body("Creating polygons from raster", 0, 0)
            msg(msg_body)

            arcpy.conversion.RasterToPolygon(las_point_stats,
                                             bridge_polys,
                                             "SIMPLIFY", "Value", "SINGLE_OUTER_PART", None)

            # eliminate holes
            if lc_memory_switch:
                bridge_polys2 = "memory/bridge_polys2"
            else:
                bridge_polys2 = os.path.join(lc_ws, "bridge_polys2")
                if arcpy.Exists(bridge_polys2):
                    arcpy.Delete_management(bridge_polys2)

            msg_body = create_msg_body("Eliminating holes from polygons", 0, 0)
            msg(msg_body)

            arcpy.management.EliminatePolygonPart(bridge_polys,
                                                  bridge_polys2,
                                                  "AREA", "20 SquareMeters", 0, "ANY")
            # regularize footprints
            if lc_memory_switch:
                bridge_polys3 = "memory/bridge_polys3"
            else:
                bridge_polys3 = os.path.join(lc_ws, "bridge_polys3")
                if arcpy.Exists(bridge_polys3):
                    arcpy.Delete_management(bridge_polys3)

            msg_body = create_msg_body("Regularizing polygons...", 0, 0)
            msg(msg_body)

            arcpy.ddd.RegularizeBuildingFootprint(bridge_polys2,
                                                  bridge_polys3,
                                                  "ANY_ANGLE", 2*lc_cell_size, 2*lc_cell_size, 0.25, 1.5, 0.1, 1000000)

            # interpolate shape on the dsm
            if lc_memory_switch:
                bridge_polys5 = "memory/bridge_polys5"
            else:
                bridge_polys5 = os.path.join(lc_ws, "bridge_polys5")
                if arcpy.Exists(bridge_polys5):
                    arcpy.Delete_management(bridge_polys5)

            msg_body = create_msg_body("Interpolating polygons...", 0, 0)
            msg(msg_body)

            if not lc_extrapolate:
                if lc_memory_switch:
                    bridge_polys4 = "memory/bridge_polys4"
                else:
                    bridge_polys4 = os.path.join(lc_ws, "bridge_polys4")
                    if arcpy.Exists(bridge_polys4):
                        arcpy.Delete_management(bridge_polys4)

                if common_lib.get_xy_unit(bridge_polys3, 0) == "Feet":
                    buffer_text = "-" + str(lc_cell_size*2) + " Feet"
                else:
                    buffer_text = "-" + str(lc_cell_size*2) + " Meters"

                arcpy.analysis.Buffer(bridge_polys3,
                                      bridge_polys4,
                                      buffer_text, "FULL", "ROUND", "NONE", None, "PLANAR")

                # densify buffer so the bridge surface will follow the dsm
                arcpy.edit.Densify(bridge_polys4, "DISTANCE", "10 Meters", "0.1 Meters", 10)

                arcpy.ddd.InterpolateShape(dsm,
                                           bridge_polys4,
                                           bridge_polys5,
                                           None, 1, "BILINEAR", "VERTICES_ONLY", 0, "EXCLUDE")
            else:
                # densify buffer so the bridge surface will follow the dsm
                arcpy.edit.Densify(bridge_polys3, "DISTANCE", "10 Meters", "0.1 Meters", 10)

                arcpy.ddd.InterpolateShape(dsm,
                                           bridge_polys3,
                                           bridge_polys5,
                                           None, 1, "BILINEAR", "VERTICES_ONLY", 0, "EXCLUDE")

            valueAttribute = "Shape_Area"
            expression = """{} > {}""".format(arcpy.AddFieldDelimiters(bridge_polys5, valueAttribute),
                                              lc_min_bridge_area)

            msg_body = create_msg_body("Removing polygons with area smaller than " +
                                       str(lc_min_bridge_area) + ".", 0, 0)
            msg(msg_body)

            # select all points with good elevation values
            select_name = arcpy.CreateUniqueName('bridge_select_lyr')
            select_lyr = arcpy.MakeFeatureLayer_management(bridge_polys5, select_name).getOutput(0)
            arcpy.SelectLayerByAttribute_management(select_lyr, "NEW_SELECTION", expression)

            bridge_polys6 = lc_output_features + "_surfaces"

            if arcpy.Exists(bridge_polys6):
                arcpy.Delete_management(bridge_polys6)

            arcpy.CopyFeatures_management(select_lyr, bridge_polys6)

            return bridge_polys6
        else:
            msg_body = create_msg_body("Couldn't detect class code " + str(lc_class_code) + " in las dataset. Exiting...", 0, 0)
            msg(msg_body, WARNING)

            return None

    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddMessage("Unhandled exception: " + str(e.args[0]))



