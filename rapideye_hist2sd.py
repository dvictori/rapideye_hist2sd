#!/c/OSGEO4W64/bin/pythonw
# -*- coding: utf-8 -*-

## se usar env python, programa demora muito para iniciar no MSys.
## Fica mais rápido se apontar diretamente p/ o executável
## usando o executável python dá problema (python stoped working). O pythonw aparentemente funciona
#!/c/OSGEO4W64/bin/python
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
"""

from osgeo import gdal
from scipy.interpolate import interp1d
import sys, os
from subprocess import call
from numpy import zeros

if len(sys.argv) < 3:
    print "This programs applies a mean +-2SD histogram stretch to images and converts to 8bit"
    print "Usage: rapideye_hist2sd.py  <input_image> <output_dir>"
    print "Output image will have the prefix: 8bit_2sd_epsg4326_"
    sys.exit()

infile = sys.argv[1]
out_path = sys.argv[2]

nome = os.path.basename(infile)
nome_saida_tmp = os.path.join(out_path, "8bit_2sd_temp_"+nome)
nome_saida = os.path.join(out_path, "8bit_2sd_epsg4326_"+nome)

# test if output file alredy exists
# if so, stop program
if os.path.isfile(nome_saida):
    print "Output file %s alredy exists. DONE" % nome_saida
    sys.exit()

inIMG = gdal.Open(infile)

# getting stats for the first 3 bands
# Using ComputeBandStats insted of stats array has min, max, mean and sd values
print "Computing band statistics"
bandas = [inIMG.GetRasterBand(b+1) for b in range(3)]
minMax = [b.ComputeRasterMinMax() for b in bandas]
meanSD = [b.ComputeBandStats() for b in bandas]

# rescale image using mean+- 2* SD
# if mean-2*sd < band(min), use band(min)
# if mean+2*sd > band(max), use band(max)

bandVals = [[0, max(minMax[b][0], meanSD[b][0] - 2* meanSD[b][1]),
             min(minMax[b][1], meanSD[b][0] + 2*meanSD[b][1]), 65536] for b in range(3)]

# leaving zero as nodata
transfVals = [1,2, 254, 255]

transfFunc = [interp1d(bandVals[b], transfVals) for b in range(3)]

print "Saving temp output image"
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
print "Reprojecting image"
call(["gdalwarp", "-t_srs", "epsg:4326", "-dstnodata", "0", "-r", "cubic", nome_saida_tmp, nome_saida], shell=False)
os.remove(nome_saida_tmp)
