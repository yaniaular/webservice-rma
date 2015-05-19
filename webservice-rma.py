import oerplib
from random import *
import random

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
db = raw_input('Do you want to create a new database before continuing? [y/N]:')
if db == 'y':
    oerp.db.drop('admin', 'serial_number')
    print 'CREATING A NEW DATABASE'
    oerp.db.create_database('admin', 'serial_number', True, 'en_US', 'admin')
    oerp.login(database='serial_number')
    module_obj = oerp.get('ir.module.module')
    module_id = module_obj.search([('name', '=', 'rma')])
    module_obj.button_immediate_install(module_id)
else:
    oerp.login(database='serial_number')
res_users_obj = oerp.get('res.users')
user_id = res_users_obj.search([('login', '=', 'admin')])
user = res_users_obj.browse( user_id[0] )
group_technical_id = _get_id_from_xml_id('group_no_one', 'base')[0]
group_stock_id = _get_id_from_xml_id('group_production_lot', 'stock')[0]
group_warehouse_id = _get_id_from_xml_id('group_locations', 'stock')[0]
user.groups_id += [group_technical_id, group_stock_id, group_warehouse_id]
oerp.write_record(user)

company_id = user.company_id.id

warehouse_obj = oerp.get('stock.warehouse')
warehouse_id = warehouse_obj.search([('company_id', '=', company_id)])
warehouse = warehouse_obj.browse( warehouse_id[0] )

pricelist_obj = oerp.get('product.pricelist')
pricelist_id = pricelist_obj.search([('type', '=', 'purchase')])
pricelist = pricelist_obj.browse( pricelist_id[0] )

product_obj = oerp.get('product.product')
purchase_obj = oerp.get('purchase.order')
sale_obj = oerp.get('sale.order')
lot_obj = oerp.get('stock.production.lot')

# oerp.execute('res.company','write',[company_id],{
#     'printer_fiscal':True,
#     'vat_check_vies':True,
#     })

#Creating Purchase Journal
print "Creando ordenes de compra"
# partner_num = 5
# supplier_num = 5
# partner_id = _get_id_from_xml_id('res_partner_' + str(partner_num), 'base')[0]
# supplier_id = _get_id_from_xml_id('res_partner_' + str(supplier_num), 'base')[0]

currency_id = _get_id_from_xml_id('EUR', 'base')[0]
lote_ids = []
for pur in xrange(1, 300):
    partner_num = random.randint(1, 26)
    partner_id = _get_id_from_xml_id('res_partner_' +
                                     str(partner_num), 'base')[0]
    print "Creando orden de compra %s" % pur
    purchase_id = oerp.execute('purchase.order', 'create', {
        'company_id': company_id,
        'partner_id': partner_id,
        'currency_id': currency_id,
        'date_order': '2015-05-08 18:17:05',
        'invoice_method': 'order',
        'location_id': warehouse.wh_input_stock_loc_id.id,
        'name': 'Order ' + str(pur),
        'picking_type_id': warehouse.in_type_id.id,
        'pricelist_id': pricelist.id,
        })

    #num_lines = random.randint(2, 7)
    num_lines = 20
    for line in xrange(1, num_lines):
        prod_num = random.randint(5, 8)
        product_id = _get_id_from_xml_id('product_product_' +
                                         str(prod_num), 'product')[0]
        product = product_obj.browse(product_id)
        oerp.execute('purchase.order.line', 'create',{
            'name': product.name,
            'order_id': purchase_id,
            'product_id': product_id,
            'company_id': company_id,
            'product_qty': 1,
            'price_unit': product.standard_price,
            'date_planned': '2015-05-08',
            })
    oerp.exec_workflow('purchase.order', 'purchase_confirm', purchase_id)
    purchase_brw = purchase_obj.browse(purchase_id)
    for picking in purchase_brw.picking_ids:
        wizard_transfer_id = oerp.execute('stock.transfer_details', 'create', {
            'picking_id': picking.id,
            'sourceloc_id': picking.location_id.id,
            'destinationloc_id': picking.location_dest_id.id,
            })
        for stock_move in picking.move_lines:
            lot_id = oerp.execute('stock.production.lot', 'create', {
                'product_id': stock_move.product_id.id,
                'supplier_id': partner_id,
            })
            lote_ids.append(lot_obj.browse(lot_id))
            oerp.execute('stock.transfer_details_items', 'create', {
                'transfer_id': wizard_transfer_id,
                'product_id': stock_move.product_id.id,
                'quantity': stock_move.product_qty,
                'sourceloc_id': stock_move.location_id.id,
                'destinationloc_id': stock_move.location_dest_id.id,
                'lot_id': lot_id,
                'product_uom_id': stock_move.product_uom.id,
            })
        oerp.execute('stock.transfer_details',
                     'do_detailed_transfer',
                     [wizard_transfer_id])


