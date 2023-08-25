
from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_special = fields.Boolean('Is Special')
