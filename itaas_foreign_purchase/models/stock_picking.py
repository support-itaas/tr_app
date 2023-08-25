# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api


class Picking(models.Model):
    _inherit = 'stock.picking'

    exchange_rate = fields.Float('Exchange Rate', digits=(12, 6), readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
