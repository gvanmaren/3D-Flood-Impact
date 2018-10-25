# -------------------------------------------------------------------------------
# Name:        CommonLib
# Purpose:     Contains common functions
#
# Author:      Gert van Maren
#
# Created:     14/12/2016
# Copyright:   (c) Esri 2016
# updated:
# updated:
# updated:

# -------------------------------------------------------------------------------

import arcpy
import os
import time
import traceback
import datetime
import logging
import sys
import math
from math import *

from bisect import bisect_left

# Constants
NON_GP = "non-gp"
ERROR = "error"
WARNING = "warning"

# ----------------------------Template Functions----------------------------#

in_memory_switch = True

def template_function(debug):

    if debug == 0:
        msg("--------------------------")
        msg("Executing template_function...")

    start_time = time.clock()

    try:

        pass

        msg_prefix = "Function template_function completed successfully."
        failed = False

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
            if debug == 1:
                msg(msg_body)


class FunctionError(Exception):

    """
    Raised when a function fails to run.
    """

    pass


def trace(*arg):

    """
    Trace finds the line, the filename
    and error message and returns it
    to the user
    """

    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # script name + line number
    line = tbinfo.split(", ")[1]

    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]

    if len(arg) == 0:
        return line, __file__, synerror
    else:
        return line, arg[1], synerror


def set_up_logging(output_folder, file):

    arcpy.AddMessage("Executing set_up_logging...")
    start_time = time.clock()

    try:
        # Make the 'logs' folder if it doesn't exist
        log_location = output_folder
        if not os.path.exists(log_location):
            os.makedirs(log_location)

        # Set up logging
        logging.getLogger('').handlers = []  # clears handlers
        date_prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M')

        log_file_date = os.path.join(log_location, file + "_" + date_prefix + ".log")
        log_file = os.path.join(log_location, file + ".log")
        log_file_name = log_file
        date_prefix = date_prefix + "\t"  # Inside messages, an extra tab to separate date and any following text is desirable

        if os.path.exists(log_file):
            try:
                os.access(log_file, os.R_OK)
                log_file_name = log_file
            except FunctionError:
                log_file_name = log_file_date

        logging.basicConfig(level=logging.INFO,
                            filename=log_file_name,
                            format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        msg("Logging set up.  Log location: " + log_location)

        failed = False

    except:
        failed = True
        raise

    finally:
        if failed:
            msg_prefix = "An exception was raised in set_up_logging."
            end_time = time.clock()
            msg_body = create_msg_body(msg_prefix, start_time, end_time)
            msg(msg_body, ERROR)


def msg(*arg):

    # Utility method that writes a logging info statement, a print statement and an
    # arcpy.AddMessage() statement all at once.
    if len(arg) == 1:
        logging.info(str(arg[0]) + "\n")
        arcpy.AddMessage(str(arg[0]))
    elif arg[1] == ERROR:
        logging.error(str(arg[0]) + "\n")
        arcpy.AddError(str(arg[0]))
    elif arg[1] == WARNING:
        logging.warning(str(arg[0]) + "\n")
        arcpy.AddWarning(str(arg[0]))
    elif arg[1] == NON_GP:
        logging.info(str(arg[0]) + "\n")
        arcpy.AddMessage(str(arg[0]))
#    print(str(arg[0]))

    return


def create_msg_body(msg_prefix, start_time, end_time):

    # Creates the message returned after each run of a function (successful or unsuccessful)
    diff = end_time - start_time

    if diff > 0:
        if msg_prefix == "":
            msg_prefix = "Elapsed time: "
        else:
            msg_prefix = msg_prefix + "  Elapsed time: "

        elapsed_time_mins = int(math.floor(diff/60))
        minutes_txt = " minutes "
        if elapsed_time_mins == 1:
            minutes_txt = " minute "
        if elapsed_time_mins > 0:
            elapsed_time_secs = int(round(diff - (60 * elapsed_time_mins)))
            seconds_txt = " seconds."
            if elapsed_time_secs == 1:
                seconds_txt = " second."
            elapsed_time_formatted = str(elapsed_time_mins) + minutes_txt + str(elapsed_time_secs) + seconds_txt
        else:
            elapsed_time_secs = round(diff - (60 * elapsed_time_mins), 2)
            seconds_txt = " seconds."
            if elapsed_time_secs == 1:
                seconds_txt = " second."
            elapsed_time_formatted = str(elapsed_time_secs) + seconds_txt

        msg_body = msg_prefix + elapsed_time_formatted

    else:
        msg_body = msg_prefix

    return msg_body


def log_message(inFile, message):
    directory = os.path.dirname(inFile)
    if not os.path.exists(directory):
        os.makedirs(directory)

    text_file = open(inFile, "a")
    text_file.write(message + "\n")
    text_file.close()


def create_gdb(path, name):
    try:
        int_gdb = os.path.join(path, name)

        if not arcpy.Exists(int_gdb):
            arcpy.CreateFileGDB_management(path, name, "CURRENT")
            return int_gdb
        else:
            return int_gdb

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def get_name_from_feature_class(feature_class):
    desc_fc = arcpy.Describe(feature_class)
    return desc_fc.name


def get_datatype_from_layer(layer):
    desc = arcpy.Describe(layer)
    return desc.dataType

def get_raster_featuretype_from_layer(layer):
    desc = arcpy.Describe(layer)
    shape_type = None

    if desc.dataType == "FeatureClass":
        msg_prefix = "The data type is: " + desc.shapetype
        shape_type = desc.shapetype
        msg_body = create_msg_body(msg_prefix, 0, 0)
        msg(msg_body)
    elif desc.dataType == "RasterDataset":
        cell_size = arcpy.GetRasterProperties_management(layer, "CELLSIZEX")
        msg_prefix = "The data type is: Raster. Cellsize is: " + str(cell_size.getOutput(0))
        msg_body = create_msg_body(msg_prefix, 0, 0)
        msg(msg_body)
    else:
        msg_prefix = "Data type not supported. RasterDataset or FeatureClass only."
        msg_body = create_msg_body(msg_prefix, 0, 0)
        msg(msg_body)

    return desc.dataType, shape_type

def is_layer(layer):
    desc_fc = arcpy.Describe(layer)
    if hasattr(desc_fc, "nameString"):
        return 1
    else:
        return 0


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        pass


def get_full_path_from_layer(in_layer):
    dir_name = os.path.dirname(arcpy.Describe(in_layer).catalogPath)
    layer_name = arcpy.Describe(in_layer).name

    return os.path.join(dir_name, layer_name)


# Get Workspace from Building feature class location
def get_work_space_from_feature_class(feature_class, get_gdb):
    dir_name = os.path.dirname(arcpy.Describe(feature_class).catalogPath)
    desc = arcpy.Describe(dir_name)

    if hasattr(desc, "datasetType") and desc.datasetType == 'FeatureDataset':
        dirname = os.path.dirname(dir_name)

    if get_gdb == "yes":
        return dir_name
    else:  # directory where gdb lives
        return os.path.dirname(dir_name)


# Field Exists
def field_exist(feature_class, field_name):
    field_list = arcpy.ListFields(feature_class, field_name)
    field_count = len(field_list)
    if field_count == 1:
        return True
    else:
        return False


# Define DeleteAdd Fields
def delete_add_field(feature_class, field, field_type):
    try:
        if field_exist(feature_class, field):
            arcpy.DeleteField_management(feature_class, field)

        arcpy.AddField_management(feature_class, field, field_type, None, None, None,
                                      None, "true", "false", None)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def get_feature_count(feature_class, query):
    fields = arcpy.ListFields(feature_class)
    count = 0

    with arcpy.da.SearchCursor(feature_class, str(fields[0].name), query) as cursor:
        for row in cursor:
            count += 1

    return count

def unique_values(table, field):
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor})

