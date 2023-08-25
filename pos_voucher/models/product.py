from odoo import api, fields, models, _
from odoo.exceptions import UserError

class product_template(models.Model):
    _inherit = 'product.template'

    is_voucher = fields.Boolean('Is voucher', default=0)