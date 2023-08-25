# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_type = fields.Many2one('purchase.order.type', string='Purchase Order Type')

