# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP Repair sequence',
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
    'depends': ['quality_mrp', 'maintenance','mrp_repair'],
    'data': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
