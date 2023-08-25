# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sale_ok = fields.Boolean(
        'Can be Sold', default=False,
        help="Specify if the product can be selected in a sales order line.",copy=False)
    purchase_ok = fields.Boolean('Can be Purchased', default=False,copy=False)
    available_in_pos = fields.Boolean(string='Available in Point of Sale',
                                      help='Check if you want this product to appear in the Point of Sale',
                                      default=False,copy=False)

