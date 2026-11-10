# -*- coding: utf-8 -*-
"""
Punzonado - lectura, limpieza y armado de matrices
"""

#%% Loading modules / Cargando modulos

'pip install ezdxf'

import pandas as pd
import numpy as np


#%% Cargando archivos

# Coordenadas
Coord = "coordenadas.xlsx"

# Conectividad de barras
Conec = "geometria.xlsx"

# Secciones
Sec = "predimensionado.xlsx"

# Esfuerzos / Fuerzas internas
Esf = "Fuerzas_internas.xlsx"

# Resistencia a la compresion del hormigon
HA=[25]
yc=1.5

# Resistencia del acero de refuerzo
Fy=500                                                                         # MPa
ys=1.15

# Dimension de columna minima (cm)
Colmin=30

# Multiplos (cm)
mult=5


#%% Funcion para leer datos de Excel

def leer(nombre_archivo):

    # Leer archivo Excel como texto
    datos_excel = pd.read_excel(nombre_archivo, sheet_name=0, dtype=str)
    # Eliminar columnas completamente vacias
    datos_excel = datos_excel.dropna(axis=1, how="all")
    # Cantidad de filas y columnas
    numero_filas = len(datos_excel)
    numero_columnas = len(datos_excel.columns)
    # Crear matriz vacia
    matriz = np.empty((numero_filas, numero_columnas), dtype=object)
    # Recorrer columnas
    for j in range(numero_columnas):
        # Recorrer filas
        for i in range(numero_filas):
            valor = datos_excel.iloc[i, j]
            # Celda vacia
            if pd.isna(valor):
                matriz[i, j] = None
            else:
                valor = str(valor).strip()
                # Intentar convertir a numero
                try:
                    valor = valor.replace(",", ".")
                    matriz[i, j] = float(valor)
                except ValueError:
                    # Si no es numero, conservar como texto
                    matriz[i, j] = valor
    return matriz


#%% Cargando coordenadas

coordenadas = leer(Coord)

# # Limpiando nodos

# i = 0
# while i < len(coordenadas[:,0]):
#     if coordenadas[i,4] != "xyzxyz":
#         coordenadas = np.delete(coordenadas, i, axis=0)
#     else:
#         i = i + 1

print("\nCOORDENADAS")
print("Dimensiones:", coordenadas.shape)


#%% Cargando conectividad

conectividad = leer(Conec)

print("\nCONECTIVIDAD")
print("Dimensiones:", conectividad.shape)

# Eliminando barras sin nombre

n_barras_inicial = len(conectividad)

conectividad = conectividad[np.array([nombre is not None and str(nombre).strip() != ""for nombre in conectividad[:,1]])]

print("\nLIMPIEZA DE BARRAS SIN NOMBRE")
print("Barras eliminadas:", n_barras_inicial - len(conectividad))
print("Barras restantes:", len(conectividad))


#%% Cargando secciones

secciones = leer(Sec)

print("\nSECCIONES")
print("Dimensiones:", secciones.shape)


#%% Cargando esfuerzos / fuerzas internas

esfuerzos = leer(Esf)

print("\nESFUERZOS")
print("Dimensiones:", esfuerzos.shape)

#%% Limpiando nodos sueltos

# Obtener todos los nodos que aparecen en conectividad
nodos_conectividad = np.concatenate((conectividad[:,2],conectividad[:,3]))

# Eliminar repetidos
nodos_conectividad = np.unique(nodos_conectividad)

# Conservar solo los nodos de coordenadas que aparecen en conectividad
coordenadas = coordenadas[np.isin(coordenadas[:,0], nodos_conectividad)]

#%% Corrigiendo valores None en numero y nombre de barra de esfuerzos

# Se supone que cada barra aparece en varias filas consecutivas.
# La primera fila del bloque tiene el numero de barra y las siguientes pueden tener None.

barra_actual = None
nombre_actual = None

