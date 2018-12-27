#!/c/OSGEO4W64/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat May 17 18:28:01 2014

Programa para fazer o balanço de cores entre duas imagens
Recebe duas imagens, sendo a primeira a referência
Retorna uma terceira imagem, após fazer o histogram match
Utiliza CDF

@author: Daniel
"""

from osgeo import gdal
import numpy as np
from scipy.interpolate import interp1d
import sys, argparse

def balanco(referencia, adjust, saida):
    '''Realiza o balanço de cores por CDF matching
    referencia: imagem referencia
    adjust: imagem para ser ajustada
    saida: imagem de saida
    nodata: valor de nodata. default = 0'''
    
    ref = gdal.Open(referencia)
    adj = gdal.Open(adjust)
    if ref.RasterCount != adj.RasterCount:
        print "Imagens com número de bandas diferentes"        
        sys.exit()
    #if (ref.RasterXSize != adj.RasterXSize) or (ref.RasterYSize != adj.RasterYSize):
    #    print "Imagens com tamanho diferente"
    #    sys.exit()
    
    # GDAL fornece histograma de cada uma das bandas
    # Não precisa fazer sample
    bandas = ref.RasterCount
    ref_hist = [ref.GetRasterBand(b+1).GetHistogram() for b in range(bandas)]
    ref_cdf = [np.cumsum(a) / float(sum(a)) for a in ref_hist]
    
    adj_hist = [adj.GetRasterBand(b+1).GetHistogram() for b in range(bandas)]
    adj_cdf = [np.cumsum(a) / float(sum(a)) for a in adj_hist]
    
    # Gera uma função inversa do CDF da imagem referência
    # Aplica os valores da CDF da imagem a ser ajustada na funcao inversa do CDF ref
    # gera função de transferência para passar falores da imagem adj p/ ref
    inv_cdf_func = [interp1d(b, range(len(b)), bounds_error=0) for b in ref_cdf]
    transf_b = [inv_cdf_func[b](adj_cdf[b]) for b in range(bandas)]
    # como transf é uma série de listas com o resultado da função ele não começa com o valor 0
    # então o 0 na imagem ajustada fica com valor com dados.
    # adicionando 0 no início da lista p/ ver se arruma
    transf = [np.insert(l, 0, 0) for l in transf_b]
    transf_func = [lambda x:transf[b][x] for b in range(bandas)]
    
    # escrevendo imagem ajustada    
    file_type = 'GTiff'    
    driver = gdal.GetDriverByName(file_type)
    outfile = driver.CreateCopy(saida, adj, 0, ['COMPRESS=LZW'])
    for b in range(bandas):
        banda_corr = transf_func[b](adj.GetRasterBand(b+1).ReadAsArray())
        outfile.GetRasterBand(b+1).WriteArray(banda_corr)
        
    #limpando
    ref = None
    adj = None
    outfile = None
    return

def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description='Faz o histogram matching entre imagem de referência e imagem a ser ajustada')
        parser.add_argument("referencia", help="Imagem para usar como referencia")
        parser.add_argument("ajuste", help='Imagem que será ajustada')
        parser.add_argument("saida", help='Nome da imagem de saida')
        args = parser.parse_args()
    
    balanco(args.referencia, args.ajuste, args.saida)

if __name__ == '__main__':
    main()
