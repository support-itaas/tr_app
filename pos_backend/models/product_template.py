# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_line_ids = fields.One2many('product.package', 'package_id', string='Package Lines')





class ProductPackage(models.Model):
    _name = 'product.package'

    package_id = fields.Many2one('product.template', string='Package Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    product_id = fields.Many2one('product.template', string='Product',required=True,)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    product_uom_qty = fields.Float('Qty', default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                                   required=True)
    @api.onchange('product_id')
    def on_product(self):
        if self:
            self.product_uom = self.product_id.uom_id.id

