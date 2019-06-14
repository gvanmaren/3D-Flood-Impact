# -------------------------------------------------------------------------------
# Name:        attribute_exposure_tbx.py
# Purpose:     wrapper for attribute_exposure.py
#
# Author:      Gert van Maren
#
# Created:     04/04/12/2018
# Copyright:   (c) Esri 2018
# updated:
# updated:
# updated:

# Required:
#

# -------------------------------------------------------------------------------

import os
import arcpy
import sys
import importlib
import attribute_exposure
if 'attribute_exposure' in sys.modules:
    importlib.reload(attribute_exposure)
import common_lib
if 'common_lib' in sys.modules:
    importlib.reload(common_lib)  # force reload of the module
import time
from common_lib import create_msg_body, msg, trace
import re

# debugging switches
debugging = 0
if debugging == 1:
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
TOOLNAME = "Attribute Exposure"
WARNING = "warning"

# error classes
class MoreThan1Selected(Exception):
    pass


class NoLayerFile(Exception):
    pass


class NoPointLayer(Exception):
    pass


class NoFeatureLayer(Exception):
    pass


class NoDepthGBD(Exception):
    pass


class NoOutput(Exception):
    pass


class NoGuideLinesLayer(Exception):
    pass


class NoGuideLinesOutput(Exception):
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


# ----------------------------Main Function---------------------------- #

def main():
    try:
        # Get Attributes from User
        if debugging == 0:
            # script variables
            riskType = arcpy.GetParameterAsText(0)
            isPercentFlood = arcpy.GetParameter(1)
            inWaterSurfaceType = arcpy.GetParameterAsText(2)
            inSurfaceGDB = arcpy.GetParameterAsText(3)
            inDepthGDB = arcpy.GetParameterAsText(4)
            inFeature = arcpy.GetParameterAsText(5)
            featureFID = arcpy.GetParameterAsText(6)
            bufferDistance = arcpy.GetParameterAsText(7)
            tolerance = arcpy.GetParameter(8)
            inDEM = arcpy.GetParameterAsText(9)
            inLossTable = arcpy.GetParameterAsText(10)
            outTable = arcpy.GetParameterAsText(11)

            minField = arcpy.GetParameter(12)
            maxField = arcpy.GetParameter(13)
            rangeField = arcpy.GetParameter(14)
            meanField = arcpy.GetParameter(15)
            stdField = arcpy.GetParameter(16)
            areaField = arcpy.GetParameter(17)
            shapeAreaField = arcpy.GetParameter(18)
            exposureField = arcpy.GetParameter(19)
            volumeField = arcpy.GetParameter(20)

            WaterSurfaceElevationLevel = arcpy.GetParameter(21)
            GroundMinField = arcpy.GetParameter(22)
            GroundMaxField = arcpy.GetParameter(23)
            GroundRangeField = arcpy.GetParameter(24)
            GroundMeanField = arcpy.GetParameter(25)
            GroundSTDField = arcpy.GetParameter(26)
            lossField = arcpy.GetParameter(27)
        else:
            # debug
            riskType = "NOAA Sea Level Rise"  # "NOAA Sea Level Rise", "FEMA Flood Percent", "FEMA Flood Annual", "Tidal Flood", "Storm Surge", "Riverine Flood"