def get_fids_for_selection(lyr):
    try:
        desc = arcpy.Describe(lyr)
        fid_list = desc.FIDSet.split(";")

        return fid_list, len(fid_list)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def set_null_or_negative_to_value_in_fields(cn_table, cn_field_list, cn_value_list, error, debug):
    try:
        if debug == 1:
            msg("--------------------------")
            msg("Executing set_null_or_negative_to_value_in_fields...")

        start_time = time.clock()
        failed = True
        null_value = False
        field_name = ""

        if arcpy.Exists(cn_table):
            with arcpy.da.UpdateCursor(cn_table, cn_field_list) as cursor:
                for row in cursor:
                    i = 0
                    for field in cn_field_list:
                        if row[i] is None or row[i] <= 0:
                            row[i] = cn_value_list[i]

                        i += 1

                    cursor.updateRow(row)

        msg_prefix = "Function set_null_or_negative_to_value_in_fields completed successfully."
        failed = False
        return null_value

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "set_null_or_negative_to_value_in_fields",
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
            if debug == 1:
                msg(msg_body)
            else:
                pass


def set_null_to_value_in_fields(cn_table, cn_field_list, cn_value_list, error, debug):
    try:
        if debug == 1:
            msg("--------------------------")
            msg("Executing set_null_to_value_in_fields...")

        start_time = time.clock()
        failed = True
        null_value = False
        field_name = ""

        if arcpy.Exists(cn_table):
            with arcpy.da.UpdateCursor(cn_table, cn_field_list) as cursor:
                for row in cursor:
                    i = 0
                    for field in cn_field_list:
                        if row[i] is None:
                            row[i] = cn_value_list[i]
                            null_value = True

                        i += 1

                    cursor.updateRow(row)

        if null_value is True:
            if error:
                list_as_string = " ".join(str(elm) for elm in cn_field_list)
                msg_prefix = "Found at least 1 NULL value in attribute fields " + list_as_string + " in " + get_name_from_feature_class(cn_table)
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body, WARNING)
                list_as_string = " ".join(str(elm) for elm in cn_value_list)
                msg_prefix = "Null values are set to " + list_as_string
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body, WARNING)

        msg_prefix = "Function set_null_to_value_in_fields completed successfully."
        failed = False
        return null_value

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "set_null_to_value_in_fields",
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
            if debug == 1:
                msg(msg_body)
            else:
                pass


