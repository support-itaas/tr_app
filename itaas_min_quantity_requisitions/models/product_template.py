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

    min_quantity = fields.Float(string="Min qty", default=0.0)
    min_uom_id = fields.Many2one('product.uom',string="Unit")