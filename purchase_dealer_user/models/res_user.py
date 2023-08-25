# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class res_users(models.Model):
    _inherit = 'res.users'

    order_type = fields.Many2one('purchase.order.type', string='Purchase Order Type')
    purchase_type = fields.Many2one('purchase.type', string='Purchase Type')