for i in range(len(esfuerzos[:, 0])):
    if esfuerzos[i, 0] is not None:
        barra_actual = esfuerzos[i, 0]
    else:
        esfuerzos[i, 0] = barra_actual
    if esfuerzos[i, 1] is not None:
        nombre_actual = esfuerzos[i, 1]
    else:
        esfuerzos[i, 1] = nombre_actual


#%% Limpiando matrices

# La matriz de secciones es el modelo principal.
# Solo se conservaran barras que aparezcan simultaneamente en:
#   1. secciones
#   2. conectividad
#   3. esfuerzos

barras_secciones = secciones[:, 0]
barras_conectividad = conectividad[:, 0]
barras_esfuerzos = esfuerzos[:, 0]


# Limpiar conectividad
i = 0
while i < len(conectividad[:, 0]):
    barra = conectividad[i, 0]
    if barra not in barras_secciones or barra not in barras_esfuerzos:
        conectividad = np.delete(conectividad, i, axis=0)
    else:
        i = i + 1

# Limpiar esfuerzos
i = 0
while i < len(esfuerzos[:, 0]):
    barra = esfuerzos[i, 0]
    if barra not in barras_secciones or barra not in conectividad[:, 0]:
        esfuerzos = np.delete(esfuerzos, i, axis=0)
    else:
        i = i + 1


# Limpiar secciones para que coincidan con las barras finales
i = 0
while i < len(secciones[:, 0]):
    barra = secciones[i, 0]
    if barra not in conectividad[:, 0] or barra not in esfuerzos[:, 0]:
        secciones = np.delete(secciones, i, axis=0)
    else:
        i = i + 1


# Actualizar cantidades despues de limpiar
nbarras_con = len(conectividad[:, 0])
nbarras_sec = len(secciones[:, 0])
nbarras_esf = len(esfuerzos[:, 0])

print("\nDESPUES DE LIMPIAR")
print("Barras en conectividad:", nbarras_con)
print("Barras en secciones:", nbarras_sec)
print("Filas en esfuerzos:", nbarras_esf)
print("Barras diferentes en esfuerzos:", len(np.unique(esfuerzos[:, 0])))


#%% Seccion de barras

# 12 columnas:
# 0-6  -> datos de conectividad
# 7-8  -> dimensiones de seccion
# 9-10 -> axil en nodo i y nodo j
# 11+   -> disponible para calculos posteriores

Datos = np.empty((nbarras_con, 26), dtype=object)

# Inicializar todo en None de forma explicita
Datos[:, :] = None

# Copiar conectividad
for j in range(7):
    Datos[:, j] = conectividad[:, j]

# Agregar dimensiones de seccion
for i in range(nbarras_con):
    barra = Datos[i, 0]
    for j in range(nbarras_sec):
        if barra == secciones[j, 0]:
            Datos[i, 7] = secciones[j, 4] / 10
            Datos[i, 8] = secciones[j, 5] / 10
            Datos[i, 9] = secciones[j, 7]    # angulo de rotacion en planta de la seccion
            break

#%% Axil de cada nodo

nodo_i = []
nodo_j = []
Axil_nodoi = []
Axil_nodoj = []
My_nodoi = []
My_nodoj = []
Mz_nodoi = []
Mz_nodoj = []

