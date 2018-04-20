import arcpy
import time
import os
import re
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

def set_value(input_source, flood_elevation_attribute, esri_flood_elevation_attribute, default_flood_elevation_value, debug):
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
            input_source = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact\Baltimore.gdb\test_area1_slr6ft_pol'
            flood_elevation_attribute = "my_elev"
            esri_flood_elevation_attribute = "flood_elevation"
            default_flood_elevation_value = 6

            home_directory = r'D:\Gert\Work\Esri\Solutions\3DFloodImpact\work2.1\3DFloodImpact'
            tiff_directory = home_directory + "\\Tiffs"
            tin_directory = home_directory + "\\Tins"
            scripts_directory = home_directory + "\\Scripts"
            rule_directory = home_directory + "\\rule_packages"
            log_directory = home_directory + "\\Logs"
            layer_directory = home_directory + "\\layer_files"
            project_ws = home_directory + "\\Results.gdb"

            enableLogging = False
            DeleteIntermediateData = True
            verbose = 1
            in_memory_switch = False

        return_code = 0
        scratch_ws = common_lib.create_gdb(home_directory, "Intermediate.gdb")
        arcpy.env.workspace = scratch_ws
        arcpy.env.overwriteOutput = True

        default_flood_elevation_value = float(re.sub("[,.]", ".", default_flood_elevation_value))

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

                arcpy.AddMessage("Processing input source: " + common_lib.get_name_from_feature_class(input_source))

                common_lib.delete_add_field(input_source, esri_flood_elevation_attribute, "DOUBLE")

                # check attribute
                if flood_elevation_attribute:
                    if common_lib.check_fields(input_source, [flood_elevation_attribute], False, verbose) == 0:
                        arcpy.CalculateField_management(input_source, esri_flood_elevation_attribute, "!" + flood_elevation_attribute + "!", "PYTHON_9.3")
                        common_lib.set_null_or_negative_to_value_in_fields(input_source, [esri_flood_elevation_attribute],
                                                                           [default_flood_elevation_value],
                                                                           True, verbose)
                        return_code = 1
                    else:  # create a default attribute
                        arcpy.CalculateField_management(input_source, esri_flood_elevation_attribute, default_flood_elevation_value, "PYTHON_9.3")
                        return_code = 1
                else:
                    arcpy.CalculateField_management(input_source, esri_flood_elevation_attribute, default_flood_elevation_value, "PYTHON_9.3")
                    return_code = 1

                return return_code

                end_time = time.clock()
                msg_body = create_msg_body("set Flood Elevation Value For Polygon completed successfully.", start_time, end_time)
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
    set_value("", "", "", "", 1)