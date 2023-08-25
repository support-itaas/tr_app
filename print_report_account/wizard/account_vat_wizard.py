# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
#import xlwt
#import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *


# ========================== this is for mixer schedule report =======================================
class account_vat_report(models.TransientModel):
    _name = 'vat.report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    type = fields.Selection([('personal','ภงด 3'),('company','ภงด 53')], string='type')

    @api.model
    def default_get(self, fields):
        res = super(account_vat_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        # disable_excel_production_report = self.env.user.company_id.disable_excel_production_report
        company_id = self.env.user.company_id.id
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        data = self.read(cr, uid, ids, context=context)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'account.move.line',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        return self.pool['report'].get_action(cr, uid, [], 'print_report_account.account_vat_report_id', data=datas,
                                              context=context)


# class production_excel_export(models.TransientModel):
#     _name = 'production.excel.export'
#
#     report_file = fields.Binary('File')
#     name = fields.Char(string='File Name', size=32)
#
#     @api.multi
#     def action_back(self):
#         if self._context is None:
#             self._context = {}
#         return {
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'production.report',
#             'target': 'new',
#         }

# ============================================ End  =================================================

