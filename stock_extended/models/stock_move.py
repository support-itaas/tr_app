# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

class StockMove(models.Model):
    _inherit = 'stock.move'

    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', related='picking_id.operating_unit_id',store=True, copy=False)
    is_account_active = fields.Boolean(string='Account Active',compute='_is_account_active',store=True)

    @api.depends('product_id','product_id.type','product_id.categ_id','date')
    def _is_account_active(self):
        for move_id in self:
            # asdfasdfasdf
            if (move_id._is_in() or move_id._is_out()) and move_id.product_id.type == 'product' and move_id.product_id.categ_id.property_valuation == 'real_time' and move_id.date >= '2021-01-01':
                move_id.is_account_active = True
            else:
                move_id.is_account_active = False


class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    is_aging = fields.Boolean(string='Aging')