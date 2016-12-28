# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 11:59:07 2016

Programa para analisar o histograma de diversas imagens
Plotar o hist acumulado de várias imagens, a média, mediana etc

@author: m330625
"""

import glob
from osgeo import gdal
from osgeo import ogr
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

pasta = 'I:\parana\8bit*.tif'
articulacao = 'C:\\geodb\\articulacao\\RapidEye_Tiles\\RapidEye_Tiles_Brasil.shp'

imagens = glob.glob(pasta)

def cospeHist(imagem):
    """Cospe o histograma da imagem, para a banda específica
    banda assume valores de 1 a n... não começa no 0 (zero)"""
    arq = gdal.Open(imagem)
    hist_r = arq.GetRasterBand(1).GetHistogram()
    hist_g = arq.GetRasterBand(2).GetHistogram()
    hist_b = arq.GetRasterBand(3).GetHistogram()
    arq = None
    return hist_r, hist_g, hist_b
 
hist_rgb = [cospeHist(i) for i in imagens]
hist_r = [i[0] for i in hist_rgb]
hist_g = [i[1] for i in hist_rgb]
hist_b = [i[2] for i in hist_rgb]

cdf_r = np.array([np.cumsum(i)/float(sum(i)) for i in hist_r])
cdf_g = np.array([np.cumsum(i)/float(sum(i)) for i in hist_g])
cdf_b = np.array([np.cumsum(i)/float(sum(i)) for i in hist_b])

def geraGraficos():
    """ funçao para gerar os gráficos e analisar a bagaça"""
    plt.subplot(221)
    plt.plot(np.transpose(cdf_r), color='gray', ls='dashed')
    plt.plot(np.mean(cdf_r, axis=0), color='red')
    plt.plot(np.median(cdf_r, axis=0), color='blue')
    plt.title('CDF for red band with mean and median values')
    
    plt.subplot(222)
    plt.plot(np.transpose(cdf_g), color='gray', ls='dashed')
    plt.plot(np.mean(cdf_r, axis=0), color='red')
    plt.plot(np.median(cdf_r, axis=0), color='blue')
    plt.title('CDF for green band with mean and median values')
    
    plt.subplot(223)
    plt.plot(np.transpose(cdf_b), color='gray', ls='dashed')
    plt.plot(np.mean(cdf_r, axis=0), color='red')
    plt.plot(np.median(cdf_r, axis=0), color='blue')
    plt.title('CDF for blue band with mean and median values')

    return

# gerando função de transformação para cada banda
# usando valores medianos
# inv_cdf_cor relaciona percentual de ocorrência ao valor de 0 a 255
# depois aplica a função inversa na cdf de cada imagem para obter uma
# função que transforma os valores da imagem aos correspondentes na mediana

median_cdf_r = np.median(cdf_r, axis=0)
median_cdf_g = np.median(cdf_g, axis=0)
median_cdf_b = np.median(cdf_b, axis=0)
inv_cdf_r = interp1d(median_cdf_r, range(len(median_cdf_r)), bounds_error=0)
inv_cdf_g = interp1d(median_cdf_g, range(len(median_cdf_g)), bounds_error=0)
inv_cdf_b = interp1d(median_cdf_b, range(len(median_cdf_b)), bounds_error=0)

def executaBalanco():
    for i in range(len(imagens)):
        arq = gdal.Open(imagens[i])
        saida = "I:\\parana_balanco\\" + str(i) + '.tif'
        transf_r = inv_cdf_r(cdf_r[i])
        transf_g = inv_cdf_g(cdf_r[i])
        transf_b = inv_cdf_b(cdf_r[i])
        np.insert(transf_r, 0, 0)
        np.insert(transf_g, 0, 0)
        np.insert(transf_b, 0, 0)
        transf_func_r = lambda x:transf_r[x]
        transf_func_g = lambda x:transf_g[x]
        transf_func_b = lambda x:transf_b[x]
        file_type = 'GTiff'    
        driver = gdal.GetDriverByName(file_type)
        outfile = driver.CreateCopy(saida, arq, 0, ['COMPRESS=LZW'])
        corr_r = transf_func_r(arq.GetRasterBand(1).ReadAsArray())
        corr_g = transf_func_g(arq.GetRasterBand(2).ReadAsArray())
        corr_b = transf_func_b(arq.GetRasterBand(3).ReadAsArray())
        arq = None
        outfile.GetRasterBand(1).WriteArray(corr_r)
        outfile.GetRasterBand(2).WriteArray(corr_g)
        outfile.GetRasterBand(3).WriteArray(corr_b)
        
        outfile = None
    return
    
# esse procedimento não deu muito certo. Não melhorou em relação ao anterior
# imagens apresentam muitas diferenças entre datas.
# olhar de perto 4 cenas que apresentam distinção, para ver histograma melhor
cenas_str = ['2227621', '2227622', '2227521', '2227522']
cenas = []
for i in cenas_str:
    cenas.append([j for j in enumerate(imagens) if i in j[1]])


def dataCenas(imagens, articulacao, saida):
    """Extrai a data das cenas e adiciona no shape de articulacao"""
    entrada = ogr.Open(articulacao)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    outfile = driver.CopyDataSource(entrada, saida)
    entrada = None
    layer = outfile.GetLayer()
    layer.CreateField(ogr.FieldDefn('Data', ogr.OFTDate))
    for i in imagens:
        data_i = i[41:51].split('-')
        cena = i[33:40]
        layer.SetAttributeFilter('TILE_ID = %i' % int(cena))
        for feature in layer:
            feature.SetField('Data', int(data_i[0]), int(data_i[1]), int(data_i[2]), 0, 0, 0, 0)
            layer.SetFeature(feature)
    outfile= None
    return

dataCenas(imagens, articulacao, 'I:\\articulacao_rapideye_2014.shp')
    
    
# olhando a data das cenas e a imagem com o balanço feito pelo 2SD
# aparentemente as diferenças não são só causadas pela data
# o porcentual de nuvens também pode atrapalhar a estimativa dos valores de SD
# o que bagunça o ajuste de cores
# devo implementar uma função para ignorar pixels com valores muito elevados (nuves) ou baixos (bordas)
# no cálculo do SD
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    