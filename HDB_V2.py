# PUNZONAMIENTO HALFEN HDB - PILAR INTERIOR SIN HUECOS
# Version con reparto simetrico en planta, NO para aprobar un detalle de obra.
# Metodo: EOTA TR 060 (2017) + ETA-12/0454 (06-12-2021).
# Losa maciza no pretensada; carga estatica; sin compresion en su plano.
# Mismo armado SUPERIOR en X e Y, uniforme, anclado y continuo hasta u_out.
# Dos capas superiores ortogonales EN CONTACTO. Sin bordes ni juntas proximos.

from math import pi, sqrt, ceil, isfinite, cos, sin, hypot, atan2, degrees

#%% Entradas
# ============================================================
# 1. Datos a leer del script PUNZONADO
# ============================================================
lado_pilar_x_cm = 30.0
lado_pilar_y_cm = 30.0
fuerza_punzonamiento_kN = 600.0                                                # VEd de calculo, ANTES de aplicar beta
tipo_pilar = "interior"                                                        # Por ahora, resuelto por Leyanis
#diametro_barras_losa_mm = 8.0                                                  # Armado SUPERIOR, igual en X e Y
#separacion_barras_losa_cm = 15.0                                               # Separacion entre ejes de barras
espesor_losa_cm = 23.0
resistencia_hormigon_MPa = 25.0                                                # fck: resistencia cilindrica
resistencia_acero_losa_MPa = 500.0                                             # fyk: NO es fyd ni el acero del perno

# Armado base
phix=8                                                                         # Armado superior en direccion X, mm
sx=15                                                                          # Separacion de armado superior en direccion X, cm
phiy=8                                                                         # Armado superior en direccion Y, mm
sy=15                                                                          # Separacion de armado superior en direccion Y, cm

# Armados complementarios
phix_suplementario=[0,12, 16, 16, 20]                                            # Armado superior en direccion X, mm
sx_suplementario=[0,15, 15, 20, 20]                                              # Separacion de armado superior en direccion X, cm
phiy_suplementario=[0,12, 16, 16, 20]                                            # Armado superior en direccion X, mm
sy_suplementario=[0,15, 15, 20, 20]                                             # Separacion de armado superior en direccion X, cm


# Dato adicional imprescindible para obtener el canto util.
recubrimiento_superior_cm = 3.0                                                # Hasta la superficie de la primera barra

# Compara todos los diametros, pero muestra las coordenadas de este:
diametro_perno_a_detallar_mm = 12                                              # En pausa (revisar despues)

