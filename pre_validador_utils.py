# Borrowed from Asistente-LADM-COL

import os.path
import re
import xml.etree.cElementTree as et


def get_models_from_xtf(xtf_path):
    """
    Get model names from an XTF file. Since XTF can be very large, we follow this strategy:
    1. Parse line by line.
        1.a. Compare parsed line with the regular expression to get the Header Section.
        1.b. If found, stop parsing the XTF file and go to 2. If not found, append the new line to parsed lines and go
            to next line.
    2. Give the Header Section to an XML parser and extract models. Note that we don't give the full XTF file to the XML
       parser because it will read it completely, which may be not optimal.
    :param xtf_path: Path to an XTF file
    :return: List of model names from the XTF
    """
    model_names = list()
    pattern = re.compile(r'(<HEADERSECTION[^>]*.*</HEADERSECTION>)')

    text_found = "<foo/>"
    try:
        with open(xtf_path, 'r') as f:
            lines = ""
            for line in f:
                lines += line
                res = re.search(pattern, lines)
                if res:
                    text_found = str(res.groups()[0])
                    break
    except UnicodeDecodeError as e:
        return False, "El archivo no tiene una codificación válida!"
    except:
        return False, "El archivo no pudo ser parseado!"

    if text_found:
        root = et.fromstring(text_found)
        element = root.find('MODELS')
        if element:
            for sub_element in element:
                if "NAME" in sub_element.attrib:
                    model_names.append(sub_element.attrib["NAME"])

    return True, sorted(model_names)


def __parse_models_from_db_meta_attrs(lst_models):
    """
    Borrowed from Asistente LADM-COL.

    Reads a list of models as saved by ili2db and  returns a dict of model dependencies.
    E.g.:
    INPUT-> ["D_G_C_V2_9_6{ LADM_COL_V1_2 ISO19107_PLANAS_V1} D_SNR_V2_9_6{ LADM_COL_V1_2} D_I_I_V2_9_6{ D_SNR_V2_9_6 D_G_C_V2_9_6}", "LADM_COL_V1_2"]
    OUTPUT-> {'D_G_C_V2_9_6': ['LADM_COL_V1_2', 'ISO19107_PLANAS_V1'], 'D_SNR_V2_9_6': ['LADM_COL_V1_2'], 'D_I_I_V2_9_6': ['D_SNR_V2_9_6', 'D_G_C_V2_9_6'], 'LADM_COL_V1_2': []}
    :param lst_models: The list of values stored in the DB meta attrs model table (column 'modelname').
    :return: Dict of model dependencies.
    """
    model_hierarchy = dict()
    for str_model in lst_models:
        parts = str_model.split("}")
        if len(parts) > 1:  # With dependencies
            for part in parts:
                if part:  # The last element of parts is ''
                    model, dependencies = part.split("{")
                    model_hierarchy[model.strip()] = dependencies.strip().split(" ")
        elif len(parts) == 1:  # No dependencies
            model_hierarchy[parts[0].strip()] = list()

    return model_hierarchy

def get_gpkg_models(cursor):
    # Borrowed from Asistente LADM-COL
    # First go for all models registered in t_ili2db_model
    result = cursor.execute("""SELECT modelname FROM t_ili2db_model;""")
    model_hierarchy = dict()
    if result is not None:
        all_models = [dbm[0] for dbm in result]  # dbm is a tuple: ('models',)
        model_hierarchy = __parse_models_from_db_meta_attrs(all_models)

    # Now go for all models listed in t_ili2db_trafo
    result = cursor.execute("""SELECT distinct substr(iliname, 1, pos-1) AS modelname from
                               (SELECT *, instr(iliname,'.') AS pos FROM t_ili2db_trafo)""")
    trafo_models = list()
    if result is not None:
        trafo_models = [dbm[0] for dbm in result]  # dbm is a tuple: ('models',)

    # Finally, using those obtained from t_ili2db_trafo, go for dependencies found in t_ili2db_model
    dependencies = list()
    for model in trafo_models:
        dependencies.extend(model_hierarchy.get(model, list()))

    res_models = list(set(dependencies + trafo_models))

    return res_models
