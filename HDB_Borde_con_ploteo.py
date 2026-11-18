# PUNZONAMIENTO HALFEN HDB - PILAR DE BORDE - PRIMERA SOLUCION Y DISTRIBUCION
# Derivado de HDB_V4_aprovechamiento.py (interior), conservando su estructura.
# Version de desarrollo. Solo pilar de borde ENRASADO con borde recto, sin huecos.
# Una cara sobre borde libre, dos caras laterales y una cara frontal con losa.
# Lado X (cx) perpendicular al borde; lado Y (cy) paralelo al borde.
# El borde libre coincide con x = -cx/2. La losa se extiende hacia +X.
# Acero base, suplementos y busqueda: primer suplemento que cumple -> break.
# Reparte simetricamente las dos caras laterales, pero no obliga a igualdad
# con la cara frontal. Prueba 0, 1, 2,... diagonales por cada esquina interior.
# Las resistencias y geometria se comprueban con EOTA TR 060 + ETA-12/0454.
# Se conserva APROVECHAMIENTO (sistema, acero C, exterior y conjunto).
# Los coeficientes particulares del informe HDB deben justificarse en proyecto.
# NOTA: las distancias/longitudes comerciales y anclajes siguen pendientes.
# No es un comprobador de ejecucion ni reemplaza el proyecto estructural.

from math import pi, sqrt, ceil, floor, isfinite, cos, sin, hypot, atan2, degrees

#%% 1. ENTRADAS DEL PILAR Y LA LOSA
lado_pilar_x_cm = 60.0                                                         # Perpendicular al borde libre (b en HDB)
lado_pilar_y_cm = 60.0                                                         # Paralelo al borde libre (a en HDB)
fuerza_punzonamiento_kN = 250 # VEd, ANTES de beta
tipo_pilar = "borde"
espesor_losa_cm = 23.0
resistencia_hormigon_MPa = 25.0
resistencia_acero_losa_MPa = 500.0   # fyk de las barras de la losa
recubrimiento_superior_cm = 3.0
# Por ahora SOLO coincide la cara posterior del pilar con el borde libre.
# No extrapolar a un pilar retranqueado o a uno de esquina.
distancia_cara_pilar_borde_cm = 0.0
# Sin dato especifico de recubrimiento lateral se controla solo que las
# cabezas no invadan el exterior de la losa. Valor en cm o None.
recubrimiento_lateral_borde_cm = None

# Armado base. Diametros en mm; separaciones en cm.
phix = 8.0
sx = 15.0
phiy = 8.0
sy = 15.0

# ALTERNATIVAS: cada posicion se suma al armado base, NO a las alternativas anteriores.
# La posicion cero significa SIN suplemento. Cada pareja 0/0 equivale a acero nulo.
# PRIORIDAD: se prueban de izquierda a derecha, SIN ordenar por area o diametro.
# Si una cumple, las alternativas posteriores NO se calculan.
# Ejemplo: para probar primero un suplemento de 15 mm cada 15 cm,
# escribe 15 en el segundo puesto de las cuatro listas (si es igual en X e Y).
# V4: los cuatro suplementos de la casa (los de la pestaña): 1 de 12 cada 15, 1 de 16 cada 15, 2 de 16 cada 20
# y 2 de 20 cada 20. barras_suplementarias dice cuantas barras van juntas en cada posicion.
phix_suplementario = [0, 12, 16, 16, 20]
sx_suplementario = [0, 15, 15, 20, 20]
phiy_suplementario = [0, 12, 16, 16, 20]
sy_suplementario = [0, 15, 15, 20, 20]
barras_suplementarias = [0, 1, 1, 2, 2]

# El canto util se calcula para CADA alternativa. No se introduce manualmente.
# d = min(d_base, d_suplementacion): el del diametro MAYOR (criterio de la pestaña, Leyanis 16-nov).
# OJO: en V3 el codigo hacia max (el del diametro menor) aunque los comentarios dijeran min.
# Se considera el armado superior en dos direcciones y dos capas en contacto.
# Si una direccion NO tiene suplemento, se utiliza el diametro base en esa direccion.

# True SOLO para la hipotesis de suplemento efectivo tambien en el exterior.
# Se supone armado uniforme en las bandas eficaces y suficientemente anclado.
# Con False el exterior utiliza UNICAMENTE el armado base (prueba conservadora).
suplemento_hasta_exterior = True

# VISUALIZACION DE PLANTA: mismos controles que el HDB_V4 interior.
mostrar_grafico = True            # Abre el grafico Matplotlib al terminar.
guardar_grafico = False           # True: guarda imagen PNG.
nombre_archivo_grafico = "HDB_Borde_Distribucion.png"
numerar_brazos_grafico = True    # Numerar cada brazo junto a su extremo.

#%% 2. CONFIGURACION HDB QUE SE CONSERVA
# Subconjunto de diametros que usa la empresa, no catalogo completo del fabricante.
diametros_pernos_mm = [12, 16, 20]
# V4: None = se prueban los tres y se queda el de MENOS ACERO (como la pestaña); un numero lo fija.
diametro_perno_a_detallar_mm = None
maximo_brazos = 64           # Limite de BUSQUEDA, NO limite de la norma
# BUSQUEDA EN BORDE: 2 caras laterales de longitud cx, 1 frontal de
# longitud cy y 2 esquinas interiores. Se prueban cantidades independientes
# de brazos en laterales y frontal, sin imponer la geometria del interior.
# Se conservan las dos caras laterales simetricas entre si.
# CONTROL PROPIO DEL GENERADOR (no limite literal de TR 060): para no dejar
# sin cobertura los extremos de la U, media celda del primer carril lateral
# <= 0.5 * 1.7d. Puede desactivarse para estudiar otras familias.
control_extremos_generador = True

# 4: se conservan CUATRO pernos por brazo en TODAS las alternativas.
# None: se permite ajustar SOLO las filas D; tambien se buscan los brazos.
# V4: None por defecto, como Halfen (en su informe del 30x60 pone 5 con el armado base).
pernos_por_carril_fijos = None

# Posiciones teoricas ligadas al canto util de CADA alternativa:
# 0.50d; 1.125d; incremento posterior de 0.75d.
# Si cambia d, las distancias tambien cambian para conservar dos pernos en C.
# No equivale a seleccionar automaticamente la longitud comercial HALFEN.

#%% 3. PARAMETROS DEL METODO Y DEL INFORME DE COMPARACION
fyk_pernos = 500.0
factor_maximo_HDB = 1.96
gamma_c = 1.50
gamma_s = 1.15
alpha_cc = 1.00
beta = 1.40                         # Valor simplificado de borde en TR 060, sujeto a sus condiciones

# Estos informes de borde (PruebaHDB.pdf y PruebaHDB2.pdf) usan 0.12.
# EOTA TR 060 2.4.3 recomienda 0.15/gamma_c = 0.10 y permite el marco
# nacional aplicable. NO se debe adoptar 0.12 automaticamente en proyecto.
C_Rdc_exterior = 0.12
aplicar_beta_red = True
beta_min_exterior = 1.10           # Minimo del informe; revisar anexo nacional

# Fuentes para trazabilidad; el script NO las abre ni consulta Internet:
# EOTA TR 060 (2017), 2.3.1, 2.4.1, 2.4.3, 3.1.
# https://www.eota.eu/sites/default/files/uploads/Technical%20reports/eota-tr-060.pdf
# ETA-12/0454, 06-12-2021, producto HDB corrugado, Anexo C2.
# PruebaHDB.pdf: 30x30, VEd=150, beta=1.40, d=190 manual, 5x HDB 12-2.
# PruebaHDB2.pdf: 50x30, VEd=250, beta=1.40, d=190 manual, 7x HDB 12-3.
# Aqui d = min(d_base, d_suplementacion), no se fuerza a los 190 del informe.
# Para borde: beta_red = max(beta/(1.2 + beta*ls/(20d)), beta_min).
# Geometria: u0=2cx+cy; u1=u0+2*pi*d; uout=u0+pi*(ls+1.5d).
# Caso enrasado solamente: NO es valido para distancia al borde > 0.

