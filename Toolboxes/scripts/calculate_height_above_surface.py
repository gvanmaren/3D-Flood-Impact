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
import time
import importlib

import common_lib
if 'common_lib' in sys.modules:
    importlib.reload(common_lib)

from common_lib import create_msg_body, msg

# Constants
WARNING = "warning"


def calculate_height(lc_input_features, lc_ws, lc_input_surface,
                     lc_output_features, lc_log_dir, lc_debug, lc_memory_switch):

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

            esri_featureID = "copy_featureID"

            # create string field for featureFID
            oidFieldName = arcpy.Describe(lc_input_features).oidFieldName
            common_lib.delete_add_field(lc_input_features, esri_featureID, "TEXT")
            arcpy.CalculateField_management(lc_input_features, esri_featureID, "!" + oidFieldName + "!", "PYTHON_9.3")

            msg_body = create_msg_body("Calculating height above surface for; " +
                                       common_lib.get_name_from_feature_class(lc_input_features), 0, 0)
            msg(msg_body)

            # run zonal stats and get maximum elevation for each polygon
            WSE_max = os.path.join(lc_ws, "SurfaceMaximum")
            if arcpy.Exists(WSE_max):
                arcpy.Delete_management(WSE_max)

            heightsTable = os.path.join(lc_ws, "heightsTable")

            if arcpy.Exists(heightsTable):
                arcpy.Delete_management(heightsTable)

            stat_type = "MAXIMUM"
            max_field = "MAX"
            zmin_field = "Z_MIN"

            arcpy.AddMessage("Calculating Height Statistics Information for " + common_lib.get_name_from_feature_class(
                lc_input_features) + ".")
            arcpy.sa.ZonalStatisticsAsTable(lc_input_features, esri_featureID, lc_input_surface, heightsTable,
                                            "DATA", stat_type)

            common_lib.delete_fields(lc_input_features, [max_field])
            arcpy.JoinField_management(lc_input_features, esri_featureID, heightsTable, esri_featureID, max_field)

            # DISREGARD for now
            # select features with MAXIMUM not NULL
            # select all points with good elevation values
            # expression = """{} IS NOT NULL""".format(arcpy.AddFieldDelimiters(lc_input_features, max_field))
            #
            # msg_body = create_msg_body("Removing polygons with NULL values for MAXIMUM height", 0, 0)
            # msg(msg_body)
            #
            # select_name = arcpy.CreateUniqueName('bridge_height_select_lyr')
            # select_lyr = arcpy.MakeFeatureLayer_management(lc_input_features, select_name).getOutput(0)
            # arcpy.SelectLayerByAttribute_management(select_lyr, "NEW_SELECTION", expression)

            bridge_polys = lc_output_features + "_height"

            if arcpy.Exists(bridge_polys):
                arcpy.Delete_management(bridge_polys)

#            arcpy.CopyFeatures_management(select_lyr, bridge_polys)
            arcpy.CopyFeatures_management(lc_input_features, bridge_polys)

            # add Z information
            arcpy.ddd.AddZInformation(bridge_polys, zmin_field, None)

            # calculate height above surface
            has_field = "HAS_height"
            common_lib.add_field(bridge_polys, has_field, "DOUBLE", 20)
            arcpy.CalculateField_management(bridge_polys, has_field, "!" + zmin_field + "! - !" + max_field + "!",
                                            "PYTHON3", None)

            # create point file for labeling

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



