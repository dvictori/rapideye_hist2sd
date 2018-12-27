# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 11:25:59 2017

Programa para gerar shapefile da articulacao RapidEye
com a data das imagens

Não estou me preocupando com cenas que tenham mais de uma data.
Não sei o que acontece nesses casos :)

ATENCAO: existem pastas e posicoes fixas no código.
É preciso verificar/arrumar antes de rodar

@author: m330625
"""

import glob
from osgeo import ogr

pasta = 'Z:\\filtro_radiometrico_2014_16bits\\*.tif'
articulacao = 'C:\\geodb\\articulacao\\RapidEye_Tiles\\RapidEye_Tiles_Brasil.shp'

imagens = glob.glob(pasta)

def dataCenas(imagens, articulacao, saida):
    """Extrai a data das cenas a partir do nome do arquito
    e adiciona no shape de articulacao
    ATENCAO: posicao da data no nome do arquivo está fixa!!!"""
    entrada = ogr.Open(articulacao)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    outfile = driver.CopyDataSource(entrada, saida)
    entrada = None
    layer = outfile.GetLayer()
    layer.CreateField(ogr.FieldDefn('Data', ogr.OFTDate))
    ini_date = 48 # posicao inicial da data no nome do arquivo
    ini_cena = 40
    for i in imagens:
        # atenção. Posicao da data no nome do arquivo está fixa
        data_i = i[ini_date:ini_date+10].split('-') 
        cena = i[ini_cena:ini_cena+7]
        layer.SetAttributeFilter('TILE_ID = %i' % int(cena))
        for feature in layer:
            feature.SetField('Data', int(data_i[0]), int(data_i[1]), int(data_i[2]), 0, 0, 0, 0)
            layer.SetFeature(feature)
    outfile= None
    return

dataCenas(imagens, articulacao, 'I:\\articulacao_rapideye_2014.shp')