# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP Consume Show Stock Onhand',
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
    'depends': ['mrp','stock','base'],
    'data': [

        'views/manufacturing_view.xml',

    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
