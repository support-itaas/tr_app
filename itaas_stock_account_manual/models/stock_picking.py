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

class stock_picking_advance(models.TransientModel):
    _name = "stock.picking.advance"


    def action_cancel(self):
        context = self._context
        stock_ping_ids = self.env['stock.picking'].browse(context['active_ids'])
        for stock_picking in stock_ping_ids.filtered(lambda m: m.state != 'done'):
            stock_picking.action_cancel()

