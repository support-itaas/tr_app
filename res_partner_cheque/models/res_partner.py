# -*- coding: utf-8 -*-

# for more product stock calculation and report

from bahttext import bahttext
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import locale
import time
from odoo import api,fields, models
from odoo.osv import osv
# from odoo.report import report_sxw
from odoo.tools import float_compare, float_is_zero


from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round
import operator as py_operator


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class res_partner(models.Model):
    _inherit = 'res.partner'

    name_for_cheque = fields.Char(string='Name for Cheque')


class account_cheque_statement(models.Model):
    _inherit = 'account.cheque.statement'

    name_for_cheque = fields.Char(string='Name for Cheque')

    @api.model
    def create(self, vals):
        if vals.get('partner_id',False):
            vals['name_for_cheque'] = self.env['res.partner'].browse(vals['partner_id']).name_for_cheque
        return super(account_cheque_statement, self).create(vals)