for i in range(nbarras_con):
    barra = Datos[i, 0]
    nodoi = Datos[i, 2]
    nodoj = Datos[i, 3]

    nodo_i.append(nodoi)
    nodo_j.append(nodoj)

    # Buscar todas las filas que pertenecen a esta barra en esfuerzos
    filas_barra = []

    for j in range(nbarras_esf):
        if esfuerzos[j, 0] == barra:
            filas_barra.append(j)

    # Cada barra debe tener 6 filas de resultados segun TRICALC al tener subdivision de barras en 3 partes
    if len(filas_barra) >= 6:

        # Para axiles
        # En el archivo de esfuerzos:
        # posicion local 3 -> axil del nodo i
        # posicion local 5 -> axil del nodo j
        fila_i = filas_barra[3]
        fila_j = filas_barra[5]
        Datos[i, 10] = esfuerzos[fila_i, 10]
        Datos[i, 11] = esfuerzos[fila_j, 10]
        Axil_nodoi.append(esfuerzos[fila_i, 10])
        Axil_nodoj.append(esfuerzos[fila_j, 10])
        
        # Para My
        fila_i = filas_barra[0]
        fila_j = filas_barra[3]
        if abs(esfuerzos[fila_i, 8])>abs(esfuerzos[fila_j, 8]):
            My=esfuerzos[fila_i, 8]
        if abs(esfuerzos[fila_i, 8])<abs(esfuerzos[fila_j, 8]):
            My=esfuerzos[fila_j, 8]
        My_nodoi.append(My)
        Datos[i, 12] = My
        
        fila_i = filas_barra[2]
        fila_j = filas_barra[5]
        if abs(esfuerzos[fila_i, 8])>abs(esfuerzos[fila_j, 8]):
            My=esfuerzos[fila_i, 8]
        if abs(esfuerzos[fila_i, 8])<abs(esfuerzos[fila_j, 8]):
            My=esfuerzos[fila_j, 8]
        My_nodoj.append(My)
        Datos[i, 13] = My
        
        # Para Mz
        fila_i = filas_barra[0]
        fila_j = filas_barra[3]
        if abs(esfuerzos[fila_i, 9])>abs(esfuerzos[fila_j, 9]):
            Mz=esfuerzos[fila_i, 9]
        if abs(esfuerzos[fila_i, 9])<abs(esfuerzos[fila_j, 9]):
            Mz=esfuerzos[fila_j, 9]
        Mz_nodoi.append(Mz)
        Datos[i, 14] = Mz
        
        fila_i = filas_barra[2]
        fila_j = filas_barra[5]
        if abs(esfuerzos[fila_i, 9])>abs(esfuerzos[fila_j, 9]):
            Mz=esfuerzos[fila_i, 9]
        if abs(esfuerzos[fila_i, 9])<abs(esfuerzos[fila_j, 9]):
            Mz=esfuerzos[fila_j, 9]
        Mz_nodoj.append(Mz)
        Datos[i, 15] = Mz

    else:
        print("BARRA CON MENOS DE 6 FILAS DE ESFUERZOS ->","fila Datos =", i,"barra =", barra,"filas encontradas =", len(filas_barra))


#%% Verificacion de axiles faltantes

problemas = 0

for i in range(nbarras_con):
    if Datos[i, 9] is None or Datos[i, 10] is None:
        problemas = problemas + 1
        print(
            "AXIL NO ENCONTRADO ->",
            "fila Datos =", i,
            "barra =", Datos[i, 0],
            "nodo i =", Datos[i, 2],
            "nodo j =", Datos[i, 3],
            "axil i =", Datos[i, 9],
            "axil j =", Datos[i, 10])

if problemas == 0:
    print("\nTodos los axiles fueron encontrados correctamente.")
else:
    print("\nCantidad de barras con axiles faltantes:", problemas)


#%% Listas finales de axiles

# Se extraen directamente desde Datos para garantizar que tengan
# exactamente la misma cantidad de filas que la matriz Datos.

Axil_nodoi = Datos[:, 10]
Axil_nodoj = Datos[:, 11]


#%% Calculando axil por nodo
# node=[]
# axil=[]
# mom_y=[]
# mom_z=[]

# print("\nCalculando axiles y momentos por nodo.")
# n_nodos=len(coordenadas[:,0])
# for i in range(n_nodos):
#     print("\nNodo "+str(i)+" \nde "+str(n_nodos))
#     ax=0                                                                       #acumulador de axiles en caso de que un nodo lo compartan mas de una barra
#     my=0
#     mz=0
#     s1=0 
#     s2=0
#     s3=0
#     for j in range(len(Datos[:,0])):
#         for k in range(len(Datos[:,0])):
#             if coordenadas[i,0]==Datos[j,2] and coordenadas[i,0]==Datos[k,3]:  # Encuentra el mismo nodo en inicial y final    
#                 ax=ax+(Datos[k,11]-Datos[j,10])
#                 my=my+(Datos[k,13]-Datos[j,12])
#                 mz=mz+(Datos[k,15]-Datos[j,14])
#                 s1=1
#                 break
#     if s1==0:
#         for j in range(len(Datos[:,0])):
#             if coordenadas[i,0]==Datos[j,2]:                                   # Encuenta el nodo solo en inicial
#                 s2=1
#                 ax=Datos[j,10]
#                 my=Datos[j,12]
#                 mz=Datos[j,14]
#                 break
    
