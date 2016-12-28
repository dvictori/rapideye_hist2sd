# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 11:29:07 2016

Avaliar diferenças no ajuste de histograma, considerando
valor de NoData e ignorando valor de nuvens

@author: m330625
"""

from osgeo import gdal
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np
from scipy.misc import imresize

pasta = 'I:\\SUL\\22Sst\\2226804_2012-11-11T143404_RE3_3A-NAC_14463122_171802\\'
basename = '2226804_2012-11-11T143404_RE3_3A-NAC_14463122_171802'
arquivo = basename+'.tif'
metadata = basename+'_metadata.xml'
cloud = basename+'_udm.tif'

inIMG = gdal.Open(pasta+arquivo)

bandas = [inIMG.GetRasterBand(b+1) for b in range(3)]

# if args.nodata is not None:
#   [b.SetNoDataValue(args.nodata) for b in bandas]

band_stats = [b.ComputeStatistics(False) for b in bandas]
minMax = [i[:2] for i in band_stats]
meanSD = [i[2:] for i in band_stats]

# histograma é calculado sobre uma amostra
# por isso a comparação com o que sai do np.histogram deve ser com valores normalizados
x = np.linspace(0, 65535, num=256)
hist_orig = [np.array(b.GetHistogram(min=0, max=65535)) for b in bandas]
plt.plot(x,hist_orig[0]/sum(hist_orig[0]), color='blue', label = 'Original')
plt.plot(x,hist_orig[1]/sum(hist_orig[1]), color='green')
plt.plot(x,hist_orig[2]/sum(hist_orig[2]), color='red')

### aplicar strech com 2SD
bandVals = [[0, max(minMax[b][0], 1, meanSD[b][0] - 2* meanSD[b][1]),
             min(minMax[b][1], meanSD[b][0] + 2*meanSD[b][1]), 65535] for b in range(3)]
 

# reservar zero as nodata
transfVals = [0,1, 65534, 65535]
transfFunc = [interp1d(bandVals[b], transfVals) for b in range(3)]

hist_2sd = []
for b in range(3):
    teste = transfFunc[b](bandas[b].ReadAsArray()).astype(int)
    teste_hist = np.histogram(teste, bins=256, range=(0, 65535))
    hist_2sd.append(teste_hist)
    teste = None
           
plt.plot(x, hist_2sd[0][0]/sum(hist_2sd[0][0]), color='blue', ls='dashed', label = '2SD')
plt.plot(x, hist_2sd[1][0]/sum(hist_2sd[0][0]), color='green', ls='dashed')
plt.plot(x, hist_2sd[2][0]/sum(hist_2sd[0][0]), color='red', ls='dashed')
plt.legend()

### hist original porém sem áreas com nuvens
# usa arquivo de máscara que vem junto com imagem
mask_file = gdal.Open(pasta+cloud)
mask = mask_file.GetRasterBand(1).ReadAsArray()
mask_file = None

hist_cloud = []
for b in range(3):
    teste = np.ma.array(bandas[b].ReadAsArray(), mask=imresize(mask, (5000, 5000), interp='nearest'))
    teste_hist = np.histogram(teste, bins=256, range=(0, 65535))
    hist_cloud.append(teste_hist)
    teste = None
    
# comparando original com original+mask
plt.plot(x,hist_orig[0]/sum(hist_orig[0]), color='blue', label = 'Original')
plt.plot(x,hist_orig[1]/sum(hist_orig[1]), color='green')
plt.plot(x,hist_orig[2]/sum(hist_orig[2]), color='red')
plt.plot(x, hist_cloud[0][0]/sum(hist_cloud[0][0]), color='blue', ls='dashed', label = 'orig_mask')
plt.plot(x, hist_cloud[1][0]/sum(hist_cloud[0][0]), color='green', ls='dashed')
plt.plot(x, hist_cloud[2][0]/sum(hist_cloud[0][0]), color='red', ls='dashed')
plt.legend()
# Diferença mínima!!!

### Agora aplicando stretch de 2SD no arquivo com máscara
### É preciso aplicar a máscara antes da etapa de calculo dos valores min, max, média e SD

minMax = []
meanSD = []
for b in bandas:
    teste = np.ma.array(b.ReadAsArray(), mask=imresize(mask, (5000, 5000), interp='nearest')).compressed()
    minMax.append([teste.min(), teste.max()])
    meanSD.append([teste.mean(), teste.std()])
    teste = None

bandVals = [[0, max(minMax[b][0], 1, meanSD[b][0] - 2* meanSD[b][1]),
             min(minMax[b][1], meanSD[b][0] + 2*meanSD[b][1]), 65535] for b in range(3)]

transfVals = [0,1, 65534, 65535]
transfFunc = [interp1d(bandVals[b], transfVals) for b in range(3)]

hist_cloud_2sd = []
for b in range(3):
    teste = transfFunc[b](bandas[b].ReadAsArray()).astype(int)
    teste_hist = np.histogram(teste, bins=256, range=(0, 65535))
    hist_cloud_2sd.append(teste_hist)
    teste = None

plt.plot(x, hist_2sd[0][0]/sum(hist_2sd[0][0]), color='blue', label = '2SD')
plt.plot(x, hist_2sd[1][0]/sum(hist_2sd[0][0]), color='green')
plt.plot(x, hist_2sd[2][0]/sum(hist_2sd[0][0]), color='red')
plt.plot(x, hist_cloud_2sd[0][0]/sum(hist_cloud_2sd[0][0]), color='black', ls='dashed', label = '2SD')
plt.plot(x, hist_cloud_2sd[1][0]/sum(hist_cloud_2sd[0][0]), color='black', ls='dashed')
plt.plot(x, hist_cloud_2sd[2][0]/sum(hist_cloud_2sd[0][0]), color='black', ls='dashed')