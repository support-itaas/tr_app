# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

import time
from odoo.osv import osv
# from odoo.report import report_sxw
import time
from datetime import datetime, timedelta
from odoo import api,fields, models
from odoo.osv import osv
# from odoo.report import report_sxw
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

        
class report_journal_daily_report(models.AbstractModel):
    _name = 'report.thai_accounting.journal_daily_report'

    @api.model
    def get_report_values(self, docids, data=None):
        company_id = self.env.user.company_id
        domain = [('company_id', '=', company_id.id)]
        if data['form']['date_from'] and data['form']['date_to']:
            domain.append(('date', '>=', data['form']['date_from']))
            domain.append(('date', '<=', data['form']['date_to']))
        if data['form']['journal_ids'][0]:
            domain.append(('journal_id', '=', data['form']['journal_ids'][0]))

        if data['form']['date_from'] and data['form']['date_to']:
            docs = self.env['account.move'].search(domain)
            return {
                'doc_ids': docids,
                'doc_model': 'account.move.line',
                'data': data['form'],
                'date_from': data['form']['date_from'],
                'date_to': data['form']['date_to'],
                'docs': docs,
                'company_id': company_id,
            }

        else:
            docs = self.env['account.move'].search([('id', '=', self.id)])

            return {
                'doc_ids': docids,
                'doc_model': 'account.move.line',
                'data': False,
                'date_from': False,
                'date_to': False,
                'docs': docs,
                'company_id': company_id,
            }


class report_journal_summary_report(models.AbstractModel):
    _name = 'report.thai_accounting.journal_summary_report'

    @api.model
    def get_report_values(self, docids, data=None):

        company_id = self.env.user.company_id
        journal_summary_ids = {}
        if data['form']['journal_ids']:
            for i in xrange(0, len(data['form']['journal_ids'])):
                domain = [('company_id', '=', company_id.id)]
                if data['form']['date_from'] and data['form']['date_to']:
                    domain.append(('date', '>=', data['form']['date_from']))
                    domain.append(('date', '<=', data['form']['date_to']))
                if data['form']['journal_ids'][i]:
                    account_id = self.env['account.journal'].search([('id','=',data['form']['journal_ids'][i])]).default_debit_account_id
                    domain.append(('account_id', '=', account_id.id))

                move_line_ids = self.env['account.move.line'].search(domain)
                all_debit = 0
                all_credit = 0
                if move_line_ids:
                    for move in move_line_ids:
                        all_debit += move.debit
                        all_credit += move.credit

                journal_summary_ids[i] = {
                    'code': self.env['account.journal'].search([('id', '=', data['form']['journal_ids'][i])],
                                                               limit=1).code,
                    'name': self.env['account.journal'].search([('id', '=', data['form']['journal_ids'][i])],
                                                               limit=1).name,
                    'debit': all_debit,
                    'credit': all_credit,
                    'balance': all_debit - all_credit
                }
            journal_summary_ids = [value for key, value in journal_summary_ids.items()]

        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'data': data['form'],
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'docs': journal_summary_ids,
            'company_id': company_id,
        }

    
