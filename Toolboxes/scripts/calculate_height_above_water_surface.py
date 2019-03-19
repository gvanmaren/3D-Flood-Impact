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
            min_field = "MIN"
            zmin_field = "Z_MIN"

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
            has_field = "HAS_height"
            common_lib.add_field(lc_input_features, has_field, "DOUBLE", 5)
            arcpy.CalculateField_management(lc_input_features, has_field, "!" + min_field + "!",
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

            arcpy.TinRaster_3d(out_tin,
                               bridge_raster,
                               "FLOAT", "LINEAR", "CELLSIZE", 1, float(cell_size))

            add_minimum_height_above_water_surface(lc_ws, bridge_polys, bridge_raster,
                                             lc_input_surface, lc_memory_switch)

            # create point file for labeling
            # round HAS_height to 2 decimals
            # add unit field

            return bridge_polys #, bridge_points
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



