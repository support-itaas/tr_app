#-*-coding: utf-8 -*-

import time
from datetime import datetime, date
from datetime import time as datetime_time
from datetime import timedelta
from dateutil import relativedelta
import pytz
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT

from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

from odoo.tools import float_compare, float_is_zero, float_round
import math



class hr_payslip_line(models.Model):
    _inherit = "hr.payslip.line"

    hr_period_id = fields.Many2one('hr.period',related='slip_id.hr_period_id',store=True)
    date_from = fields.Date(related='slip_id.date_from', string='Date From',store=True)
    date_to = fields.Date(related='slip_id.date_to', string='Date To',store=True)
    date_payment = fields.Date(related='slip_id.date_payment', string='Date of Payment',store=True)
    department_id = fields.Many2one('hr.department',related='slip_id.employee_id.department_id',store=True)


