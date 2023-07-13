# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    required_customer = fields.Boolean(string="Customer Required", default=False)
    type = fields.Selection([
        ('all_products', 'All Products'),
        ('t_service', 'Service')], default="all_products")
