import arcpy
import os

import scripts.create_3Dflood_level as create_3Dflood_level

import importlib
importlib.reload(create_3Dflood_level)  # force reload of the module

import scripts.common_lib as common_lib

class Create3DFloodLevelFromRaster(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create 3D Flood Level From Raster"
        self.description = "Creates a 3D Flood Level layer using a " + \
                            "Water Surface elevation raster as input."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_source = arcpy.Parameter(displayName="Input Flooding Layer",
                                  name="FloodingInput",
                                  datatype="GPRasterLayer",
                                  parameterType="Required",
                                  direction="Input")

        no_flood_value = arcpy.Parameter(displayName="No Flooding Value",
                                  name="NoFloodingValue",
                                  datatype="GPString",
                                  parameterType="Required",
                                  direction="Input")

        baseline_elevation = arcpy.Parameter(displayName="Baseline Elevation",
                                  name="BaselineElevation",
                                  datatype = "GPRasterLayer",
                                  parameterType="Optional",
                                  direction="Input")

        baseline_flood_value = arcpy.Parameter(displayName="Baseline Elevation Value",
                                  name="BaselineElevationValue",
                                  datatype = "Double",
                                  parameterType="Required",
                                  direction="Input")

        flood_value = arcpy.Parameter(displayName="Flood Value",
                                  name="FloodValue",
                                  datatype = "Double",
                                  parameterType="Required",
                                  direction="Input")

        outward_buffer_value = arcpy.Parameter(displayName="Buffer Value",
                                  name="BufferValue",
                                  datatype = "Double",
                                  parameterType="Optional",
                                  direction="Input")

        output_polygons = arcpy.Parameter(displayName="Output Features",
                                  name="Output Features",
                                  datatype="DEFeatureClass",
                                  parameterType="Required",
                                  direction="Output")

        derived_polygons = arcpy.Parameter(displayName="layer 1",
                                  name="layer 1",
                                  datatype="GPFeatureLayer",
                                  parameterType="Derived", enabled=True,
                                  direction="Output")

        derived_polygons2 = arcpy.Parameter(displayName="layer 2",
                                  name="layer 2",
                                  datatype="GPFeatureLayer",
                                  parameterType="Derived", enabled=True,
                                  direction="Output")

        outward_buffer_value.enabled = False
        outward_buffer_value.value = 0
        no_flood_value.value = "NoData"
        baseline_elevation.value = None
        baseline_flood_value.value = 0
        flood_value.value = 0
        outward_buffer_value.value = 0

        derived_polygons.parameterDependencies = [input_source.name]
        derived_polygons2.parameterDependencies = [input_source.name]

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layer_directory = aprx.homeFolder + "\\layer_files\\"

        derived_polygons.symbology = os.path.join(layer_directory, 'flood3Dfeet.lyrx')
        derived_polygons2.symbology = os.path.join(layer_directory, 'flood3Dmeter.lyrx')

        params = [input_source, no_flood_value, baseline_elevation, baseline_flood_value, flood_value, outward_buffer_value, output_polygons, derived_polygons, derived_polygons2]

        return params


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return


    def execute(self, parameters, messages):

        class NoLayerFile(Exception):
            pass

        class NoRasterLayer(Exception):
            pass

        class NoOutput(Exception):
            pass

        try:
            """The source code of the tool."""
            input_source, no_flood_value, baseline_elevation, baseline_flood_value, flood_value, outward_buffer, output_polygons = [p.valueAsText for p in parameters[:-2]]

            # check if input exists
            if arcpy.Exists(input_source):
                full_path_source = common_lib.get_full_path_from_layer(input_source)
            else:
                raise NoRasterLayer

            if baseline_elevation != None:
                if arcpy.Exists(baseline_elevation):
                    full_path_raster_source = common_lib.get_full_path_from_layer(baseline_elevation)
                else:
                    arcpy.AddWarning("Can't find: " + common_lib.get_name_from_feature_class(baseline_elevation))
                    full_path_raster_source = None
            else:
                full_path_raster_source = None

            desc = arcpy.Describe(input_source)

            flood_polygons = create_3Dflood_level.flood_from_raster(input_source=full_path_source,
                                        input_type=desc.dataType,
                                        no_flood_value=no_flood_value,
                                        baseline_elevation=full_path_raster_source,
                                        baseline_flood_value=parameters[2].value,
                                        flood_value=parameters[3].value,
                                        outward_buffer=parameters[4].value,
                                        output_polygons=output_polygons, debug=0)

            if flood_polygons:
                if common_lib.get_z_unit(flood_polygons, 0) == "Feet":
                    arcpy.SetParameter(7, flood_polygons)
                else:
                    arcpy.SetParameter(8, flood_polygons)
            else:
                raise NoOutput

        except NoRasterLayer:
            print("Can't find Raster layer. Exiting...")
            arcpy.AddError("Can't find Raster layer. Exiting...")

        except NoOutput:
            print("Can't create output. Exiting...")
            arcpy.AddError("Can't create output. Exiting...")


class Create3DFloodLevelFromPolygons(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create 3D Flood Level From Polygons"
        self.description = "Creates a 3D Flood Level layer using a " + \
                            "Water Surface elevation polygon feature class as input."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_source = arcpy.Parameter(displayName="Input Flooding Layer",
                                  name="FloodingInput",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")

        no_flood_value = arcpy.Parameter(displayName="No Flooding Value",
                                  name="NoFloodingValue",
                                  datatype="GPString",
                                  parameterType="Required",
                                  direction="Input")

        baseline_flood_value = arcpy.Parameter(displayName="Baseline Value",
                                  name="BaselineFlood",
                                  datatype = "Double",
                                  parameterType="Optional",
                                  direction="Input")

        flood_value = arcpy.Parameter(displayName="Flood Value",
                                  name="Flood",
                                  datatype = "Double",
                                  parameterType="Optional",
                                  direction="Input")

        outward_buffer_value = arcpy.Parameter(displayName="Buffer Value",
                                  name="BufferValue",
                                  datatype = "Double",
                                  parameterType="Optional",
                                  direction="Input")

        output_polygons = arcpy.Parameter(displayName="Output Features",
                                  name="Output Features",
                                  datatype="DEFeatureClass",
                                  parameterType="Required",
                                  direction="Output")

        derived_polygons = arcpy.Parameter(displayName="layer 1",
                                  name="layer 1",
                                  datatype="GPFeatureLayer",
                                  parameterType="Derived", enabled=True,
                                  direction="Output")

        derived_polygons2 = arcpy.Parameter(displayName="layer 2",
                                  name="layer 2",
                                  datatype="GPFeatureLayer",
                                  parameterType="Derived", enabled=True,
                                  direction="Output")

        no_flood_value.value = "NoData"
        baseline_flood_value.value = 0
        flood_value.value = 0
        outward_buffer_value.value = 0

        derived_polygons.parameterDependencies = [input_source.name]
        derived_polygons2.parameterDependencies = [input_source.name]

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layer_directory = aprx.homeFolder + "\\LayerFiles"

        derived_polygons.symbology = os.path.join(layer_directory, 'flood3Dfeet.lyrx')
        derived_polygons2.symbology = os.path.join(layer_directory, 'flood3Dmeter.lyrx')

        params = [input_source, no_flood_value, baseline_flood_value, flood_value, outward_buffer_value, output_polygons, derived_polygons, derived_polygons2]

        return params


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return


    def execute(self, parameters, messages):

        class NoPolygonLayer(Exception):
            pass

        class NoOutput(Exception):
            pass

        try:
            """The source code of the tool."""
            input_source, no_flood_value, baseline_flood_value, flood_value, outward_buffer, output_polygons = [p.valueAsText for p in parameters[:-2]]

            arcpy.AddError("Can't create outsfdvsfdvdfdvdfvsfdvput. Exiting...")

            # check if input exists
            if arcpy.Exists(input_source):
                full_path_source = common_lib.get_full_path_from_layer(input_source)
            else:
                raise NoPolygonLayer

            desc = arcpy.Describe(input_source)

            flood_polygons = create_3Dflood_level.flood_from_polygon(input_source=full_path_source,
                                        input_type=desc.dataType,
                                        no_flood_value=no_flood_value,
                                        baseline_flood_value=parameters[2].value,
                                        flood_value=parameters[3].value,
                                        outward_buffer=parameters[4].value,
                                        output_polygons=output_polygons, debug=0)

            if flood_polygons:
                if common_lib.get_z_unit(flood_polygons, 0) == "Feet":
                    arcpy.SetParameter(7, flood_polygons)
                else:
                    arcpy.SetParameter(8, flood_polygons)
            else:
                raise NoOutput

        except NoPolygonLayer:
            print("Can't find polygon layer file. Exiting...")
            arcpy.AddError("Can't find polygon layer. Exiting...")

        except NoOutput:
            print("Can't create output. Exiting...")
            arcpy.AddError("Can't create output. Exiting...")




class CreateDepthRaster(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Depth Raster"
        self.description = "Create Depth Raster"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        return

# for debug only!
def main():
#    tool = Create3DFloodLevel()
#    tool.run("", "", "", "", "", "", 1)
    create_3Dflood_level.main("", "", "", "", "", "", "", 1)

if __name__ == "__main__":
    main()
