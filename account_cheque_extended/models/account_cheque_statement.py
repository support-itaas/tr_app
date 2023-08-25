# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class account_cheque_statement(models.Model):
    _inherit = 'account.cheque.statement'

    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')

    @api.onchange('bank_account_id')
    def onchange_bank_account_id(self):
        if self.bank_account_id:
            self.cheque_bank = self.bank_account_id.bank_id
            self.account_id = self.bank_account_id.account_id

