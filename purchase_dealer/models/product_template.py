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

    # @api.model
    # def _default_operating_unit1(self):
    #     return self.env.user.default_operating_unit_id

    is_dealer_order_available = fields.Boolean(string='Available for Dealer Order')
    is_dealer_order_available_expenses = fields.Boolean(string='Available for Dealer Order Expenses')