print "Creando ordenes de venta"
partner_id = _get_id_from_xml_id('res_partner_26', 'base')[0]
num_lot = 0
for sale in xrange(1, 300):
    print "Creando orden de sale %s" % sale
    sale_id = oerp.execute('sale.order', 'create', {
        'company_id': company_id,
        'partner_id': partner_id,
        'currency_id': currency_id,
        'date_order': '2015-05-08 18:17:05',
        'order_policy': 'manual',
        'picking_policy': 'direct',
        'location_id': warehouse.wh_input_stock_loc_id.id,
        'warehouse_id': warehouse.id,
        })

    # num_lines = random.randint(2, 4)
    num_lines = 20
    sale_lot_lines = []
    print "*" * 100
    print "Length %s " % len(lote_ids)
    print "*" * 100
    for line in xrange(1, num_lines):
        print "Num Lot %s, Linea %s, Orden %s, Producto %s, Lote %s" % (num_lot, sale, line, lote_ids[num_lot].product_id.name,
                                      lote_ids[num_lot].id)
        product = lote_ids[num_lot].product_id
        sale_lot_lines.append((lote_ids[num_lot].product_id.id,
                               lote_ids[num_lot].id))
        num_lot += 1
        if num_lot > len(lote_ids):
            exit
        oerp.execute('sale.order.line', 'create', {
            'name': product.name,
            'delay': 0,
            'order_id': sale_id,
            'company_id': company_id,
            'price_unit': product.standard_price,
            'product_uom': product.uom_id.id,
            'product_id': product.id,
            'product_uom_qty': 1,
            })
        oerp.execute('sale.order', 'action_button_confirm', [sale_id])
    sale_brw = sale_obj.browse(sale_id)
    for picking in sale_brw.picking_ids:
        wizard_transfer_id = oerp.execute('stock.transfer_details', 'create', {
            'picking_id': picking.id,
            'sourceloc_id': picking.location_id.id,
            'destinationloc_id': picking.location_dest_id.id,
            })

        for stock_move in picking.move_lines:
            for lote in sale_lot_lines:
                if lote[0] == stock_move.product_id.id:
                    lote_to_use_id = lote[1]
                    sale_lot_lines.remove(lote)
                    break
            item = {
                'transfer_id': wizard_transfer_id,
                'product_id': stock_move.product_id.id,
                'quantity': 1,
                'sourceloc_id': stock_move.location_id.id,
                'destinationloc_id': stock_move.location_dest_id.id,
                'lot_id': lote_to_use_id,
                'product_uom_id': stock_move.product_uom.id,
            }
            oerp.execute('stock.transfer_details_items', 'create', item)

        oerp.execute('stock.transfer_details', 'do_detailed_transfer', [wizard_transfer_id])

        wizard_invoice_id = oerp.execute('sale.advance.payment.inv', 'create',{
            'advance_payment_method': 'all',
            },
                     {
                        'active_model': 'sale.order',
                        'active_ids': [sale_id],
                        'active_id': sale_id,
                     })
        oerp.execute('sale.advance.payment.inv', 'create_invoices',
                     [wizard_invoice_id],
                     {
                        'active_model': 'sale.order',
                        'active_ids': [sale_id],
                        'active_id': sale_id,
                     })
    for invoice_id in sale_brw.invoice_ids:
        oerp.exec_workflow('account.invoice', 'invoice_open', invoice_id.id)
