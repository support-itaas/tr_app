# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare



class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_coupon_warranty = fields.Boolean(string='Coupon Warranty')
