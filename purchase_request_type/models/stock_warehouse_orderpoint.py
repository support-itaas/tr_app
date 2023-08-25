# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    request_type = fields.Many2one('purchase.request.type', string="Purchase Request Type")
    purchase_type = fields.Many2one('purchase.type', string="Purchase Type")