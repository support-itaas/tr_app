# -*- coding: utf-8 -*-
from bahttext import bahttext

from odoo import api, models, fields
from datetime import datetime
from odoo.exceptions import UserError
from num2words import num2words
import operator
import pytz

class hr_period_report(models.Model):
    _inherit = 'hr.period'

    def baht_text(self, amount):
        return bahttext(amount)

class bahttxt_hr_employee(models.Model):
    _inherit = 'hr.employee'

    def baht_text(self, amount):
        return bahttext(amount)
