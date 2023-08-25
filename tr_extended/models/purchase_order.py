# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class Purchase_Order(models.Model):
    _inherit = "purchase.order"

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',track_visibility=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, hange_default=True, track_visibility=False)

    # 11-09-2019
    # @api.depends('purchase_type')
    # def _compute_purchase_type(self):
    #     for po in self:
    #         matrix_id = self.env['purchase.approval.matrix'].search(
    #             [('purchase_type', '=', po.purchase_type.id), ('type', '=', 'PO')], limit=1)
    #         po.matrix_id = matrix_id.id

class Purchase_Order_line(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange('product_id')
    def product_id_change_name(self):
        print("onchange_product_id_name")
        for line in self:
            print(self.product_id.name)
            line.update({'name': self.product_id.name, })