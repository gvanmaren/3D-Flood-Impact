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
esri_unit = "unit"
min_field = "MIN"
zmin_field = "Z_MIN"

def add_minimum_height_above_HAND(lc_ws, lc_input_features, lc_input_surface, lc_had_field, lc_memory_switch):
    try:
        if arcpy.Exists(lc_input_features):
            if arcpy.Exists(lc_input_surface):

                # find minimum HAND value for each input features
                heightsTable = os.path.join(lc_ws, "heightsTable")

                if arcpy.Exists(heightsTable):
                    arcpy.Delete_management(heightsTable)

                stat_type = "MINIMUM"

                arcpy.AddMessage("Calculating minimum HAND height for " + common_lib.get_name_from_feature_class(
                    lc_input_features) + ".")
                arcpy.sa.ZonalStatisticsAsTable(lc_input_features, esri_featureID, lc_input_surface, heightsTable,
                                                "DATA", stat_type)

                common_lib.delete_fields(lc_input_features, [min_field])
                arcpy.JoinField_management(lc_input_features, esri_featureID, heightsTable, esri_featureID, min_field)

                # add minimum HAND height to height_dem which was previously calculated
                hand_field = "HAND"
                common_lib.add_field(lc_input_features, hand_field, "DOUBLE", 5)

                expression = "round(float(!" + lc_had_field + "! + !" + min_field + "!), 2)"

                arcpy.CalculateField_management(lc_input_features, hand_field,
                                                expression,
                                                "PYTHON3", None)

                common_lib.delete_fields(lc_input_features, [lc_had_field, min_field])

                # alternative way ->

                # bridge surface to points

                # bridge polygons to raster

                # add Z values

                # find point with minimum Z value

                # get HAND value point

                # get DEM value for point

                # subtract DEM value from minimum Z -> Height above DEM

                # add this value to HAND for location

            else:
                msg_body = create_msg_body("Couldn't find input surface: " + str(lc_input_surface), 0, 0)
                msg(msg_body, WARNING)
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


def add_minimum_height_above_drainage(lc_ws, lc_input_features, lc_input_surface, lc_had_field, lc_memory_switch):

    try:
        if arcpy.Exists(lc_input_features):
            # find minimum value in input surface
            # run zonal stats and get minimum DEM elevation for each polygon

            heightsTable = os.path.join(lc_ws, "heightsTable")

            if arcpy.Exists(heightsTable):
                arcpy.Delete_management(heightsTable)

            stat_type = "MINIMUM"

            arcpy.sa.ZonalStatisticsAsTable(lc_input_features, esri_featureID, lc_input_surface, heightsTable,
                                            "DATA", stat_type)

            common_lib.delete_fields(lc_input_features, [min_field])
            arcpy.JoinField_management(lc_input_features, esri_featureID, heightsTable, esri_featureID, min_field)

            # add minimum Z information for input feature
            common_lib.delete_fields(lc_input_features, zmin_field)
            arcpy.AddZInformation_3d(lc_input_features, zmin_field, None)

            # calculate height above drainage surface
            common_lib.add_field(lc_input_features, lc_had_field, "DOUBLE", 5)

            expression = "round(float(!" + zmin_field + "! - !" + min_field + "!), 2)"
            arcpy.CalculateField_management(lc_input_features, lc_had_field, expression, "PYTHON3", None)

            common_lib.delete_fields(lc_input_features, [min_field])
        else:
            msg_body = create_msg_body("Couldn't find input feature class: " + str(lc_input_features), 0, 0)
            msg(msg_body, WARNING)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)        # Get the tool error messages

        arcpy.AddError(msgs)
    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddMessage("Unhandled exception: " + str(e.args[0]))


def calculate_height(lc_input_features, lc_ws, lc_tin_dir, lc_input_surface,
                     lc_is_hand, lc_dem, lc_output_features,
                     lc_log_dir, lc_debug, lc_memory_switch):

    try:
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

            had_field = "height_dem"

            # if HAND raster
            if lc_is_hand:
                arcpy.AddMessage("Assuming input surface " + common_lib.get_name_from_feature_class(lc_input_surface) + " is a HAND raster.")
                arcpy.AddMessage("First adding height above DEM to " + common_lib.get_name_from_feature_class(lc_input_features) + ".")
                add_minimum_height_above_drainage(lc_ws, bridge_polys, lc_dem, had_field, lc_memory_switch)

                arcpy.AddMessage("Now adding height above HAND raster " + common_lib.get_name_from_feature_class(lc_input_features) + ".")

                add_minimum_height_above_HAND(lc_ws, bridge_polys, lc_input_surface, had_field, lc_memory_switch)
            else:
                # if just DEM
                arcpy.AddMessage("Assuming input surface " + common_lib.get_name_from_feature_class(lc_input_surface) + " is a digital elevation model.")
                arcpy.AddMessage("Adding height above input surface to " + common_lib.get_name_from_feature_class(lc_input_features) + ".")
                add_minimum_height_above_drainage(lc_ws, bridge_polys, lc_input_surface, had_field, lc_memory_switch)

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
            z_unit = common_lib.get_z_unit(bridge_points3D, lc_debug)

            if z_unit == "Meters":
                expression = "'m'"
            else:
                expression = "'ft'"

            common_lib.delete_add_field(bridge_points3D, esri_unit, "TEXT")
            arcpy.CalculateField_management(bridge_points3D, esri_unit, expression, "PYTHON_9.3")

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



