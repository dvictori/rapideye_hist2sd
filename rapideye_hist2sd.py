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

29/dec/2016 - add option to consider cloud and nodata mask that comes with rapideye images
    This option considers that UDM file has the same name as the input file, 
    with _udm.tif ending. And both files are located in the same directory
    Working at the end of the year -- yeahhh
"""

from osgeo import gdal
from scipy.interpolate import interp1d
import sys, os
from subprocess import call
import numpy as np
import argparse
from scipy.misc import imresize

parser = argparse.ArgumentParser(
    description='Applies a mean +-2SD histogram stretch to images and converts to 8bit',
    epilog='Output image will have the prefix: 8bit_2sd_epsg4326_')
parser.add_argument('input_image', help='Input image to be processed')
parser.add_argument('out_path', help='Output directory')
parser.add_argument('-n', '--nodata', help='set NoData value for the input image.'
                    ' Will not affect output image, which has default nodata of (0,0,0)', type=int)
parser.add_argument('-m', '--mask', action='store_true', help='consider Unusable Data Mask (udm) image. '
                    'There is no need to set nodata value if UDM is used. '
                    'UDM file must have same name as the image file, with _udm.tif at the end, '
                    'and be located in the same directory.' )
args = parser.parse_args()

infile = args.input_image
out_path = args.out_path

nome = os.path.basename(infile)
in_path = os.path.split(infile)[0]
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
    print('Setting NoData value to %i'% args.nodata)
    [b.SetNoDataValue(args.nodata) for b in bandas]

if args.mask == True:
    udm_file = os.path.splitext(nome)[0]+'_udm.tif'
    inMask = gdal.Open(os.path.join(in_path, udm_file))
    mask = inMask.GetRasterBand(1).ReadAsArray()
    inMask = None
    
    xsize = inIMG.RasterXSize
    ysize = inIMG.RasterYSize
    sample = 0.01
    pos = np.random.choice(np.arange(xsize*ysize), int(xsize*ysize*sample))
    
    sample_bands = [b.ReadAsArray().flatten()[pos] for b in bandas]
    sample_udm = imresize(mask, (ysize, xsize), interp='nearest').flatten()[pos]
    sample_bands_limpo = [[v for v,m in zip(b,sample_udm) if m == 0] for b in sample_bands]
    minMax = [[min(b), max(b)] for b in sample_bands_limpo]
    meanSD = [[np.mean(b), np.std(b)] for b in sample_bands_limpo]
else:
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
    b_saida = np.zeros((inIMG.RasterXSize, inIMG.RasterYSize), dtype=int)    
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
call(["gdalwarp", "-t_srs", "epsg:4326", "-dstnodata", "0 0 0", "-srcnodata", 
      "0 0 0", "-r", "cubic", nome_saida_tmp, nome_saida], shell=False)
os.remove(nome_saida_tmp)
