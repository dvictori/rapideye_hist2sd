#!/c/OSGEO4W64/bin/python
# -*- coding: utf-8 -*-

## Depending on were you are going to execute this, you should change the shebang
## When running on windows (under MSys), program takes too long to start when using '/usr/bin/env python'
## better link directly to python executable
## Also, o windows I sometimes get a "python stoped working" error when the code ends
## If you don't want to keep seeing those errors, you can use pythonw executable instead (will run withuout opening a prompt)
## however, it will keep popping up some terminal windows with the gdalwarp process -- anoying
#!/c/OSGEO4W64/bin/pythonw
#!/usr/bin/env python


"""
Created on Wed May 28 18:34:48 2014

Program to process original RapidEye Images
Should get the original 5 bands, 16 bit
keep only the first three bands, apply a 2sd histogram stretch
export as 8bit, epsg:4326

@author: Daniel
daniel.victoria@gmail.com

I give no guarantees this will work. Keep your fingers crossed :)

1/dec/2016 - Add option to consider nodata values
    Treat a specific value as nodata. Ignores this value from statistics calculation
"""

from osgeo import gdal
from scipy.interpolate import interp1d
import sys, os
from subprocess import call
from numpy import zeros
import argparse

parser = argparse.ArgumentParser(
    description='Applies a mean +-2SD histogram stretch to images and converts to 8bit',
    epilog='Output image will have the prefix: 8bit_2sd_epsg4326_')
parser.add_argument('input_image', help='Input image to be processed')
parser.add_argument('out_path', help='Output directory')
parser.add_argument('-n', '--nodata', help='set input NoData value', type=int)
args = parser.parse_args()

infile = args.input_image
out_path = args.out_path

nome = os.path.basename(infile)
nome_saida_tmp = os.path.join(out_path, "8bit_2sd_temp_"+nome)
nome_saida = os.path.join(out_path, "8bit_2sd_epsg4326_"+nome)

# test if output file alredy exists
# if so, stop program
if os.path.isfile(nome_saida):
    print("Output file %s alredy exists. DONE" % nome_saida)
    sys.exit()

inIMG = gdal.Open(infile)

# getting stats for the first 3 bands
# Using ComputeBandStats insted of stats array has min, max, mean and sd values
# ComputeBandStats does not remove NoData
# Must first set NoData and then use ComputeStatistics
print("Computing band statistics")
bandas = [inIMG.GetRasterBand(b+1) for b in range(3)]
if args.nodata is not None:
    [b.SetNoDataValue(args.nodata) for b in bandas]

band_stats = [b.ComputeStatistics(False) for b in bandas]
minMax = [i[:2] for i in band_stats]
meanSD = [i[2:] for i in band_stats]

# rescale image using mean+- 2* SD
# if mean-2*sd < band(min), use band(min)
# also, must garantee that min is more then 0 in order to use nodata values
# if mean+2*sd > band(max), use band(max)

bandVals = [[0, max(minMax[b][0], 1, meanSD[b][0] - 2* meanSD[b][1]),
             min(minMax[b][1], meanSD[b][0] + 2*meanSD[b][1]), 65536] for b in range(3)]

# leaving zero as nodata
transfVals = [0,1, 254, 255]

transfFunc = [interp1d(bandVals[b], transfVals) for b in range(3)]

print("Saving temp output image")
# Creating output image prior to reprojection       
driver = gdal.GetDriverByName('GTiff')
dest_img = driver.Create(nome_saida_tmp, inIMG.RasterXSize, inIMG.RasterYSize, 3, gdal.gdalconst.GDT_Byte)
dest_img.SetGeoTransform(inIMG.GetGeoTransform())
dest_img.SetProjection(inIMG.GetProjection())

for b in range(3):
    banda_in = bandas[b].ReadAsArray()
    b_saida = zeros((inIMG.RasterXSize, inIMG.RasterYSize), dtype=int)    
    for l in range(inIMG.RasterYSize):
        b_saida[l] = transfFunc[b](banda_in[l]).astype(int)
    dest_img.GetRasterBand(b+1).WriteArray(b_saida)

# closing dataset
b_saida = None
dest_img = None
inIMG = None

# reprojecting to espg4326 using gdalwarp
# too lazy to do it from scratch inside python
# must specify input nodata in order for nodata output be correct
print("Reprojecting image")
call(["gdalwarp", "-t_srs", "epsg:4326", "-dstnodata", "0 0 0", "-srcnodata", "0 0 0", "-r", "cubic", nome_saida_tmp, nome_saida], shell=False)
os.remove(nome_saida_tmp)
