# PUNZONAMIENTO HALFEN HDB - INTERIOR - PRIMERA SOLUCION Y DISTRIBUCION
# Revision: el ciclo de suplementos busca primero un reparto valido de brazos. Script lineal: sin clases, funciones propias ni archivos de entrada.
# Prueba el acero base y despues los suplementos EN EL ORDEN ESCRITO.
# Se detiene en la PRIMERA alternativa que cumple TODOS los controles programados.
# Conserva las ecuaciones y el diametro; admite aumentar brazos por geometria sin cambiar los pernos por brazo.
# Muestra la distribucion SOLO de la alternativa seleccionada.
# No es una validacion completa de proyecto ni una copia del selector de HDB.

from math import pi, sqrt, ceil, isfinite, cos, sin, hypot, atan2, degrees

#%% 1. ENTRADAS DEL PILAR Y LA LOSA
lado_pilar_x_cm = 30.0
lado_pilar_y_cm = 50.0
fuerza_punzonamiento_kN = 600.0       # VEd, ANTES de beta
tipo_pilar = "interior"
espesor_losa_cm = 23.0
resistencia_hormigon_MPa = 25.0
resistencia_acero_losa_MPa = 500.0   # fyk de las barras de la losa
recubrimiento_superior_cm = 3.0

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
phix_suplementario = [0, 12, 16, 16, 20]
sx_suplementario = [0, 15, 15, 20, 20]
phiy_suplementario = [0, 12, 16, 16, 20]
sy_suplementario = [0, 15, 15, 20, 20]

# El canto util se calcula para CADA alternativa. No se introduce manualmente.
# d = min(d_base, d_suplementacion).
# Se considera el armado superior en dos direcciones y dos capas en contacto.
# Si una direccion NO tiene suplemento, se utiliza el diametro base en esa direccion.

# True SOLO para la hipotesis de suplemento efectivo tambien en el exterior.
# Se supone armado uniforme en las bandas eficaces y suficientemente anclado.
# Con False el exterior utiliza UNICAMENTE el armado base (prueba conservadora).
suplemento_hasta_exterior = True

#%% 2. CONFIGURACION HDB QUE SE CONSERVA
# Subconjunto de diametros que usa la empresa, no catalogo completo del fabricante.
diametros_pernos_mm = [12, 16, 20]
diametro_perno_a_detallar_mm = 12
carriles_por_cara = 1       # Minimo a probar por cada cara: empieza con ocho brazos
carriles_por_esquina = 1    # Se mantiene un brazo diagonal en cada esquina
maximo_carriles_por_cara = 5  # Limite de BUSQUEDA, NO limite de la norma
# MODO DE BUSQUEDA EN PLANTA:
# - "equilibrado": mismo numero de carriles en las cuatro caras, con
#   cuatro diagonales. Reproduce la familia 8, 12, 16... de nuestros ejemplos HDB.
# - "independiente": permite mas carriles en las dos caras paralelas a X
#   que en las paralelas a Y (o al reves), probando primero menos brazos.
#   Puede generar un reparto distinto del seleccionado por HDB.
# En ambos casos se comprueban acero C, separaciones y no solape de cabezas.
modo_reparto = "equilibrado"
# Se mantiene el diametro y el numero de pernos por brazo; mC se adapta.
# La EOTA TR 060 (3.1) NO obliga a un unico carril por cara.
# Exige distribucion radial y separaciones tangenciales <= 1.7d y 3.5d.


# 4: se conservan CUATRO pernos por brazo en TODAS las alternativas.
# None: se permite ajustar SOLO las filas D; tambien se buscan los brazos.
pernos_por_carril_fijos = 4

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
beta = 1.15                         # Dato adoptado en el informe, no universal

# IMPORTANTE: 0.12 es el valor IMPRESO en PruebaHDB3.pdf.
# Su base nacional debe justificarse antes de adoptarlo en un proyecto.
# El valor recomendado por TR 060, 2.4.3, es 0.15/gamma_c (0.10 aqui).
C_Rdc_exterior = 0.12
aplicar_beta_red = True
beta_min_exterior = 1.10           # Valor del informe; verificar marco aplicable

