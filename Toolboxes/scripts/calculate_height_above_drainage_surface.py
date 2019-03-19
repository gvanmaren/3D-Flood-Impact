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

def add_minimum_height_above_HAND(lc_ws, lc_input_features, lc_bridge_raster, lc_input_surface, lc_dem,
                                  lc_cell_size, lc_memory_switch):
    try:
        if arcpy.Exists(lc_input_features):
            if arcpy.Exists(lc_dem):

                # bridge surface to points
                if lc_memory_switch:
                    bridge_points = "in_memory/bridge_points"
                else:
                    bridge_points = os.path.join(lc_ws, "bridge_points")
                    if arcpy.Exists(bridge_points):
                        arcpy.Delete_management(bridge_points)

                arcpy.RasterToPoint_conversion(lc_bridge_raster,
                                               bridge_points,
                                               "Value")
                # bridge polygons to raster
                if lc_memory_switch:
                    bridge_points_polyIDs = "in_memory/bridge_points_polyids"
                else:
                    bridge_points_polyIDs = os.path.join(lc_ws, "bridge_points_polyids")
                    if arcpy.Exists(bridge_points_polyIDs):
                        arcpy.Delete_management(bridge_points_polyIDs)

                # arcpy.PolygonToRaster_conversion(lc_input_features, esri_featureID,
                #                                  bridge_raster_polyIDs,
                #                                  "CELL_CENTER", "NONE", lc_cell_size)
                #
                # arcpy.sa.ExtractValuesToPoints(bridge_points, br "bridges_output_height_PolygonToRaster",
                #                                r"D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\3DFloodImpact.gdb\Extract_bridge_1",
                #                                "NONE", "ALL")
                #
                #
                #
                #
                # # spatial join to get points with bridge poly ID
                #
                #
                #
                #
                # arcpy.analysis.SpatialJoin(bridge_points, lc_input_features,
                #                            r"D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\3DFloodImpact.gdb\bridge_points_SpatialJoin",
                #                            "JOIN_ONE_TO_ONE", "KEEP_ALL",
                #                            'pointid "pointid" true true false 4 Long 0 0,First,#,bridge_points,pointid,-1,-1;grid_code "grid_code" true true false 4 Float 0 0,First,#,bridge_points,grid_code,-1,-1;Id "Id" true true false 4 Long 0 0,First,#,bridges_output_height,Id,-1,-1;STATUS "STATUS" true true false 4 Long 0 0,First,#,bridges_output_height,STATUS,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,bridges_output_height,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,bridges_output_height,Shape_Area,-1,-1;copy_featureID "copy_featureID" true true false 255 Text 0 0,First,#,bridges_output_height,copy_featureID,0,255',
                #                            "INTERSECT", None, None)

                # add Z values

                # find point with minimum Z value

                # get HAND value point

                # get DEM value for point

                # subtract DEM value from minimum Z -> Height above DEM

                # add this value to HAND for location

                pass

        #        return bridge_polys  # , bridge_points
            else:
                msg_body = create_msg_body("Couldn't find input DEM: " + str(lc_dem), 0, 0)
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


def add_minimum_height_above_drainage(lc_ws, lc_input_features, lc_input_surface, lc_memory_switch):

    try:
        if arcpy.Exists(lc_input_features):
            # find minimum value in input surface
            # run zonal stats and get minimum DEM elevation for each polygon
            dem_min = os.path.join(lc_ws, "SurfaceMinimum")
            if arcpy.Exists(dem_min):
                arcpy.Delete_management(dem_min)

            heightsTable = os.path.join(lc_ws, "heightsTable")

            if arcpy.Exists(heightsTable):
                arcpy.Delete_management(heightsTable)

            stat_type = "MINIMUM"
            min_field = "MIN"
            zmin_field = "Z_MIN"

            arcpy.AddMessage("Calculating drainage height for " + common_lib.get_name_from_feature_class(
                lc_input_features) + ".")
            arcpy.sa.ZonalStatisticsAsTable(lc_input_features, esri_featureID, lc_input_surface, heightsTable,
                                            "DATA", stat_type)

            common_lib.delete_fields(lc_input_features, [min_field])
            arcpy.JoinField_management(lc_input_features, esri_featureID, heightsTable, esri_featureID, min_field)

            # add minimum Z information
            arcpy.AddZInformation_3d(lc_input_features, zmin_field, None)

            arcpy.AddMessage("Calculating minimum height above drainage for " + common_lib.get_name_from_feature_class(
                lc_input_features) + ".")

            # calculate height above drainage surface
            had_field = "HAD_height"
            common_lib.add_field(lc_input_features, had_field, "DOUBLE", 5)

            arcpy.CalculateField_management(lc_input_features, had_field, "!" + zmin_field + "! - !" + min_field + "!",
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
                     lc_is_hand, lc_dem, lc_output_features,
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

            # if HAND raster
            if lc_is_hand:
                arcpy.AddMessage("Assuming input surface " + lc_input_surface + " is a HAND raster.")
                arcpy.AddMessage("First adding height above DEM to " + lc_input_features + ".")
                add_minimum_height_above_drainage(lc_ws, bridge_polys, lc_dem, lc_memory_switch)

                arcpy.AddMessage("Now adding height above HAND raster " + lc_input_features + ".")

#                add_minimum_height_above_HAND(lc_ws, bridge_polys, bridge_raster, lc_input_surface, lc_dem,
#                                              cell_size, lc_memory_switch)
            else:
                # if just DEM
                arcpy.AddMessage("Assuming input surface " + lc_input_surface + " is a digital elevation model.")
                arcpy.AddMessage("Adding height above input surface to " + lc_input_features + ".")
                add_minimum_height_above_drainage(lc_ws, bridge_polys, lc_input_surface, lc_memory_switch)

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



