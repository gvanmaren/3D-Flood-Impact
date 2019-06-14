# -------------------------------------------------------------------------------
# Name:         calculate_height_above_surface
# Purpose:      Calculates height above a surface

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
import importlib

import common_lib
if 'common_lib' in sys.modules:
    importlib.reload(common_lib)

from common_lib import create_msg_body, msg

# Constants
WARNING = "warning"
esri_featureID = "copy_featureID"
zmin_field = "Z_MIN"
min_field = "MIN"
esri_unit = "unit"
has_field = "HAS_height"

def add_minimum_height_above_water_surface(lc_ws, lc_input_features, lc_bridge_raster, lc_input_surface,
                                           lc_memory_switch):

    try:
        if arcpy.Exists(lc_input_features):
            # subtract input surface from bridge raster to obtain heights above surface
            if lc_memory_switch:
                minus_raster = "in_memory/minus_3D"
            else:
                minus_raster = os.path.join(lc_ws, "minus_3D")
                if arcpy.Exists(minus_raster):
                    arcpy.Delete_management(minus_raster)

            # actual subtract
            msg_body = create_msg_body("Finding minimum distance between surfaces for each input feature...", 0, 0)
            msg(msg_body)
            arcpy.Minus_3d(lc_bridge_raster, lc_input_surface, minus_raster)

            # zonal stats to find minimum height above surface
            heights_table = os.path.join(lc_ws, "heightsTable")

            if arcpy.Exists(heights_table):
                arcpy.Delete_management(heights_table)

            stat_type = "MINIMUM"

            arcpy.AddMessage("Calculating Height Statistics Information for " +
                             common_lib.get_name_from_feature_class(lc_input_features) + ".")
            arcpy.sa.ZonalStatisticsAsTable(lc_input_features, esri_featureID, minus_raster, heights_table,
                                            "DATA", stat_type)

            # join back to bridge object
            common_lib.delete_fields(lc_input_features, [min_field])
            arcpy.JoinField_management(lc_input_features, esri_featureID, heights_table, esri_featureID, min_field)

            # add Z information
            arcpy.AddZInformation_3d(lc_input_features, zmin_field, None)

            # calculate height above surface
            common_lib.add_field(lc_input_features, has_field, "DOUBLE", 5)

            expression = "round(float(!" + min_field + "!), 2)"

            arcpy.CalculateField_management(lc_input_features, has_field, expression,
                                            "PYTHON3", None)
        else:
            msg_body = create_msg_body("Couldn't find input feature class: " + str(lc_input_features), 0, 0)
            msg(msg_body, WARNING)

    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddMessage("Unhandled exception: " + str(e.args[0]))


def calculate_height(lc_input_features, lc_ws, lc_tin_dir, lc_input_surface,
                     lc_output_features,
                     lc_log_dir, lc_debug, lc_memory_switch):

    try:
        # create dem
        desc = arcpy.Describe(lc_input_features)
        if desc.spatialReference.linearUnitName in ['Foot_US', 'Foot']:
            unit = 'Feet'
        else:
            unit = 'Meters'

        # Generate raster from lasd
        if arcpy.Exists(lc_input_features):
            if arcpy.Exists(lc_output_features):
                arcpy.Delete_management(lc_output_features)

            # make a copy
            bridge_polys = lc_output_features + "_height"

            if arcpy.Exists(bridge_polys):
                arcpy.Delete_management(bridge_polys)

            arcpy.CopyFeatures_management(lc_input_features, bridge_polys)

            # create string field for featureFID
            oidFieldName = arcpy.Describe(bridge_polys).oidFieldName
            common_lib.delete_add_field(bridge_polys, esri_featureID, "TEXT")
            arcpy.CalculateField_management(bridge_polys, esri_featureID, "!" + oidFieldName + "!", "PYTHON_9.3")

            msg_body = create_msg_body("Calculating height above surface for: " +
                                       common_lib.get_name_from_feature_class(lc_input_features), 0, 0)
            msg(msg_body)

            # create bridge tin
            out_tin = os.path.join(lc_tin_dir, "bridge_tin")
            if arcpy.Exists(out_tin):
                arcpy.Delete_management(out_tin)

            msg_body = create_msg_body("Creating raster for: " +
                                       common_lib.get_name_from_feature_class(lc_input_features), 0, 0)
            msg(msg_body)

            arcpy.CreateTin_3d(out_tin, arcpy.Describe(bridge_polys).spatialReference,
                               "{} Shape.Z Hard_Clip <None>".format(bridge_polys), "DELAUNAY")

            # turn to raster
            if 0:
                bridge_raster = "in_memory/bridge_raster"
            else:
                bridge_raster = os.path.join(lc_ws, "bridge_raster")
                if arcpy.Exists(bridge_raster):
                    arcpy.Delete_management(bridge_raster)

            # use same cell size as input surface
            cell_size = arcpy.GetRasterProperties_management(lc_input_surface, "CELLSIZEX")[0]

            dataType = "FLOAT"
            method = "LINEAR"
            sampling = "CELLSIZE " + str(cell_size)
            zfactor = "1"

            arcpy.TinRaster_3d(out_tin,
                               bridge_raster,
                               dataType,
                               method, sampling, zfactor)

            add_minimum_height_above_water_surface(lc_ws, bridge_polys, bridge_raster,
                                             lc_input_surface, lc_memory_switch)

            # create point file for labeling
            if lc_memory_switch:
                bridge_points = "in_memory/bridge_points"
            else:
                bridge_points = os.path.join(lc_ws, "bridge_points")
                if arcpy.Exists(bridge_points):
                    arcpy.Delete_management(bridge_points)

            arcpy.FeatureToPoint_management(bridge_polys,
                                            bridge_points,
                                           "INSIDE")

            bridge_points3D = lc_output_features + "_points_3D"
            if arcpy.Exists(bridge_points3D):
                arcpy.Delete_management(bridge_points3D)

            # create 3D point
            arcpy.FeatureTo3DByAttribute_3d(bridge_points, bridge_points3D, zmin_field)

            # add unit field
            common_lib.delete_add_field(bridge_points3D, esri_unit, "TEXT")

            expression = """{} IS NOT NULL""".format(arcpy.AddFieldDelimiters(bridge_points3D, has_field))

            # select all points with good elevation values
            local_layer = common_lib.get_name_from_feature_class(bridge_points3D) + "_lyr"
            select_lyr = arcpy.MakeFeatureLayer_management(bridge_points3D, local_layer).getOutput(0)
            arcpy.SelectLayerByAttribute_management(select_lyr, "NEW_SELECTION", expression, None)

            z_unit = common_lib.get_z_unit(bridge_points3D, lc_debug)

            if z_unit == "Meters":
                expression = "'m'"
            else:
                expression = "'ft'"

            arcpy.CalculateField_management(select_lyr, esri_unit, expression, "PYTHON_9.3")
            arcpy.SelectLayerByAttribute_management(select_lyr, "CLEAR_SELECTION")

            common_lib.delete_fields(bridge_polys, [min_field, zmin_field])
            common_lib.delete_fields(bridge_points3D, [min_field, zmin_field])

            return bridge_polys, bridge_points3D
        else:
            msg_body = create_msg_body("Couldn't find input feature class: " + str(lc_input_features), 0, 0)
            msg(msg_body, WARNING)

            return None

    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddMessage("Unhandled exception: " + str(e.args[0]))