def calculate_field_from_other_field(lyr, table, input_field, output_field, operator, value, debug):
    if debug == 1:
        msg("--------------------------")
        msg("Executing calculate_field_from_other_field...")

    start_time = time.clock()

    return_error = True

    try:
        if lyr:
            searchInput = lyr
        else:
            searchInput = get_full_path_from_layer(table)

        if arcpy.Exists(searchInput):
            real_fields = arcpy.ListFields(searchInput)

            if check_fields(searchInput, [input_field, output_field], return_error, 0) == 0:
                with arcpy.da.UpdateCursor(searchInput, [input_field, output_field]) as u_cursor:
                    for u_row in u_cursor:
                        if u_row[0]:
                            if operator == "multiply":
                                u_row[1] = u_row[0] * value
                            if operator == "divide":
                                u_row[1] = u_row[0] / value
                            if operator == "plus":
                                u_row[1] = u_row[0] + value
                            if operator == "minus":
                                u_row[1] = u_row[0] - value
                        else:
                            u_row[1] = u_row[0]

                        u_cursor.updateRow(u_row)

        msg_prefix = "Function calculate_field_from_other_field completed successfully."
        failed = False

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "calculate_field_from_other_field",
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
            if debug == 1:
                msg(msg_body)


def check_null_in_fields(cn_table, cn_field_list, error, debug):
    try:
        if debug == 1:
            msg("--------------------------")
            msg("Executing check_null_in_fields...")

        start_time = time.clock()
        failed = True
        null_value = False
        field_name = ""

        if arcpy.Exists(cn_table):
            with arcpy.da.SearchCursor(cn_table, cn_field_list) as cursor:
                for row in cursor:
                    i = 0
                    for field in cn_field_list:
                        if row[i] is None:
                            null_value = True
                            field_name = field
                            break

                        i += 1

                    if null_value is True:
                        if error:
                            msg_prefix = "Found at least 1 NULL value in attribute " + field_name + " in " + get_name_from_feature_class(cn_table)
                            msg_body = create_msg_body(msg_prefix, 0, 0)
                            msg(msg_body, WARNING)

                        break

        msg_prefix = "Function check_null_in_fields completed successfully."
        failed = False
        return null_value

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "check_null_in_fields",
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
            if debug == 1:
                msg(msg_body)
            else:
                pass


def check_same_spatial_reference(input_list, featureclass_list):
    try:
        we_fail = 0

        base_sr = arcpy.Describe(input_list[0]).spatialReference
        base_linear_unit = base_sr.linearUnitName
        base_Zunit = get_z_unit(input_list[0], 0)

        one_list = input_list + featureclass_list
        for f in one_list:
            if arcpy.Exists(f):
                sr = arcpy.Describe(f).spatialReference

                if sr.name != base_sr.name:
                    arcpy.AddMessage(get_name_from_feature_class(f) + " has different spatial reference " + sr.name + " than " + get_name_from_feature_class(input_list[0]))
                    we_fail = 1
                    break
                else:
                    if sr.linearUnitName != base_linear_unit:
                        arcpy.AddMessage(get_name_from_feature_class(
                            f) + " has different linear units " + sr.linearUnitName + " than " + get_name_from_feature_class(input_list[0]))
                        we_fail = 1
                        break
                    else:
                        if get_z_unit(f, 0) != base_Zunit:
                            we_fail = 1
                            arcpy.AddMessage(get_name_from_feature_class(f) + " has different spatial reference or units than " + get_name_from_feature_class(input_list[0]))
                            break
        return we_fail

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

def check_fields(cf_table, cf_field_list, error, debug):
    try:
        if debug == 1:
            msg("--------------------------")
            msg("Executing check_fields...")

        start_time = time.clock()

        real_fields_list = []
        real_fields = arcpy.ListFields(cf_table)
        i = 0

        for f in real_fields:
            real_fields_list.append(f.name)

        for s in cf_field_list:
            if s not in real_fields_list:
                i = 1
                if error:
                    msg_prefix = "Can't find " + s + " in " + cf_table
                    msg_body = create_msg_body(msg_prefix, 0, 0)
                    msg(msg_body, ERROR)

        msg_prefix = "Function check_fields completed successfully."
        failed = False

        return i

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "check_fields",
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
            if debug == 1:
                msg(msg_body)
            else:
                pass


def add_field(feature_class, field, field_type, length):
    try:
        if not field_exist(feature_class, field):
            arcpy.AddField_management(feature_class, field, field_type, field_length=length)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

# Define DeleteAdd Fields
def delete_fields(feature_class, field_list):
    try:
        for f in field_list:
            if field_exist(feature_class, f):
                arcpy.DeleteField_management(feature_class, f)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def find_field_by_wildcard(feature_class, wild_card):
    try:
        real_fields = arcpy.ListFields(feature_class)

        for f in real_fields:
            field_name = f.name
            if wild_card in field_name:
                return field_name
                break

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

def delete_fields_by_wildcard(feature_class, wild_card, fields_to_keep):
    try:
        real_fields = arcpy.ListFields(feature_class)

        for f in real_fields:
            field_name = f.name
            if wild_card in field_name:
                if f.name not in fields_to_keep:
                    arcpy.DeleteField_management(feature_class, f.name)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

