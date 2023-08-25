# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class Stock_move(models.Model):
    _inherit = 'stock.move'

    invoice_stock_picking = fields.Many2one('account.invoice',string='Invoice',related='picking_id.invoice_id',store=True)
    categ_id = fields.Many2one('product.category',related='product_id.categ_id',store=True)
