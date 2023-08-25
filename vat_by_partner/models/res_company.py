# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

class ResCompany(models.Model):
    _inherit = 'res.company'

    is_vat_by_partner = fields.Boolean(string='VAT by Partner')