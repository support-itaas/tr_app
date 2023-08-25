# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).

from odoo import models, fields, api


class Picking(models.Model):
    _inherit = 'stock.picking'

    demo_sale_id = fields.Many2one('sale.order', 'Sale Order')