#            inSurfaceGDB = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\SampleFloodData\Results_NOAA_SeaLevelRise_3D.gdb'
            inSurfaceGDB = r''
            inDepthGDB = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\SampleFloodData\NOAA_SeaLevelRise_Depth_Prj.gdb'
            inFeature = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\SampleFloodData\Baltimore.gdb\Buildings_3D'

            featureFID = "OBJECTID"
            #featureFID = "BuildingFID"

            bufferDistance = "0"
            tolerance = 1
            #            inDEM = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\Baltimore.gdb\Sandy_Baltimore_dtm_2m_test_area1_1900'
            inDEM = ""
            inLossTable = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\tables\fema_loss_potential_feet.xls\fema_loss_potential$'
            outTable = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.3\3DFloodImpact\Testing.gdb\flood_exposure_test'

            areaField = True
            minField = True
            maxField = True
            rangeField = False
            meanField = False
            stdField = False
            volumeField = True  # Stable
            shapeAreaField = True
            exposureField = True
            WaterSurfaceElevationLevel = True
            GroundMinField = True
            GroundMaxField = True
            GroundRangeField = False
            GroundMeanField = False
            GroundSTDField = False
            lossField = True

        # fail safe for Europese's comma's
        if bufferDistance:
            bufferDistance = float(re.sub("[,.]", ".", bufferDistance))
        else:
            bufferDistance = 0

        start_time = time.clock()

        esri_featureID = "copy_featureID"

        # check if input exists
        if arcpy.Exists(inDepthGDB):
            if arcpy.Exists(inFeature):
                success, copy_inFeature, stats_table = attribute_exposure.attribute_feature(riskType=riskType,
                                                               inWaterSurfaceType="",
                                                               inSurfaceGDB=inSurfaceGDB,
                                                               inDepthGDB=inDepthGDB,
                                                               inFeature=inFeature,
                                                               featureFID=featureFID,
                                                               esri_featureID=esri_featureID,
                                                               bufferDistance=bufferDistance,
                                                               tolerance=1,
                                                               inDEM=inDEM,
                                                               lossTable=inLossTable,
                                                               outTable=outTable,
                                                               areaField=areaField,
                                                               minField=minField,
                                                               maxField=maxField,
                                                               rangeField=rangeField,
                                                               meanField=meanField,
                                                               stdField=stdField,
                                                               volumeField=volumeField,
                                                               shapeAreaField=shapeAreaField,
                                                               exposureField=exposureField,
                                                               WaterSurfaceElevationLevel=WaterSurfaceElevationLevel,
                                                               GroundMinField=GroundMinField,
                                                               GroundMaxField=GroundMaxField,
                                                               GroundRangeField=GroundRangeField,
                                                               GroundMeanField=GroundMeanField,
                                                               GroundSTDField=GroundSTDField,
                                                               lossField=lossField,
                                                               debug=debugging,
                                                               lc_use_in_memory=in_memory_switch)
                end_time = time.clock()

                if success:
                    if arcpy.Exists(outTable) and arcpy.Exists(copy_inFeature) and arcpy.Exists(stats_table):
                        # join risk table to input feature class
                        arcpy.AddMessage("Joining " + outTable + " to " + common_lib.get_name_from_feature_class(inFeature) + ".")

                        join_layer = common_lib.get_name_from_feature_class(copy_inFeature) + "_temp"
                        arcpy.MakeFeatureLayer_management(copy_inFeature, join_layer)

                        arcpy.AddJoin_management(join_layer, esri_featureID, outTable, esri_featureID)

                        table_gdb = common_lib.get_work_space_from_feature_class(outTable, "yes")

                        join_copy = os.path.join(table_gdb, common_lib.get_name_from_feature_class(inFeature) + "_" + common_lib.get_name_from_feature_class(outTable))
                        if arcpy.Exists(join_copy):
                            arcpy.Delete_management(join_copy)

                        msg_body = create_msg_body("Creating new copy of " + common_lib.get_name_from_feature_class(inFeature) + " in " + table_gdb, 0, 0)
                        msg(msg_body)

                        arcpy.CopyFeatures_management(join_layer, join_copy)

                        # delete OBJECTID, esri_featureID field for table
                        common_lib.delete_fields(join_copy, [common_lib.get_name_from_feature_class(outTable) + "_OBJECTID"])
                        common_lib.delete_fields(join_copy, [common_lib.get_name_from_feature_class(outTable) + "_" +esri_featureID])
                        common_lib.delete_fields(join_copy, [common_lib.get_name_from_feature_class(inFeature) + "_" +esri_featureID])

                        common_lib.delete_fields(inFeature, [esri_featureID])

                        output_layer = common_lib.get_name_from_feature_class(join_copy)
                        arcpy.MakeFeatureLayer_management(join_copy, output_layer)

                        output_layer2 = common_lib.get_name_from_feature_class(stats_table)
                        arcpy.MakeFeatureLayer_management(stats_table, output_layer2)

                        if output_layer and output_layer2:
                            arcpy.SetParameter(28, output_layer)
                            arcpy.SetParameter(29, output_layer2)
                        else:
                            raise NoOutput

                        end_time = time.clock()
                        msg_body = create_msg_body("attribute_exposure_tbx completed successfully.", start_time,
                                                   end_time)
                        msg(msg_body)
                    else:
                        end_time = time.clock()
                        msg_body = create_msg_body("No risk table created. Exiting...", start_time,
                                                   end_time)
                        msg(msg_body, WARNING)
                else:
                    end_time = time.clock()
                    msg_body = create_msg_body("No risk table created. Exiting...", start_time,
                                               end_time)
                    msg(msg_body, WARNING)

                arcpy.ClearWorkspaceCache_management()

                # end main code

                msg(msg_body)

            else:
                raise NoFeatureLayer
        else:
            raise NoDepthGBD

    except LicenseError3D:
        print("3D Analyst license is unavailable")
        arcpy.AddError("3D Analyst license is unavailable")

    except NoPointLayer:
        print("Can't find attachment points layer. Exiting...")
        arcpy.AddError("Can't find attachment points layer. Exiting...")

    except NoFeatureLayer:
        print("Can't find feature layer. Exiting...")
        arcpy.AddError("Can't find feature layer. Exiting...")

    except NoDepthGBD:
        print("Can't find Depth GDB. Exiting...")
        arcpy.AddError("Can't find Depth GDB. Exiting...")

    except NoOutput:
        print("Can't create output joined with risk table. Exiting...")
        arcpy.AddError("Can't create output joined with risk table. Exiting...")

    except NoGuideLinesLayer:
        print("Can't find GuideLines output. Exiting...")
        arcpy.AddError("Can't find GuideLines. Exiting...")

    except NoGuideLinesOutput:
        print("Can't create GuideLines output. Exiting...")
        arcpy.AddError("Can't create GuideLines. Exiting...")

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


if __name__ == '__main__':
    main()
