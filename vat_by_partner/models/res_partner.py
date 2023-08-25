# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

class ResPartner(models.Model):
    _inherit = 'res.partner'

    taxes_id = fields.Many2many('account.tax', 'partner_customer_taxes_rel', 'partner_id', 'tax_id',
                                         string='Customer Taxes',
                                         domain=[('type_tax_use', '=', 'sale')])

    supplier_taxes_id = fields.Many2many('account.tax', 'partner_supplier_taxes_rel', 'partner_id', 'tax_id',
                                         string='Vendor Taxes',
                                         domain=[('type_tax_use', '=', 'purchase')])