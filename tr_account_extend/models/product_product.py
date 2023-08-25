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

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class product_product(models.Model):
    _inherit = 'product.product'

    is_extra_old = fields.Boolean(string='ตั้งค่าเผื่อสินค้าล้าสมัย')


    def apply_account(self):
        company_ids = self.env.user.company_ids
        account_code = self.actual_income_account_id.code
        print ('Account code',account_code)
        for company_id in company_ids:
            print ('COMpany',company_id.name)
            if not self.product_tmpl_id.with_context(force_company=company_id.id).actual_income_account_id:
                # print ('Update---')
                account_id = self.env['account.account'].sudo().search([('code','=',account_code),('company_id', '=', company_id.id)],limit=1)
                if account_id:
                    self.product_tmpl_id.with_context(force_company=company_id.id).update({'actual_income_account_id': account_id.id})
                    self.product_tmpl_id.with_context(force_company=company_id.id).update({'property_account_income_id': account_id.id})
                else:
                    raise UserError(_('Account Not found in %s')% (company_id.name))



            # self.actual_income_account_id =