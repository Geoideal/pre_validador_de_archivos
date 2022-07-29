import os.path

from pre_validador_utils import get_models_from_xtf

# At least one of these is required!
LADMCOL_MODEL_NAMES = ['Modelo_Aplicacion_LADMCOL_Lev_Cat_V1_0']


def pre_validar_archivo(path):
    if not os.path.exists(path):
        return False, "El archivo no existe!"

    extension = os.path.splitext(path)[1].lower()

    if extension == '.zip':
        return pre_validar_zip(path)
    elif extension == '.xtf':
        return pre_validar_xtf(path)
    elif extension == '.gpkg':
        return pre_validar_gpkg(path)
    else:
        return False, "Extensión de archivo inválida ('{}').".format(extension)
        
def pre_validar_zip(path):
    # Permite descomprimir?
    # Tiene un solo archivo dentro?
    # El archivo tiene extensión válida?
    # Preguntar a otro método...
    pass

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
            return False, "El archivo no incluye el modelo base LADM-COL!"
    else:
        return res, models
    
    return True, "Archivo pré-válido!"

def pre_validar_gpkg(path):
    # Es un GPKG?
    # Tiene tablas de metadatos de ili2db o coinciden los nombres de tablas?
    pass



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

    assert_false('')
    assert_false('data/inexistente.xtf')
    assert_false('data/archivo_de_texto.txt')
    assert_false('data/archivo_imagen.xtf')
    assert_false('data/archivo_xml.xtf')
    assert_false('data/archivo_de_texto.xtf')
    assert_false('data/ilivalidator_errors.xtf')
    assert_false('data/lev_cat_1_2_valido_01.xtf')
    assert_false('data/lev_cat_1_2_invalido_01.xtf')
    assert_true('data/datos_de_prueba_lev_cat_1_0.xtf')
   
    print('Tests passed!')