# Fuentes para trazabilidad; el script NO las abre ni consulta Internet:
# EOTA TR 060 (2017), 2.3.1, 2.4.1, 2.4.3, 3.1.
# https://www.eota.eu/sites/default/files/uploads/Technical%20reports/eota-tr-060.pdf
# ETA-12/0454, 06-12-2021, producto HDB corrugado, Anexo C2.
# PruebaHDB3.pdf aportado por el usuario: C_Rdc,out=0.12; beta_red=1.10.
# A diferencia del informe, d se calcula para cada alternativa.

#%% 4. VALIDACIONES Y UNIDADES
if tipo_pilar.strip().lower() != "interior":
    raise SystemExit("Esta version solo estudia interiores sin huecos ni recortes.")
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
for cantidad in (carriles_por_cara, carriles_por_esquina):
    if type(cantidad) is not int or cantidad < 0:
        raise SystemExit("Los carriles por cara/esquina deben ser enteros no negativos.")
if carriles_por_cara < 1:
    raise SystemExit("Esta familia requiere al menos un carril por cara.")
if (type(maximo_carriles_por_cara) is not int
        or maximo_carriles_por_cara < carriles_por_cara):
    raise SystemExit("El maximo por cara debe ser entero y no inferior al inicial.")
if modo_reparto not in ("equilibrado", "independiente"):
    raise SystemExit("modo_reparto debe ser 'equilibrado' o 'independiente'.")
if pernos_por_carril_fijos is not None:
    if type(pernos_por_carril_fijos) is not int or not 2 <= pernos_por_carril_fijos <= 100:
        raise SystemExit("Pernos fijos: entero entre 2 y 100, o None. 100 es un limite del script.")
if diametro_perno_a_detallar_mm not in diametros_pernos_mm:
    raise SystemExit("El diametro elegido no esta en la lista de la empresa.")
if diametro_perno_a_detallar_mm not in (10, 12, 14, 16, 20, 25):
    raise SystemExit("El diametro no esta entre los HDB corrugados de esta ETA.")
numero_alternativas = len(phix_suplementario)
if numero_alternativas == 0 or any(len(lista) != numero_alternativas for lista in
        (sx_suplementario, phiy_suplementario, sy_suplementario)):
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
u0 = 2 * (cx + cy)
fuerza_amplificada = beta * VEd
fcd = alpha_cc * fck / gamma_c
fyd_losa = fyk_losa / gamma_s

#%% 5. ARMADO BASE Y CARRILES QUE NO CAMBIAN
area_barra_x = pi * phix**2 / 4
area_barra_y = pi * phiy**2 / 4
acero_base_x = area_barra_x * 1000 / (sx * 10)
acero_base_y = area_barra_y * 1000 / (sy * 10)

# El reparto se construira en cada alternativa.
# Se prueban primero menos brazos, sin fijar una cantidad universal.
# En el modo equilibrado, 1 por cara + 1 diagonal por esquina = 8 brazos.
carriles = []
mC = 4 * (carriles_por_cara + carriles_por_esquina)
diametro_perno = diametro_perno_a_detallar_mm
area_perno = pi * diametro_perno**2 / 4
diametro_cabeza = 3 * diametro_perno
nC = 2                            # Alcance de esta version: dos pernos efectivos en C
# Posiciones, perimetros y resistencias dependientes de d se calculan
# DENTRO del for de suplementos, no aqui.
area_C_colocada = mC * nC * area_perno

print("HDB INTERIOR - SUPLEMENTACION Y BUSQUEDA GENERAL DE BRAZOS")
print(f"mC inicial={mC}; nC={nC}; perno={diametro_perno} mm; beta={beta}")
# Crear lista de repartos, ordenada por total de brazos.
# Cada par (nx, ny) significa:
# nx: carriles en CADA cara paralela a X (caras superior/inferior).
# ny: carriles en CADA cara paralela a Y (caras izquierda/derecha).
# Los carriles diagonales se reparten simetricamente en cada esquina.
candidatos_reparto = []
for nx_prueba in range(carriles_por_cara, maximo_carriles_por_cara + 1):
    for ny_prueba in range(carriles_por_cara, maximo_carriles_por_cara + 1):
        if modo_reparto == "equilibrado" and nx_prueba != ny_prueba:
            continue
        total_prueba = 2 * nx_prueba + 2 * ny_prueba + 4 * carriles_por_esquina
        candidatos_reparto.append((total_prueba, abs(nx_prueba - ny_prueba),
                                    nx_prueba, ny_prueba))
