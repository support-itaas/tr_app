# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models


class ProductPack(models.Model):
    _name = "product.pack"
    _description = "Product packs"

    @api.multi
    @api.onchange('product_id')
    def product_id_onchange(self):
        return {'domain': {'product_id': [('is_pack', '=', False)]}}

    name = fields.Char('name')
    product_template_id = fields.Many2one('product.template', 'Item')
    product_quantity = fields.Float('Quantity', default='1', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id')
    price = fields.Float('Product Price')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_pack = fields.Boolean('Combo/Pack', default=False)
    is_deliverable_product = fields.Boolean('Deliverable Product?', default=False)
    product_pack_id = fields.One2many('product.pack', 'product_template_id', 'Items in the pack')