#%% 4. VALIDACIONES Y UNIDADES
if tipo_pilar.strip().lower() != "borde":
    raise SystemExit("Esta version solo estudia pilares de BORDE enrasados, sin huecos.")
if distancia_cara_pilar_borde_cm != 0:
    raise SystemExit("Solo pilar enrasado: distancia_cara_pilar_borde_cm debe ser 0.")
if recubrimiento_lateral_borde_cm is not None:
    if not isfinite(recubrimiento_lateral_borde_cm) or recubrimiento_lateral_borde_cm < 0:
        raise SystemExit("Recubrimiento lateral debe ser None o un numero no negativo.")
if not isinstance(control_extremos_generador, bool):
    raise SystemExit("control_extremos_generador debe ser True o False.")
for valor in (lado_pilar_x_cm, lado_pilar_y_cm, espesor_losa_cm,
              resistencia_hormigon_MPa, resistencia_acero_losa_MPa,
              recubrimiento_superior_cm,
              phix, sx, phiy, sy, beta, gamma_c, gamma_s, alpha_cc,
              fyk_pernos, factor_maximo_HDB, C_Rdc_exterior,
              ) :
    if not isinstance(valor, (int, float)) or not isfinite(valor) or valor <= 0:
        raise SystemExit("Revisa los datos: dimensiones, resistencias y coeficientes positivos.")
if not isfinite(fuerza_punzonamiento_kN) or fuerza_punzonamiento_kN < 0:
    raise SystemExit("VEd debe ser finito y no negativo.")
if not 1.0 <= beta_min_exterior <= beta:
    raise SystemExit("El minimo exterior debe estar entre 1 y beta.")
if not isinstance(aplicar_beta_red, bool) or not isinstance(suplemento_hasta_exterior, bool):
    raise SystemExit("Los indicadores deben ser True o False.")
if type(maximo_brazos) is not int or maximo_brazos < 3:
    raise SystemExit("maximo_brazos debe ser un entero de 3 o mas.")
if pernos_por_carril_fijos is not None:
    if type(pernos_por_carril_fijos) is not int or not 2 <= pernos_por_carril_fijos <= 100:
        raise SystemExit("Pernos fijos: entero entre 2 y 100, o None. 100 es un limite del script.")
if diametro_perno_a_detallar_mm is not None and diametro_perno_a_detallar_mm not in diametros_pernos_mm:
    raise SystemExit("El diametro elegido no esta en la lista de la empresa.")
if any(diametro not in (10, 12, 14, 16, 20, 25) for diametro in diametros_pernos_mm):
    raise SystemExit("El diametro no esta entre los HDB corrugados de esta ETA.")
numero_alternativas = len(phix_suplementario)
if numero_alternativas == 0 or any(len(lista) != numero_alternativas for lista in
        (sx_suplementario, phiy_suplementario, sy_suplementario, barras_suplementarias)):
    raise SystemExit("Las cuatro listas suplementarias deben tener la misma longitud no nula.")
if any(lista[0] != 0 for lista in (phix_suplementario, sx_suplementario,
                                  phiy_suplementario, sy_suplementario)):
    raise SystemExit("La primera alternativa debe ser 0/0 en X e Y: solo acero base.")

cx = lado_pilar_x_cm * 10
cy = lado_pilar_y_cm * 10
h = espesor_losa_cm * 10
r = recubrimiento_superior_cm * 10
VEd = fuerza_punzonamiento_kN * 1000
fck = resistencia_hormigon_MPa
fyk_losa = resistencia_acero_losa_MPa
# Canto util del armado BASE: dos capas ortogonales en contacto.
dx_base = h - r - phix / 2
dy_base = h - r - phix - phiy / 2
d_base = (dx_base + dy_base) / 2
if h < 180 or not 20 <= fck <= 50:
    raise SystemExit("Fuera del alcance: h >= 180 mm y 20 <= fck <= 50 MPa.")
if not 0 < d_base < h - r or sx * 10 <= phix or sy * 10 <= phiy:
    raise SystemExit("Revisa d_base, recubrimiento o separaciones del armado base.")
# u0: PERIMETRO COMPLETO de la seccion cargada, usado por TR 060
# en las relaciones u0/d y el control de concentracion (como el informe HDB).
u0 = 2 * (cx + cy)
# u0_borde: longitud recta de la U ABIERTA para construir u1 y uout.
# No confundir ambos: HDB imprime u0/d con el perimetro completo.
u0_borde = 2 * cx + cy
fuerza_amplificada = beta * VEd
fcd = alpha_cc * fck / gamma_c
fyd_losa = fyk_losa / gamma_s

#%% 5. ARMADO BASE Y CARRILES QUE NO CAMBIAN
area_barra_x = pi * phix**2 / 4
area_barra_y = pi * phiy**2 / 4
acero_base_x = area_barra_x * 1000 / (sx * 10)
acero_base_y = area_barra_y * 1000 / (sy * 10)

# El reparto se construira en cada alternativa.
carriles = []
diametro_perno = diametro_perno_a_detallar_mm or diametros_pernos_mm[0]
area_perno = pi * diametro_perno**2 / 4
diametro_cabeza = 3 * diametro_perno
nC = 2                            # Alcance: 2 pernos efectivos en C por brazo
mC = 5                            # Provisional: se recalcula al buscar el reparto

print("HDB BORDE ENRASADO - SUPLEMENTACION Y DISTRIBUCION AUTOMATICA")
print(f"Dimensiones: cx perpendicular={cx/10:g} cm, cy paralelo={cy/10:g} cm")
print(f"u0 completo={u0:.2f} mm; u0_borde rectilineo={u0_borde:.2f} mm")
print("Borde libre x=-cx/2. No hay refuerzo fuera del borde ni sobre la cara posterior.")
print(f"Beta en u1/C = {beta:.2f}; beta_red exterior activado={aplicar_beta_red}")
print(f"C_Rdc exterior = {C_Rdc_exterior}: valor del informe, NO universal")
print("Canto util calculado = min(d_base, d_suplementacion), segun las armaduras")
print("Pernos por brazo:", pernos_por_carril_fijos if pernos_por_carril_fijos is not None
      else "se calculan segun extension D")
print("Control propio de extremos de la U activado:", control_extremos_generador)