#         for k in range(len(Datos[:,0])):
#             if coordenadas[i,0]==Datos[k,3]:                                   # Encuenta el nodo solo en final
#                 s3=1
#                 ax=Datos[k,11]
#                 my=Datos[k,13]
#                 mz=Datos[k,15]
#                 break
    
#     if s1==1:
#         node.append(coordenadas[i,0])
#         axil.append(ax)
#         mom_y.append(my)
#         mom_z.append(mz)
    
#     if s2==1:
#         node.append(coordenadas[i,0])
#         axil.append(ax)
#         mom_y.append(my)
#         mom_z.append(mz)
    
#     if s3==1:
#         node.append(coordenadas[i,0])
#         axil.append(ax)
#         mom_y.append(my)
#         mom_z.append(mz)

# # Uniendo ambos vectores
# # Axil_nodos = np.column_stack((node, axil))
# FI_nodos=np.column_stack((node, axil,mom_y,mom_z))

# ChatGPT version (muy rapida)
node = []
axil = []
mom_y = []
mom_z = []

print("\nCalculando axiles y momentos por nodo.")

# Diccionario:
# nodo inicial -> fila de Datos
barra_nodo_i = {}

# nodo final -> fila de Datos
barra_nodo_j = {}

for i in range(len(Datos[:,0])):
    barra_nodo_i[Datos[i,2]] = i
    barra_nodo_j[Datos[i,3]] = i

n_nodos = len(coordenadas[:,0])

for i in range(n_nodos):
    nodo = coordenadas[i,0]
    # Buscar directamente, sin recorrer todas las barras
    j = barra_nodo_i.get(nodo)
    k = barra_nodo_j.get(nodo)

    # Nodo intermedio:
    # final de barra inferior + inicial de barra superior
    if j is not None and k is not None:
        ax = Datos[k,11] - Datos[j,10]
        my = Datos[k,13] - Datos[j,12]
        mz = Datos[k,15] - Datos[j,14]

    # Nodo inferior:
    # solamente inicial
    elif j is not None:
        ax = Datos[j,10]
        my = Datos[j,12]
        mz = Datos[j,14]

    # Nodo superior:
    # solamente final
    elif k is not None:
        ax = Datos[k,11]
        my = Datos[k,13]
        mz = Datos[k,15]

    else:
        continue
    node.append(nodo)
    axil.append(ax)
    mom_y.append(my)
    mom_z.append(mz)


FI_nodos = np.column_stack((node,axil,mom_y,mom_z))

#%% Ordenamiento de nodos, cotas, axiles, momentos

nodos = []
cotas = []
axiles = []
moment_y= []
moment_z= []

for i in range(len(FI_nodos[:,0])):
    nodo = FI_nodos[i,0]
    axil_nodo = FI_nodos[i,1]
    my_nodo = FI_nodos[i,2]
    mz_nodo = FI_nodos[i,3]
    for j in range(len(coordenadas[:,0])):
        if nodo == coordenadas[j,0]:
            nodos.append(nodo)
            cotas.append(coordenadas[j,2])
            axiles.append(axil_nodo)
            moment_y.append(my_nodo)
            moment_z.append(mz_nodo)
            break

# Matriz completa
# columna 0 = nodo
# columna 1 = cota
# columna 2 = axil
Nodos_cotas_axil = np.column_stack((nodos,cotas,axiles,moment_y,moment_z))

