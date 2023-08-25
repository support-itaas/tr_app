# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  ITtaas.
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.rrule import (YEARLY,MONTHLY,WEEKLY,DAILY)
from datetime import datetime, timedelta, date
from pytz import timezone
import pytz
import calendar

import uuid

from datetime import datetime, timedelta


class pos_config_inherit(models.Model):
    _inherit = "pos.config"

    is_ignore_account = fields.Boolean(string='No Post to Account')


# class pos_order_inherit(models.Model):
#     _inherit = "pos.order"
#
#     amount_untaxed = fields.Float(string='Untaxed Amount', readonly=True, compute='_compute_sum_untaxed')
#
#     @api.depends('lines.price_subtotal')
#     def _compute_sum_untaxed(self):
#         for obj in self:
#             sum_untaxed = 0.0
#             for line in obj.lines:
#                 sum_untaxed += line.price_subtotal
#             obj.amount_untaxed = sum_untaxed