def get_fields_by_wildcard(feature_class, wild_card, fields_to_skip):
    try:
        real_fields = arcpy.ListFields(feature_class)
        field_list = []

        for f in real_fields:
            field_name = f.name
            if wild_card in field_name:
                if f.name not in fields_to_skip:
                    field_list.append(field_name)

        return(field_list)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])



def copy_features_with_selected_attributes(ws, input_obj, output_obj, keep_fields_list, where_clause, debug):
    # Make an ArcGIS Feature class, containing only the fields
    # specified in keep_fields_list, using an optional SQL query. Default
    # will create a layer/view with NO fields. '
    try:
        if debug == 1:
            msg("--------------------------")
            msg("Executing check_fields...")

        start_time = time.clock()

        field_info_str = ''

        input_fields = arcpy.ListFields(input_obj)

        if not keep_fields_list:
            keep_fields_list = []
        for field in input_fields:
            if field.name in keep_fields_list:
                field_info_str += field.name + ' ' + field.name + ' VISIBLE;'
            else:
                field_info_str += field.name + ' ' + field.name + ' HIDDEN;'

        field_info_str.rstrip(';')  # Remove trailing semicolon

        featureLayer = "feature_lyr"
        arcpy.MakeFeatureLayer_management(input_obj, featureLayer, where_clause, field_info=field_info_str)

        if arcpy.Exists(output_obj):
            arcpy.Delete_management(output_obj)

        arcpy.CopyFeatures_management(featureLayer, output_obj)

        msg_prefix = "Function copy_features_with_selected_attributes completed successfully."
        failed = False

        return output_obj

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "copy_features_with_selected_attributes",
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
            if debug == 1:
                msg(msg_body)
            else:
                pass


def remove_layers_from_scene(project, layer_list):
    start_time = time.clock()
    try:
        msg_prefix = ""

        for m in project.listMaps():  # cycle through the available SCENEs
            if m.mapType == "SCENE":
                for lyr in m.listLayers():
                    if lyr.name in layer_list:
                        layer_name = lyr.name
                        m.removeLayer (lyr)
                        msg_prefix = "Removed " + layer_name + " from project pane."
        failed = False

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "remove_layers_from_scene",
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
            msg(msg_body)