# Ordenar de menor a mayor cota
orden = np.argsort(Nodos_cotas_axil[:,1].astype(float))
Nodos_cotas_axil = Nodos_cotas_axil[orden]

# Extraer nuevamente las matrices si las queremos separadas
# Nodos_cotas = Nodos_cotas_axil[:,0:2]
# Axil_nodos = Nodos_cotas_axil[:,[0,2]]

#%% Dimension minima de pilar
print("\nPredimensionando pilares.")
f=10**6/9.81/100**2/yc # Conversion a kg/cm2 
for i in range(len(Datos[:,0])):
    k=16
    print("\nPilar "+str(i)+" \nde "+str(len(Datos[:,0])))
    for j in range(len(HA)):
        Ax_max=max(abs(Datos[i,10]),abs(Datos[i,11]))
        if (Datos[i,10])<0:
            Ax_max=-Ax_max
        if (Datos[i,11])<0:
            Ax_max=-Ax_max
            
        Ar_colocada=Datos[i,7]*Datos[i,8]
        Ar_requerida=round(abs(Ax_max*1000/(HA[j]*f)),2)
        Datos[i,k]=Ar_requerida
        Datos[i,k+1]=Ar_colocada
        if Ar_requerida >= Ar_colocada:
            Datos[i,k+2]="Aumentar"                                                  #Bien
        else:
            Datos[i,k+2]="Bien"                                              #Verificar dimensiones del pilar
        

#%% Ordenando matriz Datos por cota del nodo final
k=k+3
print("\nOrdenando nodos por cota.")
cotas_barras = []
for i in range(len(Datos[:,0])):
    nodo_final = Datos[i,3]
    for j in range(len(coordenadas[:,0])):
        if nodo_final == coordenadas[j,0]:
            cota = coordenadas[j,2]
            cotas_barras.append(cota)
            break

# Convertir a vector NumPy
cotas_barras = np.array(cotas_barras, dtype=float)

# Ordenar de menor a mayor cota
orden_Datos = np.argsort(cotas_barras)

Datos = Datos[orden_Datos]
cotas_barras = cotas_barras[orden_Datos]

# Guardar cota del nodo final en la ultima columna de Datos
Datos[:,k] = cotas_barras

#%% Agregando axil resultante del nodo final a Datos

# Buscar el axil correspondiente al nodo final de cada barra
for i in range(len(Datos[:,0])):
    nodo_final = Datos[i,3]
    for j in range(len(FI_nodos[:,0])):
        if nodo_final == FI_nodos[j,0]:
            Datos[i,k+1] = round(float(FI_nodos[j,1]),2)                       # Axiles
            Datos[i,k+2] = round(float(FI_nodos[j,2]),2)                       # Mz
            Datos[i,k+3] = round(float(FI_nodos[j,3]),2)                       # My
            break

#%% Espesor de losa requerido y As min
k=k+4
f=10**6/9.81/100**2                                                            # Conversion a kg/cm2

for j in range(len(HA)):
    for i in range(len(Datos[:,0])):
        Mymax=max(abs(Datos[i,12]),abs(Datos[i,13]))
        Mzmax=max(abs(Datos[i,14]),abs(Datos[i,15]))
        dreq=(max(Mymax,Mzmax)*1000*100/(0.85*HA[j]*f*100*0.19))**0.5          # 100 es para 1 m de ancho, 1000*100 transformacion de T.m a kg.cm
        Datos[i,k]=dreq
        # As min Y
        Datos[i,k+1]=(dreq-(dreq**2-2*Mymax*100000/(0.85*0.9*HA[j]*f*100))**0.5)/(Fy*f/(0.85*HA[j]*f*100))
        # As min Z
        Datos[i,k+2]=(dreq-(dreq**2-2*Mzmax*100000/(0.85*0.9*HA[j]*f*100))**0.5)/(Fy*f/(0.85*HA[j]*f*100))


