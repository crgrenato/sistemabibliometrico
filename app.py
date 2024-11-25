from flask import Flask, request, render_template, jsonify
import os
import pandas as pd
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Ruta del archivo Excel con los datos de entrenamiento
EXCEL_FILE_PATH = './training_data/indicadores_entrenamiento4.xlsx'

# Función para cargar y trabajar con celdas específicas
def load_training_data():
    try:
        # Cargar el archivo Excel usando pandas
        training_data = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Hoja1')
        
        # Normalizar el nombre de las columnas para asegurar consistencia
        training_data.columns = training_data.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '')
        
        # Asegurar que 'nombre_de_archivo' esté en el formato esperado
        training_data['nombre_de_archivo'] = training_data['nombre_de_archivo'].str.strip().str.lower().str.replace(' ', '_').str.replace('.pdf', '').str.replace('.', '') + ".pdf"
        
        return training_data

    except Exception as e:
        print(f"Error al cargar los datos de archivo local: {e}")
        return None

# Ruta para cargar la página web
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para procesar los PDFs subidos
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return "No se ha proporcionado un archivo.", 400

    files = request.files.getlist('file')
    analysis_results_list = []

    # Cargar los datos de entrenamiento
    training_data = load_training_data()

    if training_data is None:
        return "No se pudo cargar los datos del archivo Excel.", 500

    for file in files:
        if not file.filename.endswith('.pdf'):
            return f"El archivo {file.filename} no es un PDF válido.", 400

        # Normalizar el nombre del archivo cargado para comparación
        file_name = file.filename.strip().lower().replace(' ', '_')

        # Buscar la fila correspondiente al archivo en el archivo Excel
        matched_row = training_data[training_data['nombre_de_archivo'] == file_name]
        if matched_row.empty:
            return f"El archivo {file_name} no se encuentra en los datos de entrenamiento.", 400

        # Extraer la información de todas las categorías mencionadas y manejar NaN
        analysis_results = matched_row.iloc[0].fillna("").replace({np.nan: ""}).to_dict()

        # Convertir los valores numéricos a porcentajes según el formato del Excel
        for key, value in analysis_results.items():
            if isinstance(value, (int, float)) and key != 'publicacion':  # Excluir el año
                # Convertir el valor a porcentaje y formatear con un decimal
                analysis_results[key] = f"{value * 100:.1f}%"

        # Agregar el nombre del archivo al resultado
        analysis_results['file_name'] = file_name

        # Verificar y asignar el título, año de publicación y universidad, si existen
        analysis_results['title'] = analysis_results.get('titulo', 'No se pudo determinar el título')
        analysis_results['year'] = analysis_results.get('publicacion', 'No se pudo determinar el año')
        analysis_results['university'] = analysis_results.get('universidad', 'No se pudo determinar la universidad')
        
        analysis_results_list.append(analysis_results)

    return jsonify(analysis_results_list)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
