import streamlit as st
from PIL import Image
import numpy as np
import cv2
import yaml
import os
from streamlit_drawable_canvas import st_canvas
import pandas as pd


# Cargar las dos imágenes desde los archivos
plano_path = "Track_linea_de_caja\Planta_CF_9cam.jpg"
if plano_path:
    imagen1 = Image.open(plano_path)

imagen_path = "Track_linea_de_caja\camera65_640x480_20240307_090341.mp4_640x480.jpg"
if imagen_path:
    imagen2 = Image.open(imagen_path)


#####################################
# Funciones para mapping con opencv #
#####################################
def mapping_opencv(puntos_cam, puntos_plano_planta):
    global plano_path, imagen_path
    # Convertir los puntos a numpy array
    puntos_de_cam = np.float32([puntos_cam])
    puntos_de_planta = np.float32([puntos_plano_planta])

    # Calcular la matriz de transformación (perspectiva)
    # M = cv2.getPerspectiveTransform(
    #     puntos_de_cam, puntos_de_planta, solveMethod=0
    # )  #'method == DECOMP_LU || method == DECOMP_SVD || method == DECOMP_EIG || method == DECOMP_CHOLESKY || method == DECOMP_QR'

    M, mask = cv2.findHomography(puntos_de_cam, puntos_de_planta, cv2.RANSAC, 5.0)

    print(f"matriz_transformacion {M}")

    # crear un diccionario para guardar la matriz de transformación respectiva a la camara
    cam_id = imagen_path.split("/")[-1].replace(".jpg", "")
    cam_ref_point = f"{cam_id}_ref"
    camera_config = {cam_id: M.tolist(), cam_ref_point: "center"}

    # Guardar la matriz en un archivo YAML
    with open(imagen_path.replace(".jpg", ".yaml"), "w") as archivo_yaml:
        yaml.dump(camera_config, archivo_yaml)
    return M


def obtener_coordenadas_vertices(diccionario_svg):
    coordenadas_vertices = []

    for comando, *coordenadas in diccionario_svg:
        if comando == "M" or comando == "L":
            coordenadas_vertices.append([coordenadas[0], coordenadas[1]])

    return coordenadas_vertices


# Specify canvas parameters in application
drawing_mode = st.sidebar.selectbox(
    "Drawing tool:",
    ("polygon",),  # "point", "freedraw", "line", "rect", "circle", "transform",
)
stroke_color = st.sidebar.color_picker("Stroke color hex: ")
bg_color = st.sidebar.color_picker("Background color hex: ", "#eee")
bg_image_p = st.sidebar.file_uploader("Image Plane:", type=["png", "jpg"])
bg_image_c = st.sidebar.file_uploader("Image Camera:", type=["png", "jpg"])
realtime_update = st.sidebar.checkbox("Update in realtime", True)

# Visualizar las imágenes en la barra lateral
if imagen1 and imagen2:
    # st.sidebar.image(imagen1, caption="Imagen de plano", use_column_width=True)
    # st.sidebar.image(imagen2, caption="Imagen de cámara", use_column_width=True)

    # Variables para almacenar los puntos de mapeo de cada imagen
    puntos_planta = []
    puntos_cam = []

    # Widget para dibujar polígonos en la imagen de plano
    st.subheader("Dibujar polígonos en la imagen de plano")
    drawing_plano = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Color de relleno con cierta opacidad
        stroke_width=2,  # Ancho del trazo
        stroke_color="rgb(255, 0, 0)",  # Color del trazo (rojo)
        background_image=imagen1,
        drawing_mode="polygon",
        key="canvas_plano",
        width=imagen1.width,
        height=imagen1.height,
    )

    if (
        drawing_plano.json_data is not None
        and "objects" in drawing_plano.json_data
        and len(drawing_plano.json_data["objects"]) > 0
    ):
        objects = pd.json_normalize(drawing_plano.json_data["objects"])

        # Extraer los puntos del polígono de la lista de puntos en la sublista "path"
        points_plano = objects["path"].iloc[0]
        points_plano = obtener_coordenadas_vertices(points_plano)
        print(f"points_plano {points_plano}")

    else:
        points_plano = None

    # Widget para dibujar polígonos en la imagen de la cámara
    st.subheader("Dibujar polígonos en la imagen de cámara")
    # st.expander("Dibuja el polígono en la imagen de plano")
    drawing_cam = st_canvas(
        fill_color="rgba(0, 255, 0, 0.3)",  # Color de relleno con cierta opacidad
        stroke_width=2,  # Ancho del trazo
        stroke_color="rgb(0, 255, 0)",  # Color del trazo (verde)
        background_image=imagen2,
        drawing_mode="polygon",
        key="canvas_cam",
        width=imagen2.width,
        height=imagen2.height,
    )

    if (
        drawing_cam.json_data is not None
        and "objects" in drawing_cam.json_data
        and len(drawing_cam.json_data["objects"]) > 0
    ):
        objects = pd.json_normalize(drawing_cam.json_data["objects"])

        # Extraer los puntos del polígono de la lista de puntos en la sublista "path"
        points_cam = objects["path"].iloc[0]
        points_cam = obtener_coordenadas_vertices(points_cam)
        print(f"points_plano {points_cam}")
    else:
        points_cam = None

    # Widget para mapear los puntos
    mapear_puntos = st.sidebar.button("Mapear puntos")
    if mapear_puntos and len(points_cam) == len(points_plano):
        M = mapping_opencv(points_cam, points_plano)
        print(f"M {M}")

    # Widget para borrar todos los puntos
    borrar_puntos = st.sidebar.button("Borrar todos los puntos")
    if borrar_puntos:
        drawing_plano.json_data = None
        drawing_cam.json_data = None
        st.write("Puntos borrados.")

    # Widget para imprimir los puntos en consola
    imprimir_puntos = st.sidebar.button("Imprimir puntos en consola")
    if imprimir_puntos:
        st.write("Puntos en plano:", points_plano)
        st.write("Puntos en cámara:", points_cam)
