#-------------------------------------------------------------------------------
# Name:        CreateElevationTilePackageForAGOL
# Purpose:
#
# Author:      Gert van Maren
#
# Created:     27/07/2016
# Copyright:   (c) Esri 2016
# updated:
# updated:
# updated:
#-------------------------------------------------------------------------------

import arcpy
import os
import sys
import shutil
import re
import common_lib

class LicenseError3D(Exception):
    pass

class LicenseErrorSpatial(Exception):
    pass

class NoFeatures(Exception):
    pass

class No3DFeatures(Exception):
    pass

arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3d")

arcpy.env.overwriteOutput = True

DeleteIntermediateData = True

# Get Attributes from User
debugging = 0

if debugging == 0:
    inputDataSource = arcpy.GetParameter(0)
    scaleLevel = arcpy.GetParameterAsText(1)
    userLERC = arcpy.GetParameterAsText(2)
    cacheDirectory = arcpy.GetParameterAsText(3)
#else:
    #Debug
#    inputDataSource = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\3DBaseScenes\work1.3\LocalGovernmentScenes\LocalGovernmentScenes.gdb\DTM_meters_ProjectRaster'
#    scaleLevel = 10
#    userLERC = 0.1
#    cacheDirectory = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\3DBaseScenes\work1.3\LocalGovernmentScenes\cache'
#    project_ws = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\3DBaseScenes\work1.3\LocalGovernmentScenes\LocalGovernmentScenes.gdb'

def getNameFromFeatureClass(feature_class):
    descFC = arcpy.Describe(feature_class)
    return(descFC.name)

# Get Workspace from Building feature class location
def getWorkSpaceFromFeatureClass(feature_class, get_gdb):
    dirname = os.path.dirname(arcpy.Describe(feature_class).catalogPath)
    desc = arcpy.Describe(dirname)

    if hasattr(desc, "datasetType") and desc.datasetType == 'FeatureDataset':
        dirname = os.path.dirname(dirname)

    if (get_gdb == "yes"):
        return(dirname)
    else:                   # directory where gdb lives
        return(os.path.dirname(dirname))

def GenerateLERCTilingScheme(input_layer, cache_directory, error):
    try:
        # variables
        method = "PREDEFINED"
        numscales = "20"
        predefScheme = schemeDirectory+"\\ArcGIS_Online_Bing_Maps_Google_Maps.xml"
        outputTilingScheme = schemeDirectory+"\\"+getNameFromFeatureClass(input_layer)+"_tiling_lerc.xml"
#        scales = "#"
#        scaleType = "#"
        tileOrigin = "#"
        dpi = "96"
        tileSize = "256 x 256"
        tileFormat = "LERC"
        compQuality = "75"
        storageFormat = "COMPACT"
        lerc_error = error
        scales = [1128.497176, 2256.994353, 4513.988705, 9027.977411, 18055.954822, 36111.909643, 72223.819286,
              144447.638572,
              288895.277144, 577790.554289, 1155581.108577, 2311162.217155, 4622324.434309, 9244648.868618,
              18489297.737236,
              36978595.474472, 73957190.948944, 147914381.897889, 295828763.795777, 591657527.591555]

        scaleType = "SCALE"

        arcpy.GenerateTileCacheTilingScheme_management(input_layer, outputTilingScheme, method, numscales, predefScheme,
                                                        scales, scaleType, tileOrigin, dpi, tileSize, tileFormat, compQuality, storageFormat, lerc_error)

        # return obstruction FC
        return (outputTilingScheme)

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


