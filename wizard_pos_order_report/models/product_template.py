# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare



class product_template(models.Model):
    _inherit = 'product.template'

    select_stock_bom = fields.Boolean(string='Show Stock Bom', default=False)
    # meter_type = fields.Selection([
    #     ('p1', "P1"),
    #     ('p2', "P2"),
    #     ('p3', "P3"),
    #     ('p4', "P4"),
    #     ('p5', "ล้างรถรวม"),
    #     ('p6', "ดูดฝุ่น 1"),
    #     ('p7', "ดูดฝุ่น 2"),
    #     ('p8', "ซักพรม"),
    # ], string="Meter Type")
    meter_type = fields.Many2many('meter.type', string="Meter Type")
