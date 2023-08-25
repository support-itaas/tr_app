#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from odoo import api, tools
from odoo.osv import osv
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
import pytz
from datetime import datetime,timedelta,date
from odoo import SUPERUSER_ID
from odoo.tools import float_compare, float_is_zero
from decimal import *
import math

class hr_salary_rule(models.Model):
    _inherit = "hr.salary.rule"

    cal_tax_onetime = fields.Boolean(string="คำนวนภาษีต่อหนึ่งเดือนหรือไม่")