def import_table_with_required_fields(in_table, ws, out_table_name, local_list, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing import_table_with_required_fields...")

    start_time = time.clock()

    try:
        i = 0
        msg_prefix = ""

        if arcpy.Exists(out_table_name):
            arcpy.Delete_management(out_table_name)

        result = arcpy.TableToTable_conversion(in_table, ws, out_table_name)

        if result.status == 4:
            # check necessary fields
            if check_fields(ws + "\\" + out_table_name, local_list, True, debug) == 0:
                msg_prefix = "Function import_table_with_required_fields completed successfully."
            else:
                i = 1
        else:
            i = 1

        failed = False
        return i, ws + "\\" + out_table_name

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "import_table_with_required_fields",
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
            if debug == 1:
                msg(msg_body)
            pass


def get_z_unit(local_lyr, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing get_z_unit...")

    start_time = time.clock()

    try:

        sr = arcpy.Describe(local_lyr).spatialReference
        local_unit = 'Meters'

        if sr.VCS:
            unit_z = sr.VCS.linearUnitName
        else:
            unit_z = sr.linearUnitName
            # msg_body = ("Could not detect a vertical coordinate system for " + get_name_from_feature_class(local_lyr))
            # msg(msg_body)
            # msg_body = ("Using linear units instead.")
            # msg(msg_body)

        if unit_z in ('Foot', 'Foot_US', 'Foot_Int'):
            local_unit = 'Feet'
        else:
            local_unit = 'Meters'

        msg_prefix = "Function get_z_unit completed successfully."
        failed = False

        return local_unit

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_z_unit",
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
            if debug == 1:
                msg(msg_body)


def get_xy_unit(local_lyr, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing get_xy_unit...")

    start_time = time.clock()

    try:

        sr = arcpy.Describe(local_lyr).spatialReference
        local_unit = 'Meters'

        unit_xy = sr.linearUnitName

        if unit_xy in ('Foot', 'Foot_US', 'Foot_Int'):
            local_unit = 'Feet'
        elif unit_xy in ('Meter', 'Meters'):
            local_unit = 'Meters'
        elif unit_xy in ('Degree', 'Degrees'):
            local_unit = 'Degree'
        else:
            local_unit = None

        msg_prefix = "Function get_xy_unit completed successfully."
        failed = False

        return local_unit

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_z_unit",
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
            if debug == 1:
                msg(msg_body)


def get_cs_info(local_lyr, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing is_projected...")

    start_time = time.clock()

    try:
        cs_name = None
        cs_vcs_name = None
        projected = False

        sr = arcpy.Describe(local_lyr).spatialReference

        if sr:
            cs_name = sr.name
            msg_prefix = "Coordinate system: " + cs_name
            msg_body = create_msg_body(msg_prefix, 0, 0)
            msg(msg_body)

            if sr.type == 'PROJECTED' or sr.type == 'Projected':
                projected = True
                msg_prefix = "Coordinate system type: Projected."
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body)
            else:
                projected = False
                msg_prefix = "Coordinate system type: Geographic."
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body)

            if sr.VCS:
                cs_vcs_name = sr.VCS.name
                msg_prefix = "Vertical coordinate system: " + cs_vcs_name
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body)
            else:
                msg_prefix = "No Vertical coordinate system detected."
                msg_body = create_msg_body(msg_prefix, 0, 0)
                msg(msg_body)
        else:
            msg_prefix = "No coordinate system detected."
            msg_body = create_msg_body(msg_prefix, 0, 0)
            msg(msg_body)

        msg_prefix = "Function is_projected completed successfully."
        failed = False

        return cs_name, cs_vcs_name, projected

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "is_projected",
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
            if debug == 1:
                msg(msg_body)


def get_row_values_for_fields_with_floatvalue(lyr, table, fields, select_field, value):
#    msg("--------------------------")
#    msg("Executing get_row_values_for_selected_fields...")
    start_time = time.clock()

    try:
        debug = 0
        value_list = []
        type_list = []
        length_list = []
        check_list = list(fields)
        if select_field is not None:
            check_list.append(select_field)
        return_error = True

        if lyr:
            searchInput = lyr
        else:
            searchInput = get_full_path_from_layer(table)

        if arcpy.Exists(searchInput):
            real_fields = arcpy.ListFields(searchInput)
            if value == "no_expression":
                expression = None
            else:
                expression = """{} = {}""".format(arcpy.AddFieldDelimiters(table, select_field), str(value))
#                expression = arcpy.AddFieldDelimiters(table, select_field) + " = " + str(value)

            if check_fields(searchInput, check_list, return_error, 0) == 0:
                with arcpy.da.SearchCursor(searchInput, fields, expression) as cursor:
                    for row in cursor:
                        i = 0
                        for field in fields:
                            value_list.append(row[i])

                            # for real_field in real_fields:
                            #     if real_field.name == field:
                            #         type_list.append(real_field.type)
                            #         length_list.append(real_field.length)
                            #         break
                            i += 1

        msg_prefix = "Function get_row_values_for_selected_fields completed successfully."
        failed = False

        return value_list

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_row_values_for_selected_fields",
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
            if debug == 1:
                msg(msg_body)


def get_row_values_for_fields(lyr, table, fields, select_field, value):
#    msg("--------------------------")
#    msg("Executing get_row_values_for_selected_fields...")
    start_time = time.clock()

    try:
        debug = 0
        value_list = []
        type_list = []
        length_list = []
        check_list = list(fields)
        if select_field is not None:
            check_list.append(select_field)
        return_error = True

        if lyr:
            searchInput = lyr
        else:
            searchInput = get_full_path_from_layer(table)

        if arcpy.Exists(searchInput):
            real_fields = arcpy.ListFields(searchInput)
            if value == "no_expression":
                expression = None
            else:
                expression = """{} = {}""".format(arcpy.AddFieldDelimiters(table, select_field), str(value))
#                expression = arcpy.AddFieldDelimiters(table, select_field) + " = '" + str(value) + "'"

            if check_fields(searchInput, check_list, return_error, 0) == 0:
                with arcpy.da.SearchCursor(searchInput, fields, expression) as cursor:
                    for row in cursor:
                        i = 0
                        for field in fields:
                            value_list.append(row[i])

                            # for real_field in real_fields:
                            #     if real_field.name == field:
                            #         type_list.append(real_field.type)
                            #         length_list.append(real_field.length)
                            #         break
                            i += 1

        msg_prefix = "Function get_row_values_for_selected_fields completed successfully."
        failed = False

        return value_list

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_row_values_for_selected_fields",
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
            if debug == 1:
                msg(msg_body)


                msg(msg_body)


def set_row_values_for_field(lyr, table, field, value, debug):
    if debug == 1:
        msg("--------------------------")
        msg("Executing set_row_values_for_field...")

    start_time = time.clock()

    return_error = True

    try:
        if lyr:
            searchInput = lyr
        else:
            searchInput = get_full_path_from_layer(table)

        if arcpy.Exists(searchInput):
            real_fields = arcpy.ListFields(searchInput)

            if check_fields(searchInput, [field], return_error, 0) == 0:
                with arcpy.da.UpdateCursor(searchInput, field) as u_cursor:
                    for u_row in u_cursor:
                        u_row[0] = value
                        u_cursor.updateRow(u_row)

        msg_prefix = "Function set_row_values_for_field completed successfully."
        failed = False

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "set_row_values_for_field",
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
            if debug == 1:
                msg(msg_body)


def get_extent_feature(local_ws, local_features):

#    msg("--------------------------")
#    msg("Executing get_extent_area...")
    start_time = time.clock()

    try:
        debug = 0

        extent_feature = os.path.join(local_ws, get_name_from_feature_class(local_features) + "_extent")
        if arcpy.Exists(extent_feature):
            arcpy.Delete_management(extent_feature)

        desc = arcpy.Describe(local_features)
        extent = desc.extent
        array = arcpy.Array()
        # Create the bounding box
        array.add(extent.lowerLeft)
        array.add(extent.lowerRight)
        array.add(extent.upperRight)
        array.add(extent.upperLeft)
        # ensure the polygon is closed
        array.add(extent.lowerLeft)
        # Create the polygon object
        polygon = arcpy.Polygon(array)
        array.removeAll()

        # save to disk
        base_sr = arcpy.Describe(local_features).spatialReference
        arcpy.CopyFeatures_management(polygon, extent_feature)
        arcpy.DefineProjection_management(extent_feature, base_sr)

        del polygon

        msg_prefix = "Function get_extent_feature function completed successfully."
        failed = False

        return extent_feature

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_extent_feature",
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
            if debug == 1:
                msg(msg_body)


def get_extent_area(local_ws, local_features):

#    msg("--------------------------")
#    msg("Executing get_extent_area...")
    start_time = time.clock()

    try:
        debug = 0
        if in_memory_switch:
            temp_hull = "in_memory/temp_hull"
        else:
            temp_hull = os.path.join(local_ws, "temp_hull")
            if arcpy.Exists(temp_hull):
                arcpy.Delete_management(temp_hull)

        desc = arcpy.Describe(local_features)
        extent = desc.extent
        array = arcpy.Array()
        # Create the bounding box
        array.add(extent.lowerLeft)
        array.add(extent.lowerRight)
        array.add(extent.upperRight)
        array.add(extent.upperLeft)
        # ensure the polygon is closed
        array.add(extent.lowerLeft)
        # Create the polygon object
        polygon = arcpy.Polygon(array)
        array.removeAll()
        # save to disk
        arcpy.CopyFeatures_management(polygon, temp_hull)
        arcpy.AddField_management(temp_hull, "Shape_Area", "DOUBLE")
        exp = "!shape.area!"
        arcpy.CalculateField_management(temp_hull, "Shape_Area", exp, "PYTHON_9.3")

        del polygon

        msg_prefix = "Function get_extent_area function completed successfully."
        failed = False

        return get_row_values_for_fields(None, temp_hull, ["Shape_Area"], None, "no_expression")[0]

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "get_extent_area",
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
            if debug == 1:
                msg(msg_body)


def check_max_number_of_split(ws, features, id_field, area_field, my_area_field, panel_size, max_split, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing check_max_number_of_split...")

    start_time = time.clock()

    try:
        check = True

        # check feature type
        input_type = arcpy.Describe(features).shapetype
        units = arcpy.Describe(features).spatialReference.linearUnitName
        local_area_field = area_field

        # go to polygon to get SHAPE_Area
        if input_type == "MultiPatch":
            calculate_footprint_area(ws, features, area_field, my_area_field, id_field, debug)
            local_area_field = my_area_field

        # check for SHAPE_Area attribute
        if check_fields(features, [local_area_field], True, debug) == 0:
            unique_field_values = unique_values(features, local_area_field)

            list_len = len(unique_field_values)
            largest_area = unique_field_values[list_len - 1]

            if "Foot" in units:
                largest_area *= 0.092903

            if "Feet" in units:
                largest_area *= 0.092903

            number_of_panels = largest_area / (panel_size * panel_size)

            if number_of_panels > max_split:
                check = False

        msg_prefix = "Function check_max_number_of_split completed successfully."
        failed = False

        return check

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "check_max_number_of_split",
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
            if debug == 1:
                msg(msg_body)


def calculate_footprint_area(ws, features, area_field, my_area_field, join_field, debug):
    if debug == 1:
        msg("--------------------------")
        msg("Executing calculate_footprint_area...")

    start_time = time.clock()

    try:
        temp_footprint = os.path.join(ws, "temp_footprint")
        if arcpy.Exists(temp_footprint):
            arcpy.Delete_management(temp_footprint)

        arcpy.MultiPatchFootprint_3d(features, temp_footprint)
        delete_add_field(temp_footprint, my_area_field, "DOUBLE")
        arcpy.CalculateField_management(temp_footprint, my_area_field, "!" + area_field + "!", "PYTHON_9.3", None)

        fieldList = [my_area_field]

        delete_fields(features, fieldList)

        arcpy.JoinField_management(features, join_field, temp_footprint, join_field, fieldList)

        msg_prefix = "Function calculate_footprint_area completed successfully."
        failed = False

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "calculate_footprint_area",
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
            if debug == 1:
                msg(msg_body)


def list_rasters_in_gdb(gdb, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing list_rasters_in_gdb...")

    start_time = time.clock()

    try:
        # list all rasters in a geodatabase, including inside Feature Datasets '''
        arcpy.env.workspace = gdb

        list = arcpy.ListRasters()

        msg_prefix = "Function list_fcs_in_gdb completed successfully."
        failed = False

        return list

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "list_fcs_in_gdb",
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
            if debug == 1:
                msg(msg_body)

def list_fcs_in_gdb(gdb, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing list_fcs_in_gdb...")

    start_time = time.clock()

    try:
        # list all Feature Classes in a geodatabase, including inside Feature Datasets '''
        arcpy.env.workspace = gdb

        fcs = []
        for fds in arcpy.ListDatasets('', 'feature') + ['']:
            for fc in arcpy.ListFeatureClasses('', '', fds):
                # yield os.path.join(fds, fc)
                fcs.append(os.path.join(fds, fc))

        msg_prefix = "Function list_fcs_in_gdb completed successfully."
        failed = False

        return fcs

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "list_fcs_in_gdb",
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
            if debug == 1:
                msg(msg_body)

def listFcsInGDB(gdb):
    try:
        # list all Feature Classes in a geodatabase, including inside Feature Datasets '''
        arcpy.env.workspace = gdb

        fcs = []
        for fds in arcpy.ListDatasets('', 'feature') + ['']:
            for fc in arcpy.ListFeatureClasses('', '', fds):
                # yield os.path.join(fds, fc)
                fcs.append(os.path.join(fds, fc))
        return fcs

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

def threeD_enable_featurclass(ws, feature_class, elevation_surface, unique_ID, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing threeD_enable_featurclass...")

    start_time = time.clock()

    try:
        BASEELEVATIONfield = "BASEELEV"
        arcpy.env.mask = feature_class
        DTMMin = os.path.join(ws, "DTMMin")
        if arcpy.Exists(DTMMin):
            arcpy.Delete_management(DTMMin)
        DTMMinRaster = arcpy.sa.ZonalStatistics(feature_class, unique_ID, elevation_surface, "MINIMUM", "DATA")
        DTMMinRaster.save(DTMMin)

        feature_point = os.path.join(ws, "feature_points")
        if arcpy.Exists(feature_point):
            arcpy.Delete_management(feature_point)
        arcpy.FeatureToPoint_management(feature_class, feature_point, "INSIDE")

        arcpy.AddSurfaceInformation_3d(feature_point, DTMMin, "Z", "BILINEAR", 1, 1, 0, None)
        arcpy.AddField_management(feature_point, BASEELEVATIONfield, "FLOAT")
        arcpy.CalculateField_management(feature_point, BASEELEVATIONfield, "!Z!", "PYTHON_9.3", None)
        if arcpy.Exists(DTMMin):
            arcpy.Delete_management(DTMMin)

        # Join Base Elevation
        arcpy.JoinField_management(feature_class, unique_ID, feature_point, unique_ID, BASEELEVATIONfield)

        msg_prefix = "Function threeD_enable_featurclass completed successfully."
        failed = False

        return feature_class, BASEELEVATIONfield

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "threeD_enable_featurclass",
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
            if debug == 1:
                msg(msg_body)


def create_surface_from_points(local_ws, local_tin_ws, local_fc, local_field, local_error):
    try:
        minValue = arcpy.SearchCursor(local_fc, "", "", "", local_field + " A").next().getValue(local_field)  # Get 1st row in ascending cursor sort

        if not minValue:
            minValue = 0

        expression = """{} > {} And {} < {}""".format(arcpy.AddFieldDelimiters(local_fc, local_field), minValue, arcpy.AddFieldDelimiters(local_fc, local_field), local_error)

        # select all points with good elevation values
        local_layer = get_name_from_feature_class(local_fc) + "_lyr"
        select_lyr = arcpy.MakeFeatureLayer_management(local_fc, local_layer).getOutput(0)
        arcpy.SelectLayerByAttribute_management(local_layer, "NEW_SELECTION", expression)

        GoodPoints = os.path.join(local_ws, "good_points")
        if arcpy.Exists(GoodPoints):
            arcpy.Delete_management(GoodPoints)

        # write to fc
        arcpy.CopyFeatures_management(local_layer, GoodPoints)

        # generate surface
        arcpy.AddMessage("Interpolating values...")

        out_tin = os.path.join(local_tin_ws, "PointTin")
        if arcpy.Exists(out_tin):
            arcpy.Delete_management(out_tin)

        arcpy.CreateTin_3d(out_tin, arcpy.Describe(local_fc).spatialReference, "{} {} Mass_Points <None>".format(GoodPoints, local_field), "DELAUNAY")

        return out_tin

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def Point3DToObject(ws, rpk, in_features, elevation_attribute, buffer_attribute, height_attribute, output_features, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing Point3DToObject...")

    start_time = time.clock()

    try:

        # Buffer
        bufferedFeatures = os.path.join(ws, "bufferedFeatures")
        if arcpy.Exists(bufferedFeatures):
            arcpy.Delete_management(bufferedFeatures)

        arcpy.Buffer_analysis(in_features, bufferedFeatures, buffer_attribute)

        # Make 3D again
        buffered3DFeatures = os.path.join(ws, "buffered3DFeatures")
        if arcpy.Exists(buffered3DFeatures):
            arcpy.Delete_management(buffered3DFeatures)

        arcpy.FeatureTo3DByAttribute_3d(bufferedFeatures, buffered3DFeatures, elevation_attribute)

        HEIGHT_FIELD = "extrusion_height"
        UNIT_FIELD = "extrusion_unit"

        delete_add_field(buffered3DFeatures, HEIGHT_FIELD, "DOUBLE")
        arcpy.CalculateField_management(buffered3DFeatures, HEIGHT_FIELD, "!" + height_attribute + "!", "PYTHON_9.3", None)

        z_unit = get_z_unit(buffered3DFeatures, debug)
        delete_add_field(buffered3DFeatures, UNIT_FIELD, "TEXT")
        arcpy.CalculateField_management(buffered3DFeatures, UNIT_FIELD, "'" + z_unit + "'", "PYTHON_9.3", None)

        if arcpy.Exists(rpk):
           arcpy.FeaturesFromCityEngineRules_3d(buffered3DFeatures, rpk, output_features, "INCLUDE_EXISTING_FIELDS")
           msg_prefix = "Function Point3DToObject completed successfully."
           failed = False
        else:
            msg_body = ("Can't find " + rpk + " in the " + os.path.dirname(rpk) + " folder")
            msg(msg_body)
            failed = True

        return(output_features)

        pass

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "Point3DToObject",
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
            if debug == 1:
                msg(msg_body)


def get_attribute_range(local_input_features, attribute):

    try:
        # cycle through features, get minimum and maximum value

        # create a list of unique "Attribute" values
        unique_field_values = unique_values(local_input_features, attribute)

        return [unique_field_values[0], unique_field_values[len(unique_field_values)-1]]

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def get_unit_vector(v):
    # Normalize a vector.
    # This input vector is not expected to be normalized but the output vector is.
    # Both input and output vectors' XYZ components are contained in tuples.

    magnitude = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    x = v[0]/magnitude
    y = v[1]/magnitude
    z = v[2]/magnitude
    return x, y, z


def get_distance(v1, v2):
    distance = math.sqrt(math.pow((v1[0] - v2[0]), 2) + math.pow((v1[1] - v1[1]), 2)+math.pow((v1[2] - v1[2]), 2))

    return distance


def GetSlope(vect1, vect2):

    uv1 = get_unit_vector(vect1)
    uv2 = get_unit_vector(vect2)

    dist_a = get_distance(uv1, uv2)
    dist_o = uv1[2]-uv2[2]

    if dist_o > 0:
        slope = math.degrees(math.sin(dist_o/dist_a))
    else:
        slope = 0

    return slope


def find_closest(my_list, my_number):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(my_list, my_number)
    if pos == 0:
        return my_list[0], 0
    if pos == len(my_list):
        return my_list[-1], len(my_list) - 1
    before = my_list[pos - 1]
    after = my_list[pos]
    if after - my_number < my_number - before:
       return after, pos
    else:
       return before, pos - 1


def set_data_paths_for_packaging(data_dir, gdb, fc, model_dir, pf, rule_dir, rule, layer_dir, lf):
    try:
        scriptPath = sys.path[0]
        thisFolder = os.path.dirname(scriptPath)

        dataPath = os.path.join(thisFolder, data_dir)
        one_fc = os.path.join(dataPath, gdb, fc)

        modelPath = os.path.join(thisFolder, model_dir)
        one_modelfile = os.path.join(modelPath, pf)

        rulePath = os.path.join(thisFolder, rule_dir)
        one_rulefile = os.path.join(rulePath, rule)

        layerPath = os.path.join(thisFolder, layer_dir)
        one_layerfile = os.path.join(layerPath, lf)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def rename_file_extension(data_dir, from_extentsion, to_extension):
    try:
        files = os.listdir(data_dir)
        for filename in files:
            infilename = os.path.join(data_dir, filename)
            if os.path.isfile(infilename):
                file_ext = os.path.splitext(filename)[1]
                if from_extentsion == file_ext:
                    newfile = infilename.replace(from_extentsion, to_extension)
                    os.rename(infilename, newfile)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])


def unitConversion(layer_unit, input_unit, debug):

    if debug == 1:
        msg("--------------------------")
        msg("Executing unitConversion...")

    start_time = time.clock()

    try:

        conversionFactor = 1

        # to feet
        if layer_unit == "Feet":
            unitToFeetConversion = {'Inches': 0.0833333,
                                    'Feet': 1,
                                    'Yards': 3.000000096,
                                    'Miles': 5280.00016896,
                                    'Nautical Miles': 6076.11568,
                                    'Millimeters': 0.00328084,
                                    'Centimeters': 0.0328084,
                                    'Decimeters': 0.328084,
                                    'Meters': 3.28084,
                                    'Kilometers': 3280.84}

            conversionFactor = unitToFeetConversion[input_unit]

        # to meters
        if layer_unit == "Meters":
            unitToMeterConversion = {'Inches': 0.0254,
                                    'Feet': 0.3048,
                                    'Yards': 0.9144,
                                    'Miles': 1609.34,
                                    'Nautical Miles': 1852,
                                    'Millimeters': 0.001,
                                    'Centimeters': 0.01,
                                    'Decimeters': 0.1,
                                    'Meters': 1,
                                    'Kilometers': 1000}

            conversionFactor = unitToMeterConversion[input_unit]

        msg_prefix = "Function unitConversion completed successfully."
        failed = False

        return conversionFactor

    except:
        line, filename, synerror = trace()
        failed = True
        msg_prefix = ""
        raise FunctionError(
            {
                "function": "unitConversion",
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
            if debug == 1:
                msg(msg_body)


