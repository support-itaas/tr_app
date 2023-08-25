# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class CouponLine(models.Model):
    _name = 'coupon.line'

    package_id = fields.Many2one('product.template', string='Package Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    product_id = fields.Many2one('product.template', string='Product',required=True,)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    product_uom_qty = fields.Float('Qty', default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                                   required=True)


