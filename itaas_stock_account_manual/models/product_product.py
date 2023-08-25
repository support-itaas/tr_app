# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class product_product(models.Model):
    _inherit = 'product.product'

    # def update_standard_cost(self):
    #     print (x)
        # stock_move_ids = self.env['stock.move'].search([('state','=','done'),('product_id','=',self.id)])
        # for stock_move in stock_move_ids:
        #     if stock_move._is_in():
        #         all_qty += stock_move.product_uom_qty
        #         all_value += stock_move.value
        #     if stock_move._is_out():