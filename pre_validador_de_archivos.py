import os.path
import shutil
import tempfile
import zipfile

import sqlite3

from pre_validador_utils import (get_models_from_xtf,
                                 get_gpkg_models)

# At least one of these is required!
LADMCOL_MODEL_NAMES = ['Modelo_Aplicacion_LADMCOL_Lev_Cat_V1_2', 'Modelo_Aplicacion_LADMCOL_RIC_V0_1']


def pre_validar_archivo(path):
    if not os.path.exists(path):
        return False, "El archivo no existe!"

    extension = __get_extension(path)

    if extension == '.zip':
        return pre_validar_zip(path)
    elif extension == '.xtf':
        return pre_validar_xtf(path)
    elif extension == '.gpkg':
        return pre_validar_gpkg(path)
    else:
        return False, "Extensión de archivo inválida ('{}').".format(extension)
        
def pre_validar_zip(path):
    # Tiene un solo archivo dentro?
    # El archivo tiene extensión válida?
    # Permite descomprimir?
    # Preguntar a otro método...
    tmp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path, "r") as z:
            in_files = z.namelist()
            print(in_files)
            if len(in_files) > 1:
                return False, "Hay más de un archivo dentro del ZIP ('{}')!".format(path)
            elif len(in_files) == 0:
                return False, "No hay archivos dentro del ZIP ('{}')!".format(path)
            
            extension = __get_extension(in_files[0])
            if extension not in ['.xtf', '.gpkg']:
                return False, "La extensión del archivo dentro del ZIP es inválida ('{}').".format(extension)
            
            z.extractall(tmp_dir)
    except zipfile.BadZipFile as e:
        return False, "Problema al descomprimir el archivo ZIP ('{}')! Detalle: {}".format(path, e)
        
    res, msg = pre_validar_archivo(os.path.join(tmp_dir, in_files[0]))
    try:
        shutil.rmtree(tmp_dir)  # Remove the directory and its file
    except:
        print("WARNING: Carpeta no borrada! ('{}')".format(tmp_dir))
    
    return res, msg
        
def pre_validar_xtf(path):
    # XML?
    # Tags requeridos?
    # Modelos requeridos?
    res, models = get_models_from_xtf(path)
    #print(models)
    
    if res:
        count = 0
        for model in LADMCOL_MODEL_NAMES:
            if model not in models:
                count += 1

        if count == len(LADMCOL_MODEL_NAMES):
            return False, "¡El archivo XTF no incluye el modelo LADM-COL requerido ('{}')!".format("', '".join(LADMCOL_MODEL_NAMES))
    else:
        return res, models
    
    return True, "Archivo pre-válido!"

def pre_validar_gpkg(path):
    # Es un GPKG?
    # Tiene tablas de metadatos de ili2db o coinciden los nombres de tablas?
    conn = sqlite3.connect(path)
    c = conn.cursor()
    try:
        # Source: https://github.com/OSGeo/gdal/blob/master/swig/python/gdal-utils/osgeo_utils/samples/validate_gpkg.py
        # SQLITE 3?
        c.execute('SELECT 1 FROM sqlite_master')
        if c.fetchone() is None:
            return False, "El archivo no es una base de datos SQLite3!"

        # GPKG?
        c.execute("SELECT 1 FROM sqlite_master WHERE "
                  "name = 'gpkg_spatial_ref_sys'")
        if c.fetchone() is None:
            return False, "La BD GeoPackage no tiene tabla de sistemas de referencia!"

        # INTERLIS?
        c.execute("SELECT * FROM sqlite_master WHERE "
                  "name = 'T_ILI2DB_MODEL'")
        if c.fetchone() is None:
            return False, "La BD GeoPackage no tiene estructura INTERLIS!"

        # Modelo?
        models = get_gpkg_models(c)
        # print(models)
        count = 0
        for model in LADMCOL_MODEL_NAMES:
            if model not in models:
                count += 1

        if count == len(LADMCOL_MODEL_NAMES):
            return False, "¡La BD GeoPackage no incluye el modelo LADM-COL requerido ('{}')!".format("', '".join(LADMCOL_MODEL_NAMES))
        #print(c.fetchone())
    except:
        return False, "Problema accediendo a la GPKG."
    finally:
        c.close()
        conn.close()

    return True, "Archivo pre-válido!"

def __get_extension(path):
    return os.path.splitext(path)[1].lower()


if __name__ == '__main__':
    pre_path = os.path.dirname(os.path.abspath(__file__))
    
    def abs_path(rel_path):
        os.path.join(pre_path, rel_path)
    
    def do_assert(archivo):
        res, msg = pre_validar_archivo(archivo)
        print(msg)
        return res
    
    def assert_true(archivo):
        assert do_assert(archivo)
    
    def assert_false(archivo):
        assert not do_assert(archivo)

    # -------------------ZIP------------------------
    print("INFO: Probando ZIPs...")
    assert_false('data/zip/no_archivos.zip')
    assert_false('data/zip/multiples_archivos.zip')
    assert_false('data/zip/archivo_de_texto_txt.zip')
    assert_false('data/zip/archivo_de_texto_xtf.zip')
    assert_true('data/zip/datos_de_prueba_lev_cat_1_0.zip')

    # -------------------XTF------------------------
    print("\nINFO: Probando XTFs...")
    assert_false('')
    assert_false('data/xtf/inexistente.xtf')
    assert_false('data/xtf/archivo_de_texto.txt')
    assert_false('data/xtf/archivo_imagen.xtf')
    assert_false('data/xtf/archivo_xml.xtf')
    assert_false('data/xtf/archivo_de_texto.xtf')
    assert_false('data/xtf/ilivalidator_errors.xtf')
    assert_false('data/xtf/lev_cat_1_2_valido_01.xtf')
    assert_false('data/xtf/lev_cat_1_2_invalido_01.xtf')
    assert_true('data/xtf/datos_de_prueba_lev_cat_1_0.xtf')

    # -------------------GPKG------------------------
    print("\nINFO: Probando GPKGs...")
    assert_false('data/gpkg/archivo_de_texto.gpkg')
    assert_false('data/gpkg/sqlite.gpkg')
    assert_false('data/gpkg/no_interlis.gpkg')
    assert_false('data/gpkg/interlis_no_modelo.gpkg')
    assert_true('data/gpkg/valida_1_0.gpkg')
    assert_false('data/gpkg/valida_1_2.gpkg')
   
    print('\nAll tests passed!')
