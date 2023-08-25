# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Purchase Request Extended",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "version": "11.0.1.2.0",
    "summary": "Use this module to have notification of requirements of "
               "materials and/or external services and keep track of such "
               "requirements.",
    "category": "Purchase Management",
    "depends": [
        "purchase",
        "purchase_request"
    ],
    "data": [
        "views/purchase_request_line_make_purchase_order_view.xml",
    ],
    "license": 'LGPL-3',
    'installable': True,
    'application': True,
}
