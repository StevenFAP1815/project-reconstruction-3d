# Conclusiones

Respuesta a cada objetivo de `docs/problem-objectives.md` con los resultados
obtenidos. Las cifras proceden de `docs/master-table.md`, `docs/sfm-results.md`
y `docs/vggt-results.md`.

## Objetivos específicos

| # | Criterio de éxito | Resultado | ¿Se cumple? |
|---|---|---|---|
| OE1 | ≥ 15 vistas y RMS ≤ 0,5 px | 42 vistas, RMS 0,81 px (el moiré de la pantalla limita la detección de esquinas) | Parcial: vistas sí, RMS no |
| OE2 | ≥ 90 % registradas en un modelo, error < 1 px | Solo la caja con `D_calibrada` (100 %, 1 modelo, 1,12 px). Base: caja 63 %, canasto 46 %, audífonos 48 %, colador 9 %, vaso 5 % | Solo en la caja, y sin el umbral de 1 px |
| OE3 | Nube densa limpia y malla en mm con error ≤ 2 %, exportada en .ply/.obj/.glb | Nube densa de VGGT (MVS no concluyó en > 40 min). Mallas exportadas de los 5 objetos; error medio de la malla 4,5–18 %. Medidas individuales ≤ 2 %: ancho de la caja (1,4 %), boca del vaso (1,5 %) | Malla y exportación sí; error ≤ 2 % no |
| OE4 | Tabla comparativa con error, cobertura, tiempo y memoria | Tabla maestra con 16 corridas. COLMAP sin error dimensional, porque no hay nube densa | Parcial: la comparación de precisión métrica solo existe para VGGT |
| OE5 | Fallos con causa verificada y recomendación por objeto | Causas de SfM verificadas con datos (puntos SIFT, inliers, focal). Causas de los errores de VGGT: probables, salvo el apoyo y la franja del canasto, que sí se verificaron | Sí, con las causas de VGGT marcadas como probables |

## Hipótesis

- **H1 (COLMAP reconstruye bien O1 con error ≤ 2 %): no se pudo comprobar.** La
  caja se registró al 100 % con `D_calibrada`, pero su etapa densa no concluyó.
- **H2 (COLMAP falla en materiales difíciles): confirmada.** El registro baja con
  el material: canasto 46 %, colador 9 %, vaso 5 %. La focal del vaso se aleja un
  32,5 % de la calibrada, señal de un modelo degenerado.
- **H3 (VGGT reconstruye los cinco, con más error en los objetos con textura):
  la primera parte se confirma, la segunda no.** VGGT reconstruye los cinco con
  un 100 % de cobertura. Su peor error no está en los objetos con textura, sino
  en el más pequeño (audífonos, 18 %); el vaso tiene la mejor malla (4,5 %).

## Qué método conviene para cada tipo de objeto

| Tipo de objeto | Ejemplo | Recomendación | Motivo |
|---|---|---|---|
| Opaco con textura | Caja | COLMAP si hay GPU y tiempo; VGGT si no | SfM registra el 100 % con intrínsecos calibrados y BA; VGGT da una malla con un 5,5 % de error en 1,5 min de inferencia |
| Patrón repetitivo, estructura fina | Canasto con flores | VGGT | SfM registra el 46 % en 3 modelos que no se pueden unir |
| Transparente | Vaso | VGGT | SfM registra 4 fotos; VGGT reconstruye cuerpo y asa con un 4,5 % de error |
| Metálico calado | Colador | VGGT | SfM registra 8 fotos; VGGT, el objeto completo con un 5,8 % |
| Pequeño y brillante | Audífonos | Ninguno es fiable en mm | SfM, 48 %; VGGT, 18 % de error. Haría falta acercar la cámara o usar más resolución |

## Conclusión general

Con un teléfono y luz ambiental, VGGT fue el único método que reconstruyó los
cinco objetos por todos sus lados, con mallas de 4,5–7 % de error medio en
cuatro de ellos y una inferencia de 84–93 s por objeto. COLMAP depende del
material: solo la caja cumple sus hipótesis, y su etapa densa no es asumible
con la cuota gratuita de GPU. Ningún método alcanzó el 2 % de error medio; la
precisión métrica queda limitada por la resolución de trabajo de VGGT (518 px),
por la escala obtenida con una regla de ± 1 mm y por la superficie de apoyo,
que hubo que eliminar a posteriori.

## Trabajo futuro

- Incluir en la escena una referencia de escala (tablero o marcadores ArUco)
  para no depender de una medida del propio objeto.
- Fotografiar sobre un apoyo rígido y plano, distinto en color del objeto, para
  que la limpieza lo detecte sin ajustes.
- Ejecutar MVS a menor resolución (`max_image_size = 800`) o en una GPU más
  rápida, para comparar en precisión métrica ambos métodos.
- Refinar las cámaras de VGGT con bundle adjustment, que su repositorio ofrece,
  y comprobar si reduce el error dimensional.