#%% Guardando en Excel
# Borrando columna 6
Datos=np.delete(Datos, 6, axis=1)
print("\nGenerando archivo en Excel.")
titulos = ["Barra",
    "Nombre",
    "Nodo inicial",
    "Nodo final",
    "Longitud (cm)",
    "Crecimiento",
    "B (cm)",
    "H (cm)",
    "Rotación (º)",
    "Axil nodo inicial",
    "Axil nodo final",
    "My nodo inicial",
    "My nodo final",
    "Mz nodo inicial",
    "Mz nodo final",
    "Area mínima por compresion cm2",
    "Area colocada cm2",
    "Estado",
    "Cota nodo final (cm)",
    "Corte por punzonamiento (T)",
    "My resultante (T.m)",
    "Mz resultante (T.m)",
    "dmin (cm)",
    "AsY req (cm2)",
    "AsZ req (cm2)"]


# Convertir Datos a DataFrame
Datos_excel = pd.DataFrame(Datos,columns=titulos)

# Guardar archivo Excel
Datos_excel.to_excel("Resultados_Punzonado.xlsx",index=False)

print("\nArchivo Resultados_Punzonado.xlsx creado correctamente.")

################# Agregando escala de colores y programando celdas

from openpyxl import load_workbook
from openpyxl.styles import PatternFill

archivo_excel = "Resultados_Punzonado.xlsx"

wb = load_workbook(archivo_excel)
ws = wb.active

# El Excel termina en la columna "AsZ req (cm2)".
# No se agregan celdas ni formulas programadas a la derecha.


# Gama de colores
colores = [
    "D9EAF7",  # azul claro
    "E2F0D9",  # verde claro
    "FFF2CC",  # amarillo claro
    "FCE4D6",  # naranja claro
    "E4DFEC",  # violeta claro
    "DDEBF7",  # celeste
    "F4CCCC",  # rojo claro
    "D9D2E9",  # lila
    "D0E0E3",  # gris azulado
    "EAD1DC",  # rosa
]


# Diccionario para relacionar cada pilar con un color
colores_pilares = {}

indice_color = 0


# Recorrer filas del Excel
# Fila 1 = encabezados
for fila in range(2, ws.max_row + 1):
    # Columna 2 = Nombre
    nombre_pilar = ws.cell(row=fila,column=2).value


    # Si el pilar todavía no tiene color, asignarle uno
    if nombre_pilar not in colores_pilares:
        colores_pilares[nombre_pilar] = colores[indice_color % len(colores)]
        indice_color = indice_color + 1

    color = colores_pilares[nombre_pilar]

    relleno = PatternFill(fill_type="solid",fgColor=color)

    # Pintar toda la fila
    for columna in range(1, ws.max_column + 1):
        ws.cell(row=fila,column=columna).fill = relleno


wb.save(archivo_excel)



#%% Exportacion AutoCAD: pilares 3D + plantas 2D
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment
from pathlib import Path

# En la matriz Datos ya exportada a Excel:
# nombre=1, nodo inicial=2, nodo final=3,
# B(cm)=6, H(cm)=7, cota final=17, cortante por punzonamiento=18.
# Coordenadas: columna 0=nodo, 1=X, 2=Z(cota), 3=Y.
INDICE_X = 1
INDICE_Z = 2
INDICE_Y = 3
ALTURA_TEXTO = 12.0  # cm en espacio modelo; ajustar a escala de plano
DISTANCIA_ETIQUETA = 12.0
ARCHIVO_SALIDA = Path.cwd() / 'Pilares_2D_3D.dxf'


def numero(valor):
    try:
        n = float(valor)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def etiqueta_num(valor, dec=2):
    n = numero(valor)
    return f'{n:.{dec}f}' if n is not None else 'S/D'


# Crear archivo nuevo; no modifica ningun DWG/DXF existente
cad = ezdxf.new('R2013', setup=True)
cad.header['$INSUNITS'] = 5  # 5 = centimetros
msp = cad.modelspace()
cad.layers.new('PILARES_3D', dxfattribs={'color': 8})

# Mapa de coordenadas por identificador de nodo
nodos_xyz = {}

