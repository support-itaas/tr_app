# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime, date

class InheritAccountAccount(models.Model):
    _inherit = 'account.account'

    petty_cash_type = fields.Boolean('รายงานเงินสดย่อย')

