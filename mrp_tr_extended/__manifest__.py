# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'TR MRP Function',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Schedule and manage maintenance on machine and tools.',
    'description': """
Maintenance in MRP
==================
* Preventive vs corrective maintenance
* Define different stages for your maintenance requests
* Plan maintenance requests (also recurring preventive)
* Equipments related to workcenters
* MTBF, MTTR, ...
""",
    'depends': ['mrp','stock','base','odoo_process_costing_manufacturing'],
    'data': [
        'security/mrp_security.xml',
        'views/mrp_bom_form_view.xml',
        'views/manufacturing_view.xml',

    ],
    # 'demo': ['data/mrp_maintenance_demo.xml'],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
