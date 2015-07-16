import oerplib
from random import *
import random

DB = 'rma_demo'
NUM_SALE  = 5
NUM_PURCHASE = 5
MODULES_TO_INSTALL = ['rma', 'yoytec_customer_rma_workflow']

def _get_id_from_xml_id(xml_id, module):
    """
    Returns id of object to get
    @param xml_id: xml id of the object to which you want to find the id
    @param relation_model_str: model of the object to which you want to find the xml id
    @param ir_model_data_obj: object of ids xml table
    """

    ir_model_data_obj = oerp.get('ir.model.data')
    xml_id_list = ir_model_data_obj.search(
        [('name', '=', xml_id), ('module', '=', module)])
    if xml_id_list:
        res_id = ir_model_data_obj.read(xml_id_list[0], ['res_id'])
        res_id = [res_id.get('res_id')]
    else:
        res_id = []
    return res_id

oerp = oerplib.OERP()
oerp.config['timeout']=4000
oerp.login(database=DB)


product_obj = oerp.get('product.product')

for prod_num in xrange(2, 14):
    product_id = _get_id_from_xml_id('product_product_' +
                                        str(prod_num), 'product')[0]
    product = product_obj.browse(product_id)
    product.warranty = 5.0
    oerp.write_record(product)