# Candidatos de BORDE: para cada total se prueban combinaciones:
# mC = 2*laterales + frontal + 2*diagonales_por_esquina.
# Se consideran por separado las dos caras laterales (mismo numero),
# la frontal y las dos esquinas interiores. Primero menores mC.
# Cada candidato sigue la forma (mC, diagonales, desproporcion, lateral, frontal).
candidatos_reparto = []
for total_prueba in range(3, maximo_brazos + 1):
    for esquina_prueba in range((total_prueba - 3) // 2 + 1):
        restantes = total_prueba - 2 * esquina_prueba
        for laterales_prueba in range(1, (restantes - 1) // 2 + 1):
            frontal_prueba = restantes - 2 * laterales_prueba
            if frontal_prueba < 1:
                continue
            densidades = (laterales_prueba / cx, frontal_prueba / cy)
            desproporcion = max(densidades) / min(densidades)
            candidatos_reparto.append((total_prueba, esquina_prueba,
                                       desproporcion, laterales_prueba, frontal_prueba))
candidatos_reparto.sort()
if not candidatos_reparto:
    raise SystemExit("No hay candidatos de reparto de borde.")
print("Candidatos (total, laterales por cara, frontal, esquinas por esquina):",
      [(m, lat, fr, esqu) for m, esqu, _, lat, fr in candidatos_reparto[:12]], "...")
resultados = []
primera_solucion = None
distribucion = []

#%% 6. CICLO FOR DE SUPLEMENTOS: BREAK AL CUMPLIR
for i in range(numero_alternativas):
    phi_sup_x = phix_suplementario[i]
    s_sup_x = sx_suplementario[i]
    phi_sup_y = phiy_suplementario[i]
    s_sup_y = sy_suplementario[i]
    barras_sup = barras_suplementarias[i]

    # Validar SOLO la alternativa que se esta probando.
    # Las posteriores no se evaluan si ya se encuentra solucion.
    for phi_sup, s_sup in ((phi_sup_x, s_sup_x), (phi_sup_y, s_sup_y)):
        if (not isinstance(phi_sup, (int, float)) or not isinstance(s_sup, (int, float))
                or not isfinite(phi_sup) or not isfinite(s_sup)
                or phi_sup < 0 or s_sup < 0):
            raise SystemExit("Suplementos: valores finitos no negativos.")
        if (phi_sup == 0) != (s_sup == 0):
            raise SystemExit("Suplemento nulo: 0/0. Con barra: diametro y separacion positivos.")
        if phi_sup > 0 and s_sup * 10 <= phi_sup:
            raise SystemExit("Separacion suplementaria no superior a su diametro.")

    # Cada malla se convierte POR SEPARADO a mm2/m; despues se suman.
    acero_suplementario_x = 0.0
    acero_suplementario_y = 0.0
    if phi_sup_x > 0:
        acero_suplementario_x = barras_sup * pi * phi_sup_x**2 / 4 * 1000 / (s_sup_x * 10)
    if phi_sup_y > 0:
        acero_suplementario_y = barras_sup * pi * phi_sup_y**2 / 4 * 1000 / (s_sup_y * 10)
    # CANTO UTIL: minimo del armado base y de la suplementacion.
    # Sin suplemento en alguna direccion, se mantiene el diametro base de esa direccion.
    phi_efectivo_x = phi_sup_x if phi_sup_x > 0 else phix
    phi_efectivo_y = phi_sup_y if phi_sup_y > 0 else phiy
    dx_suplementacion = h - r - phi_efectivo_x / 2
    dy_suplementacion = h - r - phi_efectivo_x - phi_efectivo_y / 2
    d_suplementacion = (dx_suplementacion + dy_suplementacion) / 2

    if d_base <= d_suplementacion:
        dx, dy = dx_base, dy_base
    else:
        dx, dy = dx_suplementacion, dy_suplementacion
    d = min(d_base, d_suplementacion)   # V4: el del diametro mayor (V3 hacia max)
    if not 0 < max(dx, dy, d) < h - r:
        raise SystemExit("Canto util no valido para esta alternativa.")
    if u0 >= 12 * d or max(cx, cy) / min(cx, cy) > 2:
        raise SystemExit("Esta geometria requiere estudiar perimetros reducidos.")

    # Solo 2 cuartos de circulo en u1, no 4 como en interior.
    u1 = u0_borde + 2 * pi * d
    vEd = fuerza_amplificada / (u1 * d)
    k = min(2.0, 1 + sqrt(200 / d))
    C_Rdc = 0.18 / gamma_c
    if u0 / d < 4:
        C_Rdc = max(0.15 / gamma_c, C_Rdc * (0.1 * u0 / d + 0.6))
    if d <= 600:
        coeficiente_minimo = 0.0525
    elif d >= 800:
        coeficiente_minimo = 0.0375
    else:
        coeficiente_minimo = 0.0525 - (d - 600) * (0.0525 - 0.0375) / 200
    vmin = coeficiente_minimo / gamma_c * k**1.5 * sqrt(fck)
    eta = max(1.0, min(1.6, 1 + (d - 200) / 1000))
    area_C_necesaria = fuerza_amplificada * gamma_s * eta / fyk_pernos
    # El acero C se calcula DESPUES de elegir el numero de brazos.
    limite_interior = 1.7 * d
    limite_exterior = 3.5 * d

    # Posiciones actualizadas para no confundir pernos de zona C y D.
    primer_perno_C = 0.50 * d
    ultimo_perno_C = 1.125 * d
    separacion_radial = 0.75 * d

    acero_losa_por_metro_x = acero_base_x + acero_suplementario_x
    acero_losa_por_metro_y = acero_base_y + acero_suplementario_y
    # V4: la cuantia, con el canto util d en las dos direcciones, como el programa de Halfen
    # (su informe del 30x60: 10,9 cm2/m sobre d = 18,8 cm, rho = 0,58 %).
    rho_x = acero_losa_por_metro_x / (1000 * d)
    rho_y = acero_losa_por_metro_y / (1000 * d)
    rho_geometrica = sqrt(rho_x * rho_y)
    rho = min(rho_geometrica, 0.02, 0.5 * fcd / fyd_losa)
    termino_hormigon = k * (100 * rho * fck)**(1 / 3)
    vRdc = max(C_Rdc * termino_hormigon, vmin)
    vRdmax = factor_maximo_HDB * vRdc

    # No se atribuye al exterior un suplemento que no llegue a ser efectivo alli.
    if suplemento_hasta_exterior:
        rho_exterior = rho
    else:
        rho_exterior = min(sqrt(acero_base_x / (1000 * d)
                                * acero_base_y / (1000 * d)), 0.02, 0.5 * fcd / fyd_losa)
    vRdc_exterior = max(C_Rdc_exterior * k * (100 * rho_exterior * fck)**(1 / 3), vmin)
    VEd_max_hormigon = vRdmax * u1 * d / beta

    # Longitud teorica requerida. Biseccion de la comprobacion exterior;
    # GEOMETRIA DE BORDE: uout = (2cx+cy) + pi*(ls+1.5d).
    # BETA RED DE BORDE: denominador 20d, no 40d del interior.
    # no confundir esta longitud con la ultima fila realmente colocada.
    ls_inferior = 0.0
    ls_superior = max(d, (beta * VEd / (vRdc_exterior * d) - u0_borde) / pi - 1.5 * d)
    for iteracion in range(70):
        ls_prueba = (ls_inferior + ls_superior) / 2
        beta_prueba = beta
        if aplicar_beta_red:
            beta_prueba = max(beta / (1.2 + beta * ls_prueba / (20 * d)), beta_min_exterior)
        capacidad_prueba = vRdc_exterior * (u0_borde + pi * (ls_prueba + 1.5 * d)) * d / beta_prueba
        if capacidad_prueba >= VEd:
            ls_superior = ls_prueba
        else:
            ls_inferior = ls_prueba
    ls_necesario = ls_superior
    if ls_necesario < 1e-8:
        ls_necesario = 0.0

    # Modo FIJO o modo de ajuste de filas D. Los brazos se buscan mas abajo.
    if pernos_por_carril_fijos is None:
        nD = max(0, ceil((ls_necesario - ultimo_perno_C) / separacion_radial - 1e-12))
    else:
        nD = pernos_por_carril_fijos - nC
    if nD > 100:
        raise SystemExit("Mas de 100 filas D: fuera del limite de exploracion del script.")
    posiciones = [primer_perno_C, ultimo_perno_C]
    for fila_D in range(1, nD + 1):
        posiciones.append(ultimo_perno_C + fila_D * separacion_radial)
    ls_colocado = posiciones[-1]
    mD = mC if nD > 0 else 0
    pernos_C = mC * nC
    pernos_D = mD * nD
    u_out_colocado = u0_borde + pi * (ls_colocado + 1.5 * d)
    beta_red = beta
    if aplicar_beta_red:
        beta_red = max(beta / (1.2 + beta * ls_colocado / (20 * d)), beta_min_exterior)
    # Este perimetro necesario usa beta_red de la CONFIGURACION COLOCADA.
    u_out_necesario = beta_red * VEd / (vRdc_exterior * d)
    vEd_exterior = beta_red * VEd / (u_out_colocado * d)
    VEd_max_exterior = vRdc_exterior * u_out_colocado * d / beta_red

    # BUSQUEDA DEL REPARTO DE BORDE.
    # Cada alternativa conserva el numero radial de pernos; prueban brazos
    # laterales (dos caras), frontal (una cara) y diagonales (dos esquinas).
    # Usamos distancia recta entre brazos vecinos sobre la U ABIERTA.
    # En r=d -> limite 1.7d; en r=ls -> limite 3.5d.
    # No se conecta el ultimo brazo al primero atravesando el borde libre.
    reparto_encontrado = False
    repartos_probados = []
    cumple_hormigon = VEd <= VEd_max_hormigon + 1e-7
    cumple_exterior = VEd <= VEd_max_exterior + 1e-7
    elegido = None
    ultimo_probado = None
    diametros_a_revisar = (diametros_pernos_mm if diametro_perno_a_detallar_mm is None
                           else [diametro_perno_a_detallar_mm])
    candidatos_a_revisar = candidatos_reparto
    if not (cumple_hormigon and cumple_exterior):
        # Si falla u1 o el contorno exterior, ni 64 brazos ni otros
        # diametros resuelven esta alternativa longitudinal.
        # Probar 1 candidato solo para mantener los datos de diagnostico,
        # y pasar al suplemento siguiente, sin hacer una busqueda inutil.
        diametros_a_revisar = diametros_a_revisar[:1]
        candidatos_a_revisar = candidatos_reparto[:1]
        print(f"Alternativa {i}: no cumple u1 o exterior; "
              "se omite busqueda exhaustiva de brazos.")
    for diametro_prueba in diametros_a_revisar:
        area_perno_prueba = pi * diametro_prueba**2 / 4
        cabeza_prueba = 3 * diametro_prueba
        for _, esquina_prueba, _, carriles_cara_x, carriles_cara_y in candidatos_a_revisar:
            # En BORDE: carriles_cara_x = por cada lateral (longitud cx),
            #          carriles_cara_y = en cara frontal (longitud cy).
            # Control de cobertura de los dos extremos libres de la U.
            distancia_extremo = cx / (2 * carriles_cara_x)
            cobertura_extremos_ok = (not control_extremos_generador
                                   or distancia_extremo <= limite_interior / 2 + 1e-8)
            # No descartamos el candidato por continue: si TODOS fallan,
            # conservamos uno diagnosticado para evitar una variable vacia.
            carriles = []
            # Dos caras laterales, orientadas hacia +/-Y, desde el borde
            # libre hasta la cara frontal. Misma cantidad en ambas.
            for j in range(carriles_cara_x):
                x = -cx / 2 + (j + 0.5) * cx / carriles_cara_x
                carriles.extend([(x, cy / 2, 0.0, 1.0),
                                 (x, -cy / 2, 0.0, -1.0)])
            # Cara frontal x=+cx/2, normal hacia la losa en +X.
            for j in range(carriles_cara_y):
                y = -cy / 2 + (j + 0.5) * cy / carriles_cara_y
                carriles.append((cx / 2, y, 1.0, 0.0))
            # Diagonales SOLO en las dos esquinas interiores (x=+cx/2).
            for signo_y in (1, -1):
                for j in range(esquina_prueba):
                    angulo = (j + 0.5) * pi / (2 * esquina_prueba)
                    carriles.append((cx / 2, signo_y * cy / 2,
                                     cos(angulo), signo_y * sin(angulo)))
            mC_prueba = len(carriles)
            VRd_acero_C_prueba = mC_prueba * nC * area_perno_prueba * fyk_pernos / (gamma_s * eta)
            acero_ok = VEd <= VRd_acero_C_prueba / beta + 1e-7

            # Orden por angulo polar en [-pi,+pi]: corresponde a una U abierta
            # desde el extremo inferior al superior, sin cierre por borde libre.
            separaciones_maximas = []
            for radio_control in (d, ls_colocado):
                puntos = sorted(((x0 + radio_control * ux, y0 + radio_control * uy)
                                 for x0, y0, ux, uy in carriles),
                                key=lambda q: atan2(q[1], q[0]))
                separaciones_maximas.append(max(
                    hypot(puntos[n][0] - puntos[n-1][0], puntos[n][1] - puntos[n-1][1])
                    for n in range(1, len(puntos))))
            separacion_interior, separacion_exterior = separaciones_maximas

            # Todas las posiciones, para excluir colisiones entre cabezas.
            coordenadas_pernos = []
            for x0, y0, ux, uy in carriles:
                for distancia_pilar in posiciones:
                    coordenadas_pernos.append((x0 + distancia_pilar * ux,
                                               y0 + distancia_pilar * uy))
            distancia_minima = float("inf")
            for indice_perno in range(len(coordenadas_pernos)):
                for otro_perno in range(indice_perno + 1, len(coordenadas_pernos)):
                    distancia_minima = min(distancia_minima, hypot(
                        coordenadas_pernos[indice_perno][0] - coordenadas_pernos[otro_perno][0],
                        coordenadas_pernos[indice_perno][1] - coordenadas_pernos[otro_perno][1]))

            # Borde libre x=-cx/2; comprobar cada cabeza, no solo los ejes.
            recubrimiento_lateral_disponible = min(
                (x + cx/2 - cabeza_prueba/2) for x, y in coordenadas_pernos)
            cabezas_dentro = recubrimiento_lateral_disponible >= -1e-8
            if recubrimiento_lateral_borde_cm is not None:
                cabezas_dentro = (cabezas_dentro and recubrimiento_lateral_disponible
                                 >= recubrimiento_lateral_borde_cm*10 - 1e-8)
            geometria_ok = (separacion_interior <= limite_interior + 1e-8
                            and separacion_exterior <= limite_exterior + 1e-8
                            and distancia_minima > cabeza_prueba + 1e-8
                            and cabezas_dentro and cobertura_extremos_ok)
            repartos_probados.append((diametro_prueba, mC_prueba, carriles_cara_x, carriles_cara_y,
                                      esquina_prueba, acero_ok, geometria_ok))
            probado = {
                "diametro": diametro_prueba, "area": area_perno_prueba, "cabeza": cabeza_prueba,
                "carriles": carriles[:], "mC": mC_prueba, "nx": carriles_cara_x,
                "ny": carriles_cara_y, "esquina": esquina_prueba,
                "VRd": VRd_acero_C_prueba, "acero_ok": acero_ok,
                "geometria_ok": geometria_ok, "sep_i": separacion_interior,
                "sep_e": separacion_exterior, "dmin": distancia_minima,
                "coordenadas": coordenadas_pernos,
                "recubrimiento_lateral_disponible": recubrimiento_lateral_disponible,
                "distancia_extremo": distancia_extremo,
                "acero_mm2": mC_prueba * len(posiciones) * area_perno_prueba,
            }
            ultimo_probado = probado
            if acero_ok and geometria_ok:
                if elegido is None or probado["acero_mm2"] < elegido["acero_mm2"] - 1e-9:
                    elegido = probado
                break

    # Las variables que usa el resto del script, con el elegido (o el ultimo probado si no cumple ninguno).
    reparto_encontrado = elegido is not None
    escogido = elegido if elegido is not None else ultimo_probado
    if escogido is None:
        raise SystemExit("No se genero ningun candidato de borde para evaluar.")
    diametro_perno = escogido["diametro"]
    area_perno = escogido["area"]
    diametro_cabeza = escogido["cabeza"]
    carriles = escogido["carriles"]
    carriles_cara_x, carriles_cara_y = escogido["nx"], escogido["ny"]
    carriles_por_esquina = escogido["esquina"]
    mC = escogido["mC"]
    mD = mC if nD > 0 else 0
    pernos_C = mC * nC
    pernos_D = mD * nD
    area_C_colocada = pernos_C * area_perno
    VRd_acero_C = escogido["VRd"]
    VEd_max_acero_C = VRd_acero_C / beta
    cumple_acero_C = escogido["acero_ok"]
    cumple_geometria = escogido["geometria_ok"]
    separacion_interior, separacion_exterior = escogido["sep_i"], escogido["sep_e"]
    distancia_minima = escogido["dmin"]
    coordenadas_pernos = escogido["coordenadas"]
    # Tipo como se pide: HDB-diametro/altura-pernos/largo (pasos). Altura del perno: la del catalogo
    # (165 a 355 de 10 en 10) que no es menor que h - 2·recubrimiento; pasos redondeados al mm uno a uno;
    # pletina 75 mm mas alla del ultimo perno (como los tres informes de Halfen).
    altura_perno = next((a for a in range(165, 356, 10) if a >= h - 2 * r - 1e-6), None)
    pasos_mm = []
    for numero_fila, distancia_pilar in enumerate(posiciones):
        anterior = posiciones[numero_fila - 1] if numero_fila else 0.0
        pasos_mm.append(int(floor(distancia_pilar - anterior + 0.5 + 1e-9)))
    grupos_pasos = []
    for paso in pasos_mm:
        if grupos_pasos and grupos_pasos[-1][1] == paso:
            grupos_pasos[-1][0] += 1
        else:
            grupos_pasos.append([1, paso])
    tipo_hdb = (f"HDB-{diametro_perno:g}/{altura_perno or '?'}-{len(posiciones)}/{sum(pasos_mm) + 75} ("
                + "/".join(f"{n}x{p}" if n > 1 else f"{p}" for n, p in grupos_pasos) + "/75)")

    # El for anterior encuentra la primera propuesta dentro de la familia elegida
    # que cumple acero C y geometria; ahora se comprueban hormigon y exterior.
    cumple = (reparto_encontrado and cumple_hormigon and cumple_acero_C
              and cumple_exterior and cumple_geometria)
    VEd_max_configuracion = min(VEd_max_hormigon, VEd_max_acero_C, VEd_max_exterior)

    # V4a - APROVECHAMIENTO: la resistencia gobernante es la MENOR de las tres.
    # El porcentaje global es el MAYOR de los tres porcentajes parciales.
    # No confundir el aprovechamiento en u1 (como la barra de HDB)
    # con el aprovechamiento real de la configuracion de pernos y exterior.
    aprovechamiento_hormigon = 100 * VEd / VEd_max_hormigon
    aprovechamiento_acero_C = 100 * VEd / VEd_max_acero_C
    aprovechamiento_exterior = 100 * VEd / VEd_max_exterior
    aprovechamiento = max(aprovechamiento_hormigon, aprovechamiento_acero_C,
                          aprovechamiento_exterior)

    if VEd_max_configuracion == VEd_max_acero_C:
        comprobacion_gobernante = "Acero de pernos en C"
    elif VEd_max_configuracion == VEd_max_hormigon:
        comprobacion_gobernante = "Resistencia maxima en u1"
    else:
        comprobacion_gobernante = "Perimetro exterior"

    resultado = {
        "indice": i, "suplemento_x": (phi_sup_x, s_sup_x),
        # Datos exclusivos para rotular el plano (sin recalcular resistencias).
        "armado_base_x": (phix, sx), "armado_base_y": (phiy, sy),
        "numero_barras_suplementarias": barras_sup,
        "VEd_kN": VEd / 1000,
        "carriles_por_cara": carriles_cara_x if carriles_cara_x == carriles_cara_y else None,
        "carriles_por_esquina": carriles_por_esquina, "tipo_hdb": tipo_hdb,
        "carriles_cara_x": carriles_cara_x, "carriles_cara_y": carriles_cara_y,
        "carriles_laterales_por_cara": carriles_cara_x,
        "carriles_frontal": carriles_cara_y,
        "carriles_diagonales_por_esquina": carriles_por_esquina,
        "recubrimiento_lateral_disponible": escogido["recubrimiento_lateral_disponible"],
        "distancia_extremo": escogido["distancia_extremo"],
        "reparto_encontrado": reparto_encontrado,
        "repartos_probados": repartos_probados[:],
        "u0": u0, "u0_borde": u0_borde, "u1": u1,
        "d_base": d_base, "d_suplementacion": d_suplementacion,
        "dx": dx, "dy": dy,
        "suplemento_y": (phi_sup_y, s_sup_y), "d": d,
        "acero_losa_por_metro_x": acero_losa_por_metro_x,
        "acero_losa_por_metro_y": acero_losa_por_metro_y,
        "rho": rho, "rho_exterior": rho_exterior, "vRdc": vRdc,
        "vRdmax": vRdmax, "vRdc_exterior": vRdc_exterior,
        "mC": mC, "mD": mD, "nC": nC, "nD": nD, "diametro": diametro_perno,
        "posiciones": posiciones[:], "ls_necesario": ls_necesario,
        "ls_colocado": ls_colocado, "u_out_colocado": u_out_colocado,
        "u_out_necesario": u_out_necesario, "beta_red": beta_red,
        "VRd_acero_C": VRd_acero_C, "area_C_necesaria": area_C_necesaria,
        "VEd_max_hormigon": VEd_max_hormigon, "VEd_max_acero_C": VEd_max_acero_C,
        "VEd_max_exterior": VEd_max_exterior, "VEd_max_configuracion": VEd_max_configuracion,
        "comprobacion_gobernante": comprobacion_gobernante,
        "aprovechamiento": aprovechamiento,  # Porcentaje global, para el programa principal
        "aprovechamiento_hormigon": aprovechamiento_hormigon,
        "aprovechamiento_acero_C": aprovechamiento_acero_C,
        "aprovechamiento_exterior": aprovechamiento_exterior,
        "cumple_hormigon": cumple_hormigon, "cumple_acero_C": cumple_acero_C,
        "cumple_exterior": cumple_exterior, "cumple_geometria": cumple_geometria,
        "cumple": cumple, "carriles": carriles[:], "coordenadas_pernos": coordenadas_pernos,
        "separacion_interior": separacion_interior, "separacion_exterior": separacion_exterior,
        "distancia_minima_centros": distancia_minima,
        "pernos_C": pernos_C, "pernos_D": pernos_D,
        "area_C_colocada": area_C_colocada, "vEd_exterior": vEd_exterior
    }
    resultados.append(resultado)
    print(f"\nALTERNATIVA {i}: suplemento X={phi_sup_x}/{s_sup_x}; Y={phi_sup_y}/{s_sup_y}")
    print(f"d_base={d_base:.2f}; d_suplementacion={d_suplementacion:.2f}; d=min={d:.2f} mm")
    print(f"Asx={acero_losa_por_metro_x / 100:.5f}; Asy={acero_losa_por_metro_y / 100:.5f} cm2/m")
    print(f"rho={rho:.7f}; vRdc={vRdc:.6f}; vRdc_exterior={vRdc_exterior:.6f} MPa")
    print(f"u0/d completo={u0/d:.3f}; u1 de borde={u1:.3f} mm")
    print(f"VRdc={vRdc * u1 * d / 1000:.3f}; VRdmax={vRdmax * u1 * d / 1000:.3f} kN")
    print(f"Brazos probados (diametro, mC, laterales, frontal, por esquina, acero_C_ok, geometria_ok): {repartos_probados[:20]}")
    print(f"Elegido: diametro {diametro_perno} mm; tipo {tipo_hdb}")
    print(f"mC={mC}; nC={nC}; nD={nD}; total={pernos_C + pernos_D} pernos")
    print("Posiciones desde la cara del pilar (mm):", [round(p, 3) for p in posiciones])
    print(f"ls_necesario={ls_necesario:.3f}; ls_colocado={ls_colocado:.3f} mm")
    print(f"u_out_colocado={u_out_colocado:.3f} mm; beta_red={beta_red:.3f}")
    print(f"Limites VEd ANTES de beta: sistema={VEd_max_hormigon / 1000:.3f}; "
          f"acero C={VEd_max_acero_C / 1000:.3f}; exterior={VEd_max_exterior / 1000:.3f} kN")
    print(f"Capacidad resistente={VEd_max_configuracion / 1000:.3f} kN "
          f"= {VEd_max_configuracion / 9806.65:.3f} tf; gobierna {comprobacion_gobernante}")
    print(f"Geometria programada: {cumple_geometria}; resultado: {'CUMPLE CALCULOS PROGRAMADOS' if cumple else 'NO CUMPLE'}")
    if not cumple_hormigon:
        print("Falla u1: mas pernos D NO resuelven este limite para el armado actual.")
    if not cumple_acero_C:
        print("Falla acero C: mas acero superior o mas pernos SOLO en D NO resuelven ese limite.")
    if not cumple_exterior:
        print("Falla exterior: revisar armado eficaz exterior, extension del HDB o configuracion.")
    if not reparto_encontrado:
        print("No se encontro reparto que cumpla acero C y geometria dentro del limite de busqueda.")
    elif not cumple_geometria:
        print("Falla geometria: la cifra de capacidad resistente NO acredita una solucion admisible.")

    # IMPORTANTE: este break sale del bucle de SUPLEMENTOS.
    # Solo se llega aqui despues de comprobar resistencia Y geometria.
    if cumple:
        primera_solucion = resultado
        print("SE ELIGE ESTA ALTERNATIVA. No se calculan las siguientes.")
        break

#%% 7. RESULTADO UNICO Y DISTRIBUCION DE LA ALTERNATIVA SELECCIONADA
print("\n" + "=" * 76)
print("RESULTADO FINAL - PRIMERA ALTERNATIVA QUE CUMPLE")
print("=" * 76)
print(f"Alternativas calculadas: {len(resultados)} de {numero_alternativas}")

if primera_solucion is None:
    print("NINGUNA alternativa cumple todos los controles con este reparto y diametro.")
    print("NO SE SELECCIONA una distribucion como valida.")
    print("Revisa las causas indicadas en cada alternativa.")
    print("Se exploraron brazos adicionales y los diametros de la lista.")
else:
    # Al detener el bucle, las variables corresponden a la alternativa elegida.
    # No usamos los valores de otra alternativa posterior.
    print(f"Alternativa elegida: {i} (0 = solo armado base)")
    print(f"Armado superior BASE: X = diametro {phix:g} mm cada {sx:g} cm; "
          f"Y = diametro {phiy:g} mm cada {sy:g} cm")
    if phi_sup_x == 0 and phi_sup_y == 0:
        print("SUPLEMENTACION: NINGUNA. Cumple con el acero base.")
    else:
        if phi_sup_x == 0:
            print("SUPLEMENTO X: ninguno.")
        else:
            print(f"SUPLEMENTO X: diametro {phi_sup_x:g} mm cada {s_sup_x:g} cm.")
        if phi_sup_y == 0:
            print("SUPLEMENTO Y: ninguno.")
        else:
            print(f"SUPLEMENTO Y: diametro {phi_sup_y:g} mm cada {s_sup_y:g} cm.")
    print(f"Canto util elegido d = min({d_base:.2f}, {d_suplementacion:.2f}) = {d:.2f} mm")
    print(f"Acero total X = {acero_losa_por_metro_x / 100:.3f} cm2/m; "
          f"Y = {acero_losa_por_metro_y / 100:.3f} cm2/m")
    if vEd <= vRdc:
        print("En u1 no se necesita armadura de punzonamiento con este armado.")
        print("Se muestra la comprobacion del HDB PREFIJADO, no una necesidad de colocarlo.")

    print("\nREPARTO HDB")
    print(f"Perno elegido: {diametro_perno:g} mm")
    print(f"mC = {mC} brazos; mD = {mD} brazos")
    print(f"Cada una de las dos caras LATERALES (longitud cx): {carriles_cara_x} brazos")
    print(f"Cara FRONTAL (longitud cy): {carriles_cara_y} brazos")
    print(f"Cada una de las dos esquinas interiores: {carriles_por_esquina} diagonales")
    print("Cara posterior coincidente con borde libre: 0 brazos")
    print(f"TIPO HDB TEORICO, NO PEDIDO COMERCIAL: {mC} x {tipo_hdb}")
    print(f"nC = {nC} pernos C/brazo; nD = {nD} pernos D/brazo")
    print(f"Total = {mC} brazos x {nC + nD} pernos = {pernos_C + pernos_D} pernos")
    print(f"Pernos en C: {pernos_C}; pernos en D: {pernos_D}")
    print(f"ls_colocado = {ls_colocado:.3f} mm; u_out_colocado = {u_out_colocado:.3f} mm")

    print("\nPOSICIONES RADIALES (IGUALES EN TODOS LOS BRAZOS)")
    print("Perno | Zona | Distancia a cara/esquina [mm] | Paso anterior [mm]")
    distancia_anterior = 0.0
    for numero_fila, distancia_pilar in enumerate(posiciones, start=1):
        zona = "C" if numero_fila <= nC else "D"
        print(f"{numero_fila:5d} | {zona:4s} | {distancia_pilar:29.3f} | "
              f"{distancia_pilar - distancia_anterior:18.3f}")
        distancia_anterior = distancia_pilar
    print("El primer paso se mide desde el pilar; los siguientes, entre pernos.")
    print("ls_colocado NO es la longitud comercial de la pletina.")

    print("\nDISTRIBUCION EN PLANTA")
    print("Coordenadas en mm. Origen: centro del pilar. +X derecha; +Y arriba.")
    print("Angulo desde +X, sentido antihorario. Se muestran los ejes de los pernos.")
    print("Las diagonales parten solo de las dos ESQUINAS INTERIORES (+X).")
    print("NO se generan pernos fuera del borde libre x=-cx/2.")
    for numero_carril, (x0, y0, ux, uy) in enumerate(carriles, start=1):
        angulo = degrees(atan2(uy, ux)) % 360
        print(f"\nBrazo {numero_carril:02d}: arranque ({x0:.2f}, {y0:.2f}) mm; "
              f"angulo = {angulo:.2f} grados")
        print("  Perno | Zona |        X [mm] |        Y [mm] | Distancia [mm]")
        for numero_fila, distancia_pilar in enumerate(posiciones, start=1):
            zona = "C" if numero_fila <= nC else "D"
            x = x0 + distancia_pilar * ux
            y = y0 + distancia_pilar * uy
            distribucion.append({
                "carril": numero_carril, "perno": numero_fila, "zona": zona,
                "x_mm": x, "y_mm": y, "distancia_pilar_mm": distancia_pilar,
                "angulo_grados": angulo
            })
            print(f"  {numero_fila:5d} | {zona:4s} | {x:13.2f} | {y:13.2f} | "
                  f"{distancia_pilar:14.3f}")
    primera_solucion["distribucion"] = distribucion

    print("\nCOMPROBACIONES Y CAPACIDAD DEL RESULTADO ELEGIDO")
    print(f"Sistema: {VEd / 1000:.3f} <= {VEd_max_hormigon / 1000:.3f} kN")
    print(f"Acero C: {VEd / 1000:.3f} <= {VEd_max_acero_C / 1000:.3f} kN")
    print(f"Exterior: {VEd / 1000:.3f} <= {VEd_max_exterior / 1000:.3f} kN")
    print(f"Separacion interior sobre contorno = {separacion_interior:.3f} "
          f"<= {limite_interior:.3f} mm")
    print(f"Separacion exterior sobre contorno = {separacion_exterior:.3f} "
          f"<= {limite_exterior:.3f} mm")
    print(f"Distancia minima entre ejes = {distancia_minima:.3f} mm; "
          f"diametro cabeza = {diametro_cabeza:.3f} mm (sin solapamiento)")
    print(f"Recubrimiento lateral geometrico minimo a cabezas = "
          f"{primera_solucion['recubrimiento_lateral_disponible']:.2f} mm")
    print(f"Distancia del extremo libre al primer brazo lateral = "
          f"{primera_solucion['distancia_extremo']:.2f} mm")
    print(f"CAPACIDAD VEd = {VEd_max_configuracion / 1000:.3f} kN "
          f"= {VEd_max_configuracion / 9806.65:.3f} tf")

    # V4a - Resumen como HDB, sin ocultar los otros limites del conjunto.
    print("\nAPROVECHAMIENTO")
    print(f"VRd,c en u1 = {vRdc * u1 * d / 1000:.2f} kN")
    print(f"VRd,max en u1 = {vRdmax * u1 * d / 1000:.2f} kN")
    print(f"beta x VEd = {fuerza_amplificada / 1000:.2f} kN")
    print(f"Aprovechamiento sistema HDB (u1) = {aprovechamiento_hormigon:.2f} %")
    print(f"Aprovechamiento acero en C = {aprovechamiento_acero_C:.2f} %")
    print(f"Aprovechamiento perimetro exterior = {aprovechamiento_exterior:.2f} %")
    print(f"APROVECHAMIENTO DEL CONJUNTO = {aprovechamiento:.2f} %")
    barras_llenas = min(30, max(0, round(aprovechamiento / 100 * 30)))
    print("[" + "#" * barras_llenas + "." * (30 - barras_llenas) + "] 100 % = limite")
    print(f"Gobierna: {comprobacion_gobernante}")
    print("Cumple las comprobaciones PROGRAMADAS; quedan las verificaciones de proyecto.")
    print("Se ha elegido la PRIMERA valida en tus listas, no la de menor peso o coste.")

print("\nPENDIENTES: disposicion real y canto util de la armadura suplementaria; bandas eficaces;")
print("continuidad y anclaje mas alla de u_out; justificacion de C_Rdc,out y beta_min;")
print("longitudes comerciales, altura y anclaje de pernos, recubrimientos y hormigonado.")
print("El tipo HDB impreso es una aproximacion GEOMETRICA, NO referencia comercial validada.")
print("En cada alternativa se prueban los diametros de la lista y se queda el de menos acero.")
if pernos_por_carril_fijos is not None:
    print("Los pernos por brazo son fijos; los brazos pueden aumentar.")
else:
    print("Los pernos D y los brazos pueden aumentar segun la alternativa.")
print("BORDE: la cara posterior es borde libre. No aplica a retranqueos, esquinas ni huecos.")
print("La cobertura de extremos es una regla ADICIONAL de este generador, no de TR 060.")
print("TR 060 3.1 exige armadura transversal cerca de bordes libres (PENDIENTE).")
print("Los brazos se eligen dentro de la familia buscada; no es el selector comercial HDB.")


#%% 8. FUNCION DE PLOTEO (MISMA PRESENTACION QUE EL PILAR INTERIOR)
def plotear_hdb_borde(solucion, cx_mm, cy_mm, mostrar=True, guardar=False,
                        archivo_png="HDB_Borde_Distribucion.png",
                        numerar_brazos=True):
    """Dibuja el pilar EN BORDE, los brazos y los pernos C/D.

    Parametros:
      solucion: diccionario primera_solucion generado por el calculo.
      cx_mm, cy_mm: dimension perpendicular/paralela al borde, en mm.
      mostrar: abre la ventana Matplotlib al finalizar.
      guardar: guarda PNG de alta resolucion (archivo_png).
      numerar_brazos: identifica los brazos junto a sus extremos.

    Devuelve (figura, ejes). Si no hay solucion valida, (None, None).
    NO calcula resistencias ni modifica la distribucion seleccionada.
    Borde libre vertical en x = -cx_mm/2; la losa esta hacia +X.
    La longitud dibujada es teorica: de la cara/esquina al ultimo perno;
    no representa necesariamente la longitud comercial de la pletina.
    """
    if solucion is None or not solucion.get("cumple", False):
        print("GRAFICO HDB: no hay solucion valida para dibujar.")
        return None, None

    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Patch
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter

    carriles_plano = solucion["carriles"]
    posiciones_plano = solucion["posiciones"]
    nC_plano = solucion["nC"]
    diametro_plano = solucion["diametro"]
    radio_cabeza = 1.5 * diametro_plano  # ETA: diametro cabeza = 3 veces el vastago.

    if not carriles_plano or not posiciones_plano:
        print("GRAFICO HDB: faltan brazos o posiciones de pernos.")
        return None, None

    # Diagrama a la izquierda y cuadro de armado/aprovechamiento a la derecha.
    # Se utiliza la solucion ya calculada: no se modifican posiciones ni resultados.
    figura = plt.figure(figsize=(13.0, 9.1), facecolor="white")
    ejes = figura.add_axes([0.065, 0.215, 0.615, 0.685])
    ejes.set_facecolor("#fbfcfe")
    panel = figura.add_axes([0.705, 0.165, 0.275, 0.735])
    panel.set_xlim(0, 1)
    panel.set_ylim(0, 1)
    panel.axis("off")
    panel.add_patch(Rectangle((0, 0), 1, 1, facecolor="#f7f9fc",
                              edgecolor="#dce4eb", linewidth=1.1,
                              transform=panel.transAxes, zorder=0))

    # Dibujo del pilar, centrado en el origen del modelo.
    ejes.add_patch(Rectangle((-cx_mm / 2, -cy_mm / 2), cx_mm, cy_mm,
                             edgecolor="#8c5128", facecolor="#d9a779",
                             linewidth=2, zorder=4))
    ejes.text(0, 0, f"PILAR BORDE\n{cx_mm/10:g} x {cy_mm/10:g} cm",
              ha="center", va="center", fontsize=10, weight="bold",
              color="#57331d", zorder=5)

    todos_los_x = [-cx_mm / 2, cx_mm / 2]
    todos_los_y = [-cy_mm / 2, cy_mm / 2]

    # Se usan las coordenadas teoricas del CALCULO, sin redondear ni reubicar pernos.
    for numero_brazo, (x0, y0, ux, uy) in enumerate(carriles_plano, start=1):
        xx = [x0 + distancia * ux for distancia in posiciones_plano]
        yy = [y0 + distancia * uy for distancia in posiciones_plano]
        todos_los_x.extend(xx)
        todos_los_y.extend(yy)

        # Eje del brazo, desde su origen en el pilar al ultimo perno.
        ejes.plot([x0, xx[-1]], [y0, yy[-1]], color="#394d63",
                  linewidth=3.2, solid_capstyle="round", zorder=2)

        # Cabezas de pernos con dimensiones fisicas relativas a la planta.
        for numero_perno, (xp, yp) in enumerate(zip(xx, yy), start=1):
            color = "#287ab7" if numero_perno <= nC_plano else "#e09a3c"
            ejes.add_patch(Circle((xp, yp), radius=radio_cabeza,
                                  facecolor=color, edgecolor="#173048",
                                  linewidth=0.75, zorder=6))
            ejes.plot(xp, yp, marker="o", markersize=1.9,
                      markerfacecolor="white", markeredgecolor="white", zorder=7)

        if numerar_brazos:
            separacion_rotulo = max(50.0, 3.0 * radio_cabeza)
            xt = xx[-1] + separacion_rotulo * ux
            yt = yy[-1] + separacion_rotulo * uy
            ejes.text(xt, yt, f"{numero_brazo:02d}", ha="center", va="center",
                      fontsize=8, color="#263b52", weight="bold", zorder=8)
            todos_los_x.append(xt)
            todos_los_y.append(yt)

    # El borde libre coincide con la cara izquierda del pilar, x=-cx/2.
    # La zona sin losa queda ligeramente visible para identificar ese borde;
    # la region de losa se marca sutilmente a la derecha sin ocultar pernos.
    x_borde_libre = -cx_mm / 2
    x_mayor = max(todos_los_x)
    y_alcance = max(abs(valor) for valor in todos_los_y)
    margen = max(90.0, 0.12 * max(x_mayor - x_borde_libre, 2 * y_alcance))
    xmin = x_borde_libre - max(120.0, 0.28 * margen)
    xmax = x_mayor + margen
    ymin, ymax = -y_alcance - margen, y_alcance + margen
    ejes.set_xlim(xmin, xmax)
    ejes.set_ylim(ymin, ymax)
    # Zona de losa hacia +X, sin inventar la extension real de la placa.
    ejes.add_patch(Rectangle((x_borde_libre, ymin), xmax-x_borde_libre, ymax-ymin,
                             facecolor="#edf5f7", edgecolor="none", alpha=0.47,
                             zorder=0))
    ejes.plot([x_borde_libre, x_borde_libre], [ymin, ymax],
              color="#ba514b", linewidth=2.6, linestyle=(0, (6, 3)), zorder=3)
    ejes.text(x_borde_libre - 45, ymax - 0.035 * (ymax-ymin), "BORDE LIBRE",
              rotation=90, ha="center", va="top", fontsize=9,
              color="#a64039", weight="bold", zorder=3)
    ejes.set_aspect("equal", adjustable="box")
    ejes.grid(True, color="#b6c3cf", linewidth=0.6, alpha=0.3)
    ejes.set_axisbelow(True)
    # El calculo utiliza mm; los ejes se muestran en cm para facilitar la lectura.
    ejes.xaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor / 10:g}"))
    ejes.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor / 10:g}"))
    ejes.set_xlabel("X [cm]")
    ejes.set_ylabel("Y [cm]")

    n_pernos = len(carriles_plano) * len(posiciones_plano)
    texto_resumen = (f"{len(carriles_plano)} brazos  |  "
                     f"{len(posiciones_plano)} pernos/brazo  |  "
                     f"{n_pernos} pernos  |  Diametro {diametro_plano:g} mm")
    figura.suptitle("HDB - PILAR DE BORDE | DISTRIBUCION EN PLANTA",
                    x=0.065, y=0.967, ha="left", fontsize=17, weight="bold",
                    color="#243c53")
    ejes.set_title(texto_resumen, fontsize=10, pad=12, color="#394d63")
    laterales = solucion.get("carriles_laterales_por_cara", 0)
    frontal = solucion.get("carriles_frontal", 0)
    diagonales = solucion.get("carriles_diagonales_por_esquina", 0)
    ejes.text(0.5, 1.005,
              f"Laterales: {laterales} por cara  |  Frontal: {frontal}  |  "
              f"Esquinas interiores: {diagonales} por esquina",
              transform=ejes.transAxes, ha="center", va="bottom",
              fontsize=8.5, color="#526d82")

    # ----------- Cuadro lateral: armado realmente elegido ----------------
    base_x = solucion.get("armado_base_x", (None, None))
    base_y = solucion.get("armado_base_y", (None, None))
    sup_x = solucion.get("suplemento_x", (0, 0))
    sup_y = solucion.get("suplemento_y", (0, 0))
    n_sup = solucion.get("numero_barras_suplementarias", 1)

    panel.text(0.06, 0.965, "ARMADO SUPERIOR UTILIZADO", fontsize=11,
               weight="bold", color="#243c53", va="top")
    panel.plot([0.06, 0.94], [0.923, 0.923], color="#d4dde7", linewidth=1)

    panel.text(0.06, 0.891, "ARMADO BASE", fontsize=9, weight="bold",
               color="#536a7b")
    if base_x[0] is not None and base_y[0] is not None:
        panel.text(0.08, 0.849, f"X: Ø{base_x[0]:g}/{base_x[1]:g}",
                   fontsize=10.2, color="#273d52")
        panel.text(0.08, 0.811, f"Y: Ø{base_y[0]:g}/{base_y[1]:g}",
                   fontsize=10.2, color="#273d52")
    else:
        panel.text(0.08, 0.842, "No disponible", fontsize=10, color="#536a7b")

    panel.text(0.06, 0.748, "SUPLEMENTACION", fontsize=9, weight="bold",
               color="#536a7b")
    def texto_suplemento(datos):
        diametro, paso = datos
        if not diametro or not paso:
            return "Ninguno"
        cantidad = f"{n_sup:g} × " if n_sup != 1 else ""
        return f"{cantidad}Ø{diametro:g}/{paso:g}"
    if (sup_x[0] or sup_y[0]):
        panel.text(0.08, 0.706, "X: " + texto_suplemento(sup_x),
                   fontsize=10.2, color="#273d52")
        panel.text(0.08, 0.669, "Y: " + texto_suplemento(sup_y),
                   fontsize=10.2, color="#273d52")
    else:
        panel.text(0.08, 0.704, "Sin suplemento: solo acero base",
                   fontsize=9.5, color="#273d52")

    asx = solucion.get("acero_losa_por_metro_x")
    asy = solucion.get("acero_losa_por_metro_y")
    if asx is not None and asy is not None:
        panel.text(0.06, 0.618, f"As total  X: {asx / 100:.2f} cm²/m  |  Y: {asy / 100:.2f} cm²/m",
                   fontsize=9.5, weight="bold", color="#364f68")

    # ----------- Cuadro lateral: aprovechamientos calculados -------------
    panel.plot([0.06, 0.94], [0.579, 0.579], color="#d4dde7", linewidth=1)
    panel.text(0.06, 0.547, "APROVECHAMIENTO", fontsize=11, weight="bold",
               color="#243c53")
    ap_global = solucion.get("aprovechamiento")
    if ap_global is not None:
        panel.text(0.06, 0.471, f"{ap_global:.2f} %", fontsize=24, weight="bold",
                   color="#235178")
        panel.text(0.06, 0.431, "Del conjunto (comprobacion gobernante)",
                   fontsize=8.5, color="#607182")

    barras = (
        ("Sistema HDB (u1)", "aprovechamiento_hormigon", 0.364),
        ("Acero de pernos en C", "aprovechamiento_acero_C", 0.279),
        ("Perimetro exterior", "aprovechamiento_exterior", 0.194),
    )
    for etiqueta, clave, y in barras:
        porcentaje = solucion.get(clave)
        if porcentaje is None:
            continue
        panel.text(0.06, y, etiqueta, fontsize=9.3, color="#273d52",
                   va="center")
        panel.text(0.94, y, f"{porcentaje:.2f} %", fontsize=9.3, weight="bold",
                   color="#273d52", ha="right", va="center")
        panel.add_patch(Rectangle((0.06, y - 0.029), 0.88, 0.011,
                                  color="#dce4ec", linewidth=0))
        panel.add_patch(Rectangle((0.06, y - 0.029),
                                  0.88 * min(100, max(0, porcentaje)) / 100,
                                  0.011, color="#3681b5", linewidth=0))

    gobierna = solucion.get("comprobacion_gobernante", "No especificada")
    panel.text(0.06, 0.102, "Gobierna: " + gobierna,
               fontsize=9, weight="bold", color="#384e64")
    ved = solucion.get("VEd_kN")
    vr = solucion.get("VEd_max_configuracion")
    if ved is not None and vr is not None:
        panel.text(0.06, 0.060, f"VEd = {ved:.1f} kN  |  Capacidad = {vr / 1000:.1f} kN",
                   fontsize=9, color="#526a7e")
    leyenda = [
        Line2D([0], [0], color="#ba514b", lw=2, linestyle="--", label="Borde libre"),
        Patch(facecolor="#d9a779", edgecolor="#8c5128", label="Pilar"),
        Line2D([0], [0], color="#394d63", lw=3, label="Eje del brazo"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#287ab7",
               markeredgecolor="#173048", markersize=9, label="Perno en zona C"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#e09a3c",
               markeredgecolor="#173048", markersize=9, label="Perno en zona D"),
    ]
    figura.legend(handles=leyenda, loc="lower center", bbox_to_anchor=(0.365, 0.075),
                  ncol=2, frameon=False, fontsize=9)
    figura.text(0.5, 0.018,
               "Esquema de borde ENRASADO. Verificar anclajes, detalle y producto comercial HDB.",
               ha="center", fontsize=8, color="#6b7580")

    if guardar:
        figura.savefig(archivo_png, dpi=220, bbox_inches="tight")
        print(f"PLANO HDB GUARDADO: {archivo_png}")
    if mostrar:
        plt.show()
    return figura, ejes



# Graficar SOLO cuando alguna alternativa haya pasado las comprobaciones.
# La funcion lee primera_solucion; no modifica el resultado del dimensionamiento.
if primera_solucion is not None and (mostrar_grafico or guardar_grafico):
    figura_hdb, ejes_hdb = plotear_hdb_borde(
        primera_solucion, cx, cy,
        mostrar=mostrar_grafico,
        guardar=guardar_grafico,
        archivo_png=nombre_archivo_grafico,
        numerar_brazos=numerar_brazos_grafico
    )