candidatos_reparto.sort()
print("Modo de reparto:", modo_reparto)
print("Candidatos (brazos, sobre caras X, sobre caras Y):",
      [(t, nx, ny) for t, _, nx, ny in candidatos_reparto])
print(f"d_base={d_base:.2f} mm; beta*VEd={fuerza_amplificada / 1000:.2f} kN")
print(f"C_Rdc,out={C_Rdc_exterior}; beta_red activado={aplicar_beta_red}")
print("ATENCION: estos parametros exteriores reproducen el informe, no son universales.")
print("d=min(d_base, d_suplementacion) para cada alternativa; comprobar cotas reales de armadura.")
print("Modo:", "pernos por brazo fijos, brazos adaptables" if pernos_por_carril_fijos is not None
      else "brazos adaptables y ajuste de filas D")
resultados = []                 # Solo alternativas realmente calculadas
primera_solucion = None          # Sigue en None si ninguna cumple
distribucion = []                # Un registro por perno de la solucion elegida

#%% 6. CICLO FOR DE SUPLEMENTOS: BREAK AL CUMPLIR
for i in range(numero_alternativas):
    phi_sup_x = phix_suplementario[i]
    s_sup_x = sx_suplementario[i]
    phi_sup_y = phiy_suplementario[i]
    s_sup_y = sy_suplementario[i]

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
        acero_suplementario_x = pi * phi_sup_x**2 / 4 * 1000 / (s_sup_x * 10)
    if phi_sup_y > 0:
        acero_suplementario_y = pi * phi_sup_y**2 / 4 * 1000 / (s_sup_y * 10)
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
    d = max(d_base, d_suplementacion)
    if not 0 < max(dx, dy, d) < h - r:
        raise SystemExit("Canto util no valido para esta alternativa.")
    if u0 >= 12 * d or max(cx, cy) / min(cx, cy) > 2:
        raise SystemExit("Esta geometria requiere estudiar perimetros reducidos.")

    u1 = u0 + 4 * pi * d
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
    rho_x = acero_losa_por_metro_x / (1000 * dx)
    rho_y = acero_losa_por_metro_y / (1000 * dy)
    rho_geometrica = sqrt(rho_x * rho_y)
    rho = min(rho_geometrica, 0.02, 0.5 * fcd / fyd_losa)
    termino_hormigon = k * (100 * rho * fck)**(1 / 3)
    vRdc = max(C_Rdc * termino_hormigon, vmin)
    vRdmax = factor_maximo_HDB * vRdc

    # No se atribuye al exterior un suplemento que no llegue a ser efectivo alli.
    if suplemento_hasta_exterior:
        rho_exterior = rho
    else:
        rho_exterior = min(sqrt(acero_base_x / (1000 * dx)
                                * acero_base_y / (1000 * dy)), 0.02, 0.5 * fcd / fyd_losa)
    vRdc_exterior = max(C_Rdc_exterior * k * (100 * rho_exterior * fck)**(1 / 3), vmin)
    VEd_max_hormigon = vRdmax * u1 * d / beta

    # Longitud teorica requerida. Biseccion de la comprobacion exterior;
    # no confundir esta longitud con la ultima fila realmente colocada.
    ls_inferior = 0.0
    ls_superior = max(d, (beta * VEd / (vRdc_exterior * d) - u0) / (2 * pi) - 1.5 * d)
    for iteracion in range(70):
        ls_prueba = (ls_inferior + ls_superior) / 2
        beta_prueba = beta
        if aplicar_beta_red:
            beta_prueba = max(beta / (1.2 + beta * ls_prueba / (40 * d)), beta_min_exterior)
        capacidad_prueba = vRdc_exterior * (u0 + 2 * pi * (ls_prueba + 1.5 * d)) * d / beta_prueba
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
    u_out_colocado = u0 + 2 * pi * (ls_colocado + 1.5 * d)
    beta_red = beta
    if aplicar_beta_red:
        beta_red = max(beta / (1.2 + beta * ls_colocado / (40 * d)), beta_min_exterior)
    # Este perimetro necesario usa beta_red de la CONFIGURACION COLOCADA.
    u_out_necesario = beta_red * VEd / (vRdc_exterior * d)
    vEd_exterior = beta_red * VEd / (u_out_colocado * d)
    VEd_max_exterior = vRdc_exterior * u_out_colocado * d / beta_red

    # BUSQUEDA DEL REPARTO. Por cada suplemento probamos diferentes
    # cantidades de brazos en las caras, manteniendo las diagonales.
    # Se mantiene el numero de pernos por brazo dentro de cada alternativa.
    # El filtro de separacion sobre tramos/arcos es el de la version anterior.
    reparto_encontrado = False
    repartos_probados = []
    cumple_hormigon = VEd <= VEd_max_hormigon + 1e-7
    cumple_exterior = VEd <= VEd_max_exterior + 1e-7

    # Las dos caras de una misma direccion reciben igual numero de carriles.
    # Se buscan alternativas siguiendo candidatos_reparto.
    for _, _, carriles_cara_x, carriles_cara_y in candidatos_reparto:
        carriles = []
        # CARAS SUPERIOR E INFERIOR: longitud cx
        for j in range(carriles_cara_x):
            x = -cx / 2 + (j + 0.5) * cx / carriles_cara_x
            carriles.extend([(x, cy / 2, 0.0, 1.0),
                             (x, -cy / 2, 0.0, -1.0)])
        # CARAS DERECHA E IZQUIERDA: longitud cy
        for j in range(carriles_cara_y):
            y = -cy / 2 + (j + 0.5) * cy / carriles_cara_y
            carriles.extend([(cx / 2, y, 1.0, 0.0),
                             (-cx / 2, y, -1.0, 0.0)])
        # DIAGONALES: un abanico de carriles radiales en cada esquina.
        for signo_x, signo_y in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            for j in range(carriles_por_esquina):
                angulo = (j + 0.5) * pi / (2 * carriles_por_esquina)
                carriles.append((signo_x * cx / 2, signo_y * cy / 2,
                                 signo_x * cos(angulo), signo_y * sin(angulo)))

        mC = len(carriles)
        mD = mC if nD > 0 else 0
        pernos_C = mC * nC
        pernos_D = mD * nD
        area_C_colocada = pernos_C * area_perno
        VRd_acero_C = area_C_colocada * fyk_pernos / (gamma_s * eta)
        VEd_max_acero_C = VRd_acero_C / beta
        cumple_acero_C = VEd <= VEd_max_acero_C + 1e-7

        # Separacion tangencial: regla TR 060, apdo 3.1.
        # Medimos tramos + arco redondeado; es conservador frente
        # a la separacion recta entre pernos. Se verifica a r=d y r=ls.
        separaciones_maximas = []
        for radio_control in (d, ls_colocado):
            separaciones = []
            if carriles_cara_x > 1:
                separaciones.append(cx / carriles_cara_x)
            if carriles_cara_y > 1:
                separaciones.append(cy / carriles_cara_y)
            if carriles_por_esquina == 0:
                separaciones.append(cx / (2 * carriles_cara_x)
                                     + cy / (2 * carriles_cara_y)
                                     + pi * radio_control / 2)
            else:
                medio_arco = pi * radio_control / (4 * carriles_por_esquina)
                separaciones.extend([cx / (2 * carriles_cara_x) + medio_arco,
                                      cy / (2 * carriles_cara_y) + medio_arco])
                if carriles_por_esquina > 1:
                    separaciones.append(pi * radio_control / (2 * carriles_por_esquina))
            separaciones_maximas.append(max(separaciones))
        separacion_interior, separacion_exterior = separaciones_maximas

        # Distancia minima entre ejes: evita solapamiento de cabezas.
        coordenadas_pernos = []
        for numero_carril, (x0, y0, ux, uy) in enumerate(carriles, start=1):
            for numero_fila, distancia_pilar in enumerate(posiciones, start=1):
                coordenadas_pernos.append((x0 + distancia_pilar * ux,
                                           y0 + distancia_pilar * uy))
        distancia_minima = float("inf")
        for indice_perno in range(len(coordenadas_pernos)):
            for otro_perno in range(indice_perno + 1, len(coordenadas_pernos)):
                distancia_minima = min(distancia_minima, hypot(
                    coordenadas_pernos[indice_perno][0] - coordenadas_pernos[otro_perno][0],
                    coordenadas_pernos[indice_perno][1] - coordenadas_pernos[otro_perno][1]))
        cumple_geometria = (separacion_interior <= limite_interior + 1e-8
                            and separacion_exterior <= limite_exterior + 1e-8
                            and distancia_minima > diametro_cabeza + 1e-8)

        repartos_probados.append((mC, carriles_cara_x, carriles_cara_y, cumple_acero_C, cumple_geometria))
        if cumple_acero_C and cumple_geometria:
            reparto_encontrado = True
            break

    # El for anterior encuentra la primera propuesta dentro de la familia elegida
    # que cumple acero C y geometria; ahora se comprueban hormigon y exterior.
    cumple = (reparto_encontrado and cumple_hormigon and cumple_acero_C
              and cumple_exterior and cumple_geometria)
    VEd_max_configuracion = min(VEd_max_hormigon, VEd_max_acero_C, VEd_max_exterior)
    if VEd_max_configuracion == VEd_max_acero_C:
        comprobacion_gobernante = "Acero de pernos en C"
    elif VEd_max_configuracion == VEd_max_hormigon:
        comprobacion_gobernante = "Resistencia maxima en u1"
    else:
        comprobacion_gobernante = "Perimetro exterior"

    resultado = {
        "indice": i, "suplemento_x": (phi_sup_x, s_sup_x),
        "carriles_por_cara": carriles_cara_x if carriles_cara_x == carriles_cara_y else None,
        "carriles_cara_x": carriles_cara_x, "carriles_cara_y": carriles_cara_y,
        "reparto_encontrado": reparto_encontrado,
        "repartos_probados": repartos_probados[:],
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
    print(f"VRdc={vRdc * u1 * d / 1000:.3f}; VRdmax={vRdmax * u1 * d / 1000:.3f} kN")
    print(f"Brazos probados (mC, nx, ny, acero_C_ok, geometria_ok): {repartos_probados}")
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
    print("Se exploraron brazos adicionales, pero el diametro se mantuvo fijo.")
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
    print(f"En cada cara paralela a X: {primera_solucion['carriles_cara_x']} brazos; "
          f"paralela a Y: {primera_solucion['carriles_cara_y']} brazos")
    print(f"En cada esquina: {carriles_por_esquina} brazos diagonales")
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
    print("Las diagonales parten de las ESQUINAS del pilar, no de su centro.")
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
    print(f"CAPACIDAD VEd = {VEd_max_configuracion / 1000:.3f} kN "
          f"= {VEd_max_configuracion / 9806.65:.3f} tf")
    print(f"Utilizacion = {100 * VEd / VEd_max_configuracion:.2f} %; "
          f"gobierna: {comprobacion_gobernante}")
    print("Cumple las comprobaciones PROGRAMADAS; quedan las verificaciones de proyecto.")
    print("Se ha elegido la PRIMERA valida en tus listas, no la de menor peso o coste.")

print("\nPENDIENTES: disposicion real y canto util de la armadura suplementaria; bandas eficaces;")
print("continuidad y anclaje mas alla de u_out; justificacion de C_Rdc,out y beta_min;")
print("longitudes comerciales, altura y anclaje de pernos, recubrimientos y hormigonado.")
print("El diametro del perno se mantiene en todas las alternativas.")
if pernos_por_carril_fijos is not None:
    print("Los pernos por brazo son fijos; los brazos pueden aumentar.")
else:
    print("Los pernos D y los brazos pueden aumentar segun la alternativa.")
print("El numero de brazos surge de los limites resistentes y geometricos dentro")
print("de la familia de reparto seleccionada; NO reproduce toda la optimizacion HDB.")
