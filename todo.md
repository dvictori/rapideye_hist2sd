# TO DO

First version: 2/dez/2016

File containign things that should be done in the rapideye_hist2sd.py program

1. Reproject data without using gdal_warp
  * In windows, sometime gdal_warp will crash at the end of reprojection, blocking the conversion process. Maybee, if I reprocess without calling an external tool, it will not crash.
2. Count number of 0 values in file. If more then a threshold, consider it nodata, else, consider it data
  * This is a problem when considering 0 as nodata and processing scenes with very dark areas

  
### New program idea

Color balance between scenes. Maybee extract histogram for all images, calculate a medium histogram and do the transform