for registro in coordenadas:
    if len(registro) <= max(INDICE_X, INDICE_Y, INDICE_Z):
        continue

    x = numero(registro[INDICE_X])
    y = numero(registro[INDICE_Y])
    z = numero(registro[INDICE_Z])

    if None not in (x, y, z):
        nodos_xyz[str(registro[0]).strip()] = (x, -y, z)

plantas = set()
correctos = 0
omitidos = []

for fila in Datos:
    nombre = str(fila[1]).strip() if fila[1] is not None else ''
    if not nombre or nombre.lower() in ('none', 'nan'):
        continue

    pi = nodos_xyz.get(str(fila[2]).strip())
    pj = nodos_xyz.get(str(fila[3]).strip())
    b = numero(fila[6])
    h = numero(fila[7])
    # Tras eliminar la columna 6 de Datos, el cortante por punzonamiento queda en la columna 18.
    cortante = numero(fila[19])
    if pi is None or pj is None or b is None or h is None or b <= 0 or h <= 0:
        omitidos.append((nombre, 'Faltan nodos o seccion B/H'))
        continue

    # Planta identificada por la cota REAL del nodo final (en cm)
    cota = pj[2]
    cota_id = f'{cota:.2f}'.replace('-', 'M').replace('.', '_')
    capa_2d = f'P_{cota_id}_PILARES'
    capa_datos = f'P_{cota_id}_DATOS'
    if capa_2d not in cad.layers:
        cad.layers.new(capa_2d, dxfattribs={'color': 7})
        cad.layers.new(capa_datos, dxfattribs={'color': 3})
    plantas.add(cota)

    # PLANTA 2D: rectangulo centrado en nodo final, en z=0.
    # Los dibujos de distintas plantas coinciden en XY y se distinguen por capas.
    x, y, _ = pj
    puntos2d = [(x-b/2,y-h/2),(x+b/2,y-h/2),
                (x+b/2,y+h/2),(x-b/2,y+h/2)]
    msp.add_lwpolyline(puntos2d, close=True, dxfattribs={'layer': capa_2d})

    # Texto DXF: solo nombre del pilar, seccion y cortante por punzonamiento.
    lineas = [nombre, f'{b:g} x {h:g} cm',
              f'Vpunz = {etiqueta_num(cortante)} T']
    tx = x + b/2 + DISTANCIA_ETIQUETA
    ty = y + h/2
    for j, contenido in enumerate(lineas):
        msp.add_text(contenido, dxfattribs={
            'layer': capa_datos, 'height': ALTURA_TEXTO,
            'insert': (tx, ty - j*ALTURA_TEXTO*1.5, 0)
        })

    # 3D: prisma por seis caras; sin asumir verticalidad perfecta.
    # Seccion alineada a ejes globales XY (rotaciones locales no disponibles).
    xi, yi, zi = pi
    xj, yj, zj = pj
    base = [(xi-b/2,yi-h/2,zi), (xi+b/2,yi-h/2,zi),
            (xi+b/2,yi+h/2,zi), (xi-b/2,yi+h/2,zi)]
    tapa = [(xj-b/2,yj-h/2,zj), (xj+b/2,yj-h/2,zj),
            (xj+b/2,yj+h/2,zj), (xj-b/2,yj+h/2,zj)]
    msp.add_3dface(base, dxfattribs={'layer': 'PILARES_3D'})
    msp.add_3dface(tapa, dxfattribs={'layer': 'PILARES_3D'})
    for j in range(4):
        k = (j+1) % 4
        msp.add_3dface([base[j], base[k], tapa[k], tapa[j]],
                       dxfattribs={'layer': 'PILARES_3D'})
    correctos += 1

cad.saveas(ARCHIVO_SALIDA)
print('\nDXF generado:', ARCHIVO_SALIDA)
print('Pilares dibujados:', correctos)
print('Plantas:', len(plantas), sorted(plantas))
print('Pilares omitidos:', len(omitidos))
for nombre, motivo in omitidos[:20]:
    print(' -', nombre, ':', motivo)



