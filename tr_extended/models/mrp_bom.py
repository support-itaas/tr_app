# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64

class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    permission_type = fields.Selection([('machine', 'Machine'), ('cleanser', 'Cleanser')], string='Type')

    bom_description_line_ids = fields.One2many('bom.description.line', 'description_id', string=' Process Description')

class bom_description(models.Model):
    _name = "bom.description.line"
    _description = "Process Description"

    description_id = fields.Many2one('mrp.bom', string='Description ID')
    # main_product_id = fields.Many2one('product.product', string='Product', required=True)
    # opt_product_id = fields.Many2one('product.template', string='Optional Product', required=True)
    description = fields.Text(string='Description', required=True)
    # product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    # price_unit = fields.Float('Unit Price', required=True)

