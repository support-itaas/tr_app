# © 2019 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2019 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Operating Unit in Purchase",
    "version": "11.0.1.1.0",
    "summary": "An operating unit (OU) is an organizational entity part of a "
               "company",
    "author": "Eficent, "
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/operating-unit",
    "category": "Purchase Management",
    "depends": ["purchase", "account_operating_unit"],
    "data": [
        "security/purchase_security.xml",
        "views/purchase_view.xml",
        "views/purchase_report_view.xml",
    ],
    'installable': True
}