for i in range(len(phix_suplementario)):
    
    # ============================================================
    # 2. Parametros de pernos usados en punzonmaiento industrial
    # ============================================================
    diametros_pernos_mm = [12, 16, 20]                                         # HDB corrugados; no HDB-G; no usamos ni 10 ni 14
    fyk_pernos = 500.0                                                         # MPa. Propiedad del producto, independiente de la losa
    factor_maximo_HDB = 1.96
    
    # LIMITE DE BUSQUEDA del programa, no un maximo normativo.
    maximo_carriles_a_probar = 64                                                  # Para no ir mas alla de este numero
    # Familia propia de reparto: 4, 8, 12, ... carriles simetricos.
    # Igual numero por cada cara e igual numero por cada esquina.
    # No se afirma que sea la unica familia ni la solucion global mas economica.
    
    gamma_c = 1.50           # Situacion persistente/transitoria ordinaria         # No tocar
    gamma_s = 1.15                                                                 # No tocar
    alpha_cc = 1.00          # Valor adoptado para calcular fcd                    # No tocar
    
    # Se conserva 1.15 por ser solo interior.
    # TR 060 recomienda 1.10 para interior salvo indicacion nacional distinta.
    # El uso de beta simplificado exige arriostramiento independiente del
    # portico losa-pilar y luces adyacentes que no difieran mas del 25 %.
    
    if tipo_pilar.strip().lower() == "interior":
        beta = 1.15                                                                # Aqui se meterían los demas betas
    else:
        raise SystemExit("Esta version no calcula pilares de borde ni de esquina.")
    
    #%% Comienzan los calculos
    # ============================================================
    # 3. COMPROBAR DATOS Y CONVERTIR A mm, N Y MPa
    # ============================================================
    for valor in (lado_pilar_x_cm, lado_pilar_y_cm, espesor_losa_cm,
                  phix,sx,phiy,sy,resistencia_hormigon_MPa, resistencia_acero_losa_MPa,
                  recubrimiento_superior_cm):
        if not isfinite(valor) or valor <= 0:
            raise SystemExit("Las dimensiones y resistencias deben ser positivas.")
    
    if not isfinite(fuerza_punzonamiento_kN) or fuerza_punzonamiento_kN < 0:
        raise SystemExit("VEd debe ser un numero finito, mayor o igual que cero.")
    
    cx = lado_pilar_x_cm * 10
    cy = lado_pilar_y_cm * 10
    h = espesor_losa_cm * 10
    r = recubrimiento_superior_cm * 10
    # phi = diametro_barras_losa_mm
    # s = separacion_barras_losa_cm * 10
    VEd = fuerza_punzonamiento_kN * 1000                                           # A Newton
    fck = resistencia_hormigon_MPa
    fyk_losa = resistencia_acero_losa_MPa
    
    if diametro_perno_a_detallar_mm not in diametros_pernos_mm:
        raise SystemExit("El diametro a detallar debe estar en la lista comercial.")
    if (not isinstance(maximo_carriles_a_probar, int)
            or maximo_carriles_a_probar < 4
            or maximo_carriles_a_probar % 4 != 0):
        raise SystemExit("El limite de busqueda debe ser un entero multiplo de 4.")
    
    if h < 180 or not 20 <= fck <= 50:
        raise SystemExit("Fuera del alcance usado: h >= 180 mm y 20 <= fck <= 50 MPa.")
    if sx*10 <= phix or r + 2 * phix >= h:
        raise SystemExit("Revisa separacion, recubrimiento y espesor: geometria imposible.")
    if sy*10 <= phiy or r + 2 * phiy >= h:
        raise SystemExit("Revisa separacion, recubrimiento y espesor: geometria imposible.")
    
    
    # ============================================================
    # 4. CANTO UTIL Y CUANTIA DEL ARMADO SUPERIOR
    # ============================================================
    dx = h - r - max(phix,phix_suplementario[i]) / 2
    dy = h - r - max(phix,phix_suplementario[i]) - max(phiy,phiy_suplementario[i]) / 2
    d = (dx + dy) / 2
    
    area_barra_x = pi * phix**2 / 4+pi * phix_suplementario[i]**2 / 4          # Con i=0, no hay suplementacion
    acero_losa_por_metro_x = area_barra_x * 1000 / sx /10   # mm2/m            # Con i=0, no hay suplementacion. /10 para transformar a cm
    area_barra_y = pi * phiy**2 / 4+pi * phix_suplementario[i]**2 / 4          # Con i=0, no hay suplementacion
    acero_losa_por_metro_y = area_barra_y * 1000 / sy /10   # mm2/m            # Con i=0, no hay suplementacion. /10 para transformar a cm
    
    rho_x = acero_losa_por_metro_x / (1000 * dx)
    rho_y = acero_losa_por_metro_y / (1000 * dy)
    rho_geometrica = sqrt(rho_x * rho_y)
    
    fcd = alpha_cc * fck / gamma_c
    fyd_losa = fyk_losa / gamma_s
    rho = min(rho_geometrica, 0.02, 0.5 * fcd / fyd_losa)
    
    print("\n1. LOSA Y ARMADO SUPERIOR")
    print(f"Canto util medio d = {d:.2f} mm")
    print(f"Acero en direccion = {acero_losa_por_metro_x / 100:.3f} cm2/m")
    print(f"Acero en direccion = {acero_losa_por_metro_y / 100:.3f} cm2/m")
    print(f"Cuantia geometrica = {rho_geometrica:.6f}")
    print(f"Cuantia usada = {rho:.6f}")
    print(f"Beta adoptado = {beta:.2f}; verificar sus condiciones de aplicacion.")
    
    
    # ============================================================
    # 5. PERIMETROS Y SOLICITACION
    # ============================================================
    u0 = 2 * (cx + cy)
    if u0 >= 12 * d or max(cx, cy) / min(cx, cy) > 2:
        raise SystemExit("Este pilar requiere estudiar perimetros reducidos: no incluidos.")
    
    u1 = u0 + 4 * pi * d
    fuerza_amplificada = beta * VEd
    vEd = fuerza_amplificada / (u1 * d)
    
    print("\n2. SOLICITACION")
    print(f"Perimetro u0 = {u0:.2f} mm")
    print(f"Perimetro u1 = {u1:.2f} mm")
    print(f"Beta x VEd = {fuerza_amplificada / 1000:.2f} kN")
    print(f"Tension solicitante vEd = {vEd:.4f} MPa")
    
    
    # ============================================================
    # 6. RESISTENCIA SIN PERNOS Y RESISTENCIA MAXIMA HDB
    # ============================================================
    k = min(2.0, 1 + sqrt(200 / d))
    C_Rdc = 0.18 / gamma_c
    if u0 / d < 4:
        C_Rdc = max(0.15 / gamma_c, (0.18 / gamma_c) * (0.1 * u0 / d + 0.6))
    
    if d <= 600:
        coeficiente_minimo = 0.0525
    elif d >= 800:
        coeficiente_minimo = 0.0375
    else:
        coeficiente_minimo = 0.0525 - (d - 600) * (0.0525 - 0.0375) / 200
    
    vmin = (coeficiente_minimo / gamma_c) * k**1.5 * sqrt(fck)
    termino_hormigon = k * (100 * rho * fck)**(1 / 3)
    vRdc = max(C_Rdc * termino_hormigon, vmin)
    vRdmax = factor_maximo_HDB * vRdc        
    
    print("\n3. RESISTENCIAS")
    print(f"Resistencia sin pernos vRdc = {vRdc:.4f} MPa")
    print(f"Resistencia maxima HDB vRdmax = {vRdmax:.4f} MPa")
    print(f"Utilizacion sin pernos = {100 * vEd / vRdc:.1f} %")
    
    if vEd <= vRdc:
        print("\nEn u1 NO se necesita armadura de punzonamiento.")
        print("No se dimensionan pernos C/D. No se verifican otros estados limite.")
    
    elif vEd > vRdmax:
        print("\nSe SUPERA la resistencia maxima del sistema HDB.")
        print("No se resuelve aumentando el numero o el diametro de los pernos.")  # Aca se determina el uso o no de suplementacion
        print("Se requiere suplementación en el acero superior.")                                       
    
    else:
        print("\nSe NECESITA refuerzo. No se supera la resistencia maxima HDB.")
    
        # ========================================================
        # 7. AREA TOTAL DE PERNOS NECESARIA EN LA ZONA C
        # ========================================================
        eta = max(1.0, min(1.6, 1 + (d - 200) / 1000))
        area_C_necesaria = fuerza_amplificada * gamma_s * eta / fyk_pernos
    
        print("\n4. ACERO NECESARIO EN C")
        print(f"Factor eta = {eta:.3f}")
        print(f"Area total necesaria en C = {area_C_necesaria:.2f} mm2")
    
    
        # ========================================================
        # 8. EXTENSION Y POSICIONES RADIALES C/D
        # ========================================================
        # Misma cuantia longitudinal hasta el exterior; sigma_cp = 0.
        # No se aprovecha reduccion de beta en u_out.
        vRdc_exterior = max((0.15 / gamma_c) * termino_hormigon, vmin)
        u_out_necesario = fuerza_amplificada / (vRdc_exterior * d)
        r_out_necesario = (u_out_necesario - u0) / (2 * pi)
        ls_necesario = max(0.0, r_out_necesario - 1.5 * d)
    
        # ELECCION de esta version: dos pernos efectivos en C por carril.
        # No es un maximo normativo de pernos ni una referencia comercial.
        nC = 2
        separacion_radial = 0.75 * d
        primer_perno_C = 0.375 * d
        ultimo_perno_C = 1.125 * d
        nD = max(0, ceil((ls_necesario - ultimo_perno_C) / separacion_radial))
        posiciones = [primer_perno_C, ultimo_perno_C]
        for fila_D in range(1, nD + 1):
            posiciones.append(ultimo_perno_C + fila_D * separacion_radial)
        ls_colocado = posiciones[-1]
    
        # Familia sin recortes, con la ultima fila en el contorno paralelo
        # a la columna. Expresion del Anexo C2 de ETA-12/0454 (2021).
        u_out_colocado = u0 + 2 * pi * (ls_colocado + 1.5 * d)
        vEd_exterior = fuerza_amplificada / (u_out_colocado * d)
    
        print("\n5. EXTENSION Y FILAS RADIALES")
        print(f"Resistencia exterior = {vRdc_exterior:.4f} MPa")
        print(f"u_out necesario = {u_out_necesario:.2f} mm")
        print(f"ls necesario = {ls_necesario:.2f} mm")
        print(f"Pernos en C por carril = {nC}")
        print(f"Pernos en D por carril prolongado = {nD}")
        for numero, r in enumerate(posiciones, start=1):
            zona = "C" if numero <= nC else "D"
            print(f"Fila {numero}: zona {zona}, distancia al pilar = {r:.2f} mm")
        print(f"u_out colocado, modelo Anexo C2 = {u_out_colocado:.2f} mm")
        print(f"vEd exterior = {vEd_exterior:.4f} MPa")
    
        # ========================================================
        # 9. BUSCAR EL NUMERO DE CARRILES PARA CADA DIAMETRO
        # ========================================================
        # Cada carril se representa con CUATRO numeros:
        # (x0, y0, ux, uy)
        # x0,y0 = punto de partida en la cara/esquina del pilar.
        # ux,uy = direccion unitaria hacia fuera.
        # Coordenadas de un perno a distancia r:
        # x = x0 + r*ux; y = y0 + r*uy.
        # El centro del pilar es (0,0).
        #
        # Se prueba una FAMILIA ELEGIDA POR NOSOTROS, no un catalogo:
        # - carriles normales a cada cara, repartidos uniformemente;
        # - carriles en abanico desde cada esquina, si hacen falta;
        # - las cuatro caras reciben el mismo numero de carriles;
        # - las cuatro esquinas reciben el mismo numero de carriles;
        # - todos los carriles continuan hasta ls: mD = mC si hay D.
        #
        # Los limites de separacion son los de TR 060, apartado 3.1.
        # Se mide por LINEAS Y ARCOS del contorno redondeado (conservador
        # respecto a la distancia recta entre pernos vecinos).
        # Se comprueba a r=d el tramo interior y a r=ls el exterior.
        # No basta con dividir un perimetro total entre el numero de carriles.
        limite_interior = 1.7 * d
        limite_exterior = 3.5 * d
        resumen = []
        detalle = None
    
        print("\n6. COMPARACION DE DIAMETROS Y REPARTOS")
        print("Diametro | Min.acero | Carriles | Pernos C | Pernos D | Total")
    
        for diametro_perno in diametros_pernos_mm:
            area_perno = pi * diametro_perno**2 / 4
            diametro_cabeza = 3 * diametro_perno  # ETA: cabeza = 3 veces vastago
            minimo_por_acero = ceil(area_C_necesaria / (nC * area_perno))
            encontrado = False
    
            # Primero se prueba el menor numero de carriles de esta familia.
            for numero_carriles in range(4, maximo_carriles_a_probar + 1, 4):
                if numero_carriles < minimo_por_acero:
                    continue
    
                # m = 4*carriles_por_cara + 4*carriles_por_esquina.
                # Probamos primero menos carriles diagonales: criterio propio.
                for carriles_por_esquina in range(numero_carriles // 4):
                    carriles_por_cara = numero_carriles // 4 - carriles_por_esquina
                    separaciones_maximas = []
    
                    for radio in (d, ls_colocado):
                        separaciones = []
                        # Entre carriles vecinos sobre una misma cara.
                        if carriles_por_cara > 1:
                            separaciones.append(cx / carriles_por_cara)
                            separaciones.append(cy / carriles_por_cara)
    
                        if carriles_por_esquina == 0:
                            # Rodea una esquina sin ningun carril diagonal.
                            separaciones.append(
                                cx / (2 * carriles_por_cara)
                                + cy / (2 * carriles_por_cara)
                                + pi * radio / 2
                            )
                        else:
                            # Cara -> primer carril del abanico de la esquina.
                            medio_arco = pi * radio / (4 * carriles_por_esquina)
                            separaciones.append(cx / (2 * carriles_por_cara) + medio_arco)
                            separaciones.append(cy / (2 * carriles_por_cara) + medio_arco)
                            # Entre dos carriles de una misma esquina.
                            if carriles_por_esquina > 1:
                                separaciones.append(pi * radio / (2 * carriles_por_esquina))
    
                        separaciones_maximas.append(max(separaciones))
    
                    separacion_interior = separaciones_maximas[0]
                    separacion_exterior = separaciones_maximas[1]
                    if separacion_interior > limite_interior + 1e-8:
                        continue
                    if separacion_exterior > limite_exterior + 1e-8:
                        continue
    
                    # Construir las posiciones de TODOS los carriles.
                    carriles = []
                    for j in range(carriles_por_cara):
                        x = -cx / 2 + (j + 0.5) * cx / carriles_por_cara
                        y = -cy / 2 + (j + 0.5) * cy / carriles_por_cara
                        carriles.append((x, cy / 2, 0.0, 1.0))    # Cara superior
                        carriles.append((cx / 2, y, 1.0, 0.0))    # Cara derecha
                        carriles.append((x, -cy / 2, 0.0, -1.0))  # Cara inferior
                        carriles.append((-cx / 2, y, -1.0, 0.0))  # Cara izquierda
    
                    for signo_x, signo_y in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
                        for j in range(carriles_por_esquina):
                            angulo = (j + 0.5) * pi / (2 * carriles_por_esquina)
                            carriles.append((signo_x * cx / 2, signo_y * cy / 2,
                                             signo_x * cos(angulo), signo_y * sin(angulo)))
    
                    # Descartar SOLAPAMIENTOS FISICOS de cabezas.
                    # Esto NO sustituye separaciones libres por hormigonado,
                    # comprobacion del arido, tolerancias ni choques con las mallas.
                    # En esta familia los carriles se separan al alejarse del pilar;
                    # la distancia minima entre carriles se da en la primera fila.
                    distancia_minima = separacion_radial
                    primeros_pernos = []
                    for x0, y0, ux, uy in carriles:
                        primeros_pernos.append((x0 + primer_perno_C * ux,
                                                 y0 + primer_perno_C * uy))
                    for i in range(len(primeros_pernos)):
                        for j in range(i + 1, len(primeros_pernos)):
                            distancia = hypot(primeros_pernos[i][0] - primeros_pernos[j][0],
                                              primeros_pernos[i][1] - primeros_pernos[j][1])
                            distancia_minima = min(distancia_minima, distancia)
                    if distancia_minima <= diametro_cabeza + 1e-8:
                        continue
    
                    encontrado = True
                    break
    
                if encontrado:
                    break
    
            if not encontrado:
                print(f"{diametro_perno:8.0f} | {minimo_por_acero:9d} | SIN REPARTO EN LA FAMILIA")
                continue
    
            mC = numero_carriles
            mD = mC if nD > 0 else 0
            pernos_C = mC * nC
            pernos_D = mD * nD
            area_C_colocada = pernos_C * area_perno
            VRd_acero_C = area_C_colocada * fyk_pernos / (gamma_s * eta)
    
            print(f"{diametro_perno:8.0f} | {minimo_por_acero:9d} | {mC:8d} |"
                  f" {pernos_C:8d} | {pernos_D:8d} | {pernos_C + pernos_D:5d}")
    
            # Guardamos numeros normales para consultar despues el diametro elegido.
            solucion = {
                "diametro": diametro_perno,
                "minimo_por_acero": minimo_por_acero,
                "mC": mC, "mD": mD, "nC": nC, "nD": nD,
                "pernos_C": pernos_C, "pernos_D": pernos_D,
                "por_cara": carriles_por_cara, "por_esquina": carriles_por_esquina,
                "separacion_interior": separacion_interior,
                "separacion_exterior": separacion_exterior,
                "distancia_minima_centros": distancia_minima,
                "area_C_colocada": area_C_colocada,
                "VRd_acero_C": VRd_acero_C,
                "carriles": carriles,
            }
            resumen.append(solucion)
            if diametro_perno == diametro_perno_a_detallar_mm:
                detalle = solucion
    
        # ========================================================
        # 10. MOSTRAR EL REPARTO DEL DIAMETRO ELEGIDO
        # ========================================================
        print("\n7. REPARTO ELEGIDO PARA MOSTRAR")
        if detalle is None:
            print("No se encontro reparto para el diametro a detallar.")
            print("Esto no demuestra que el producto no sirva: la busqueda es limitada.")
        else:
            print(f"Diametro = {detalle['diametro']} mm")
            print(f"Carriles minimos solo por acero = {detalle['minimo_por_acero']}")
            print(f"Carriles repartidos en C = {detalle['mC']}")
            print(f"Carriles por cada cara = {detalle['por_cara']}")
            print(f"Carriles por cada esquina = {detalle['por_esquina']}")
            print(f"Pernos C = {detalle['mC']} x {nC} = {detalle['pernos_C']}")
            if nD > 0:
                print(f"Carriles prolongados a D = {detalle['mD']}")
                print(f"Pernos D = {detalle['mD']} x {nD} = {detalle['pernos_D']}")
            else:
                print("No se necesitan pernos en D para este caso.")
            print(f"Total de pernos = {detalle['pernos_C'] + detalle['pernos_D']}")
    
            print("\n8. COMPROBACIONES DEL REPARTO")
            print(f"Acero C colocado = {detalle['area_C_colocada']:.2f} mm2")
            print(f"Acero C necesario = {area_C_necesaria:.2f} mm2")
            print(f"Resistencia acero C = {detalle['VRd_acero_C'] / 1000:.2f} kN")
            print(f"Beta x VEd = {fuerza_amplificada / 1000:.2f} kN")
            print(f"Separacion sobre contorno a 1d = {detalle['separacion_interior']:.2f} mm"
                  f" <= {limite_interior:.2f} mm")
            print(f"Separacion sobre contorno de ultima fila = {detalle['separacion_exterior']:.2f} mm"
                  f" <= {limite_exterior:.2f} mm")
            print(f"Separacion radial = {separacion_radial:.2f} mm <= 0.75d")
            print(f"u_out colocado = {u_out_colocado:.2f} mm >= {u_out_necesario:.2f} mm")
            print("Cumple las comprobaciones resistentes y de separacion PROGRAMADAS.")
    
            # ========================================================
            # CAPACIDAD MAXIMA DE ESTA CONFIGURACION FIJA
            # No cambia el diametro, los carriles ni las filas C/D.
            # Todas las fuerzas de este bloque son VEd, ANTES de beta.
            # Se conserva beta tambien en el perimetro exterior.
            # ========================================================
    
            # Limite de resistencia maxima del sistema, en u1.
            VEd_max_hormigon = vRdmax * u1 * d / beta
    
            # Limite del acero en C DEL DIAMETRO ELEGIDO.
            # No usar VRd_acero_C suelto: corresponde al ultimo diametro
            # del bucle, que puede no ser el diametro elegido para detallar.
            VEd_max_acero_C = detalle["VRd_acero_C"] / beta
    
            # Limite del hormigon fuera de la ultima fila COLOCADA.
            VEd_max_exterior = vRdc_exterior * u_out_colocado * d / beta
    
            # Deben cumplirse las tres comprobaciones simultaneamente.
            VEd_max_configuracion = min(
                VEd_max_hormigon,
                VEd_max_acero_C,
                VEd_max_exterior
            )
    
            # Conversion: 1 tonelada-fuerza metrica (tf) = 9806.65 N.
            VEd_max_configuracion_kN = VEd_max_configuracion / 1000
            VEd_max_configuracion_tf = VEd_max_configuracion / 9806.65
            utilizacion_configuracion = VEd / VEd_max_configuracion
    
            if VEd_max_configuracion == VEd_max_exterior:
                comprobacion_gobernante = "Perimetro exterior u_out"
            elif VEd_max_configuracion == VEd_max_hormigon:
                comprobacion_gobernante = "Resistencia maxima HDB en u1"
            else:
                comprobacion_gobernante = "Acero de pernos en zona C"
    
            print("\nCAPACIDAD MAXIMA - CONFIGURACION FIJA")
            print(f"Diametro elegido = {detalle['diametro']:.0f} mm")
            print(f"Carriles C = {detalle['mC']}; pernos C/carril = {nC}")
            print(f"Carriles D = {detalle['mD']}; pernos D/carril = {nD}")
            print(f"Limite sistema HDB = {VEd_max_hormigon / 1000:.3f} kN"
                  f" = {VEd_max_hormigon / 9806.65:.3f} tf")
            print(f"Limite acero C = {VEd_max_acero_C / 1000:.3f} kN"
                  f" = {VEd_max_acero_C / 9806.65:.3f} tf")
            print(f"Limite exterior = {VEd_max_exterior / 1000:.3f} kN"
                  f" = {VEd_max_exterior / 9806.65:.3f} tf")
            print(f"CAPACIDAD VEd = {VEd_max_configuracion_kN:.3f} kN"
                  f" = {VEd_max_configuracion_tf:.3f} tf")
            print(f"Gobierna: {comprobacion_gobernante}")
            print(f"Utilizacion con la fuerza introducida ="
                  f" {100 * utilizacion_configuracion:.2f} %")
            print("Se conserva beta = " + str(beta) + " tambien en u_out.")
            print("Capacidad de CALCULO dentro del modelo programado;")
            print("no es carga caracteristica ni carga experimental de rotura.")
            print("Permanecen las comprobaciones constructivas pendientes.")
    
            print("\n9. COORDENADAS EN PLANTA (mm; origen en el centro del pilar)")
            print("Angulo medido desde +X, en sentido antihorario.")
            for numero, (x0, y0, ux, uy) in enumerate(detalle['carriles'], start=1):
                angulo = degrees(atan2(uy, ux)) % 360
                print(f"Carril {numero:02d}: arranca en ({x0:.2f}, {y0:.2f}),"
                      f" direccion {angulo:.2f} grados")
                for fila, r in enumerate(posiciones, start=1):
                    zona = "C" if fila <= nC else "D"
                    x = x0 + r * ux
                    y = y0 + r * uy
                    print(f"    Perno {fila}: zona {zona}, x={x:.2f}, y={y:.2f}, r={r:.2f}")
    
        print("\nALCANCE Y COMPROBACIONES PENDIENTES")
        print("Reparto simetrico de una familia propia; no es un minimo normativo")
        print("ni una optimizacion de todas las configuraciones HDB posibles.")
        print("Se mantienen TODOS los carriles de C en D: no se optimiza mD por separado.")
        print("mC/mD cuentan brazos; no necesariamente piezas comerciales independientes.")
        print("Solo interior rectangular sin huecos, bordes ni juntas que recorten u_out.")
        print("Falta: altura y anclaje de pernos, recubrimiento inferior, longitudes")
        print("de suministro, compatibilidad con las mallas, tolerancias y hormigonado.")
        print("Confirmar beta, armado longitudinal efectivo/anclado y otras verificaciones.")
        print("Este reparto NO sustituye la revision del detalle constructivo.")
        break