def ManageTileCache(input_layer, cache_directory, output_scheme, scale_level):
    try:
        # variables
        scales = [1128.497176,2256.994353,4513.988705,9027.977411,18055.954822,36111.909643,72223.819286,144447.638572,
                  288895.277144,577790.554289,1155581.108577,2311162.217155,4622324.434309,9244648.868618,18489297.737236,
                  36978595.474472,73957190.948944,147914381.897889,295828763.795777,591657527.591555]

        list_length = len(scales)

        folder = cache_directory
        mode = "RECREATE_ALL_TILES"
        cacheName = getNameFromFeatureClass(input_layer) + "_cache"
        dataSource = input_layer
        method = "IMPORT_SCHEME"
        tilingScheme = output_scheme
        scale_default = "#"
        areaofinterest = "#"
        maxcellsize = "#"
        maxcachedscale = str(scales[0])
        mincachedscale = str(scales[list_length - 1 - scale_level])

        #  check if directory is present
        if arcpy.Exists(folder+"\\"+cacheName):
            shutil.rmtree(folder+"\\"+cacheName)
            arcpy.AddMessage("Deleted old cache directory: "+folder+"\\"+cacheName)

        arcpy.AddMessage("Creating Tile Cache with "+str(list_length - scale_level)+" levels: L"+str(scale_level)+":"+mincachedscale+" down to L:"+str(list_length - 1)+":"+maxcachedscale)

        result = arcpy.ManageTileCache_management(
            folder, mode, cacheName, dataSource, method, tilingScheme,
            scale_default, areaofinterest, maxcellsize, mincachedscale, maxcachedscale)

        ##arcpy.AddMessage(result.status)

        # return obstruction FC
        return (folder+"\\"+cacheName)

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


def ExportTileCache(input_layer, cache_directory, tile_cache):
    try:
        cacheSource = tile_cache
        cacheFolder = cache_directory
        cachePackage = getNameFromFeatureClass(input_layer)
        cacheType = "TILE_PACKAGE"

        arcpy.AddMessage("Creating Tile Package: " + cacheFolder + "\\" +cachePackage+".tpk. This might take some time...")
        arcpy.GetMessages()
        arcpy.ExportTileCache_management(cacheSource, cacheFolder, cachePackage,
                                         cacheType)

        return (cacheFolder + "\\" + cachePackage)

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


try:
    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")
    else:
        raise LicenseError3D

    if debugging == 0:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        homeFolder = aprx.homeFolder

        if os.path.exists(homeFolder + "\\p20"):      # it is a package
            homeFolder = homeFolder + "\\p20"

        arcpy.AddMessage("Project Home Directory is: " + homeFolder)

        schemeDirectory = homeFolder+"\\tiling_schemes"
#    else:
#        homeFolder = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\3DBaseScenes\work1.3\LocalGovernmentScenes'
#        schemeDirectory = r'D:\Gert\Work\Esri\Solutions\LocalGovernment\3DBaseScenes\work1.3\LocalGovernmentScenes\tiling_schemes'

    layerDirectory = homeFolder + "\\layer_files"

    if os.path.exists(layerDirectory):
        common_lib.rename_file_extension(layerDirectory, ".txt", ".lyrx")

    # fail safe for Europese's comma's
    lercError = float(re.sub("[,.]", ".", userLERC))
    scaleLevel = re.sub("[,.]", ".", scaleLevel)

    outputTilingScheme = GenerateLERCTilingScheme(inputDataSource, cacheDirectory, lercError)
    arcpy.AddMessage("Created LERC Tiling Scheme with LERC error: "+str(lercError))

    tileCache = ManageTileCache(inputDataSource, cacheDirectory, outputTilingScheme, int(scaleLevel))
    arcpy.AddMessage("Created Tile Cache...")

    arcpy.AddMessage("Exporting to Tile Package...")
    tilePackage = ExportTileCache(inputDataSource, cacheDirectory, tileCache)


except LicenseError3D:
    print("3D Analyst license is unavailable")
    arcpy.AddError("3D Analyst license is unavailable")

except LicenseErrorSpatial:
    print("Spatial Analyst license is unavailable")
    arcpy.AddError("Spatial Analyst license is unavailable")

except NoFeatures:
    # The input has no features
    #
    print(('Error creating feature class'))
    arcpy.AddError('Error creating feature class')

except No3DFeatures:
    # The input has no 3D features
    #
    print(('2D features are not supported. Drag your 2D layer to the 3D layers section in the TOC and use the "Layer 3D to Feature Class" GP tool to create 3D features.'))
    arcpy.AddError('2D features are not supported. Drag your 2D layer to the 3D layers section in the TOC and use the "Layer 3D to Feature Class" GP tool to create 3D features.')

except arcpy.ExecuteWarning:
    print ((arcpy.GetMessages(1)))
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

finally:
    # Check in the 3D Analyst extension
    #
    arcpy.CheckInExtension("3D")
    # Check in the Spatial Analyst extension
    #
    arcpy.CheckInExtension("spatial")