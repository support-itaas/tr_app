# -*- coding: utf-8 -*-

{
    'name': 'TR Extended',
    'version': '11.0.1.5',
    'category': 'Apps',
    'summary': "TR Functions",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': [
        'product','sale','purchase','base','account','mrp','stock','thai_accounting','bi_material_purchase_requisitions','hr','purchase_request'],
    'data': [

        'security/security_group.xml',
        'security/ir.model.access.csv',
        'views/material_purchase_requisition_view.xml',
        'views/hr_holidays_view.xml',
        'views/res_partner_view.xml',
        'views/stock_picking_view.xml',
        'views/hr_contract_views.xml',
        'views/view_bom_mrp.xml',
        'views/view_mrp_production.xml',
        # 'views/mrp_bom_form_view.xml',
        # 'views/partner_form_view.xml',
        # 'views/mrp_bom_form_view_conf.xml',
        # 'views/mrp_production_form_view.xml',
        'views/invoice_form_customer_inherit.xml',

        'views/view_stock_move_tree_inherit.xml',
        'views/hr_equipment_request_view_form.xml',
        'views/view_repair_order_form.xml',
        # Add by Book 19/11/2019 ಠ_ಠ
        'views/purchase_order_tree.xml',
        'views/view_purchase_order_filter.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
