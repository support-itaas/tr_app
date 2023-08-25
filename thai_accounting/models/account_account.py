# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError

class account_account(models.Model):
    _inherit = "account.account"

    wht = fields.Boolean(string='Witholding Tax')
    bank_fee = fields.Boolean(string='ค่าธรรมเนียม')
    diff_little_money = fields.Boolean(string='เศษสตางค์')
    payment_cut_off = fields.Boolean(string='ตัดจ่าย')
    sale_tax_report = fields.Boolean(string='รายงานภาษีขาย')
    purchase_tax_report = fields.Boolean(string='รายงานภาษีซื้อ')



class sale_order(models.Model):
    _inherit = 'sale.order'
    sale_order_note = fields.Text(string="Note")


# class AccountReportGeneralLedger(models.TransientModel):
#     _inherit = "account.report.general.ledger"
#
#     department_id = fields.Many2one('hr.department', string="แผนก")
#
#     def _print_report(self, data):
#         data = self.pre_print_report(data)
#         data['form'].update(self.read(['initial_balance', 'sortby'])[0])
#         # print "update more department"
#         data['form'].update(self.read(['department_id'])[0])
#         if data['form'].get('initial_balance') and not data['form'].get('date_from'):
#             raise UserError(_("You must define a Start Date"))
#         records = self.env[data['model']].browse(data.get('ids', []))
#         return self.env['report'].with_context(landscape=True).get_action(records, 'account.report_generalledger', data=data)
#
# class ReportGeneralLedger(models.AbstractModel):
#     _inherit = 'report.account.report_generalledger'
#
#     # @api.v8
#     # def prepare_move_lines_for_reconciliation_widget(self, target_currency=False, target_date=False):
#     #     """ Returns move lines formatted for the manual/bank reconciliation widget
#     #
#     #         :param target_currency: curreny you want the move line debit/credit converted into
#     #         :param target_date: date to use for the monetary conversion
#     #     """
#     #     context = dict(self._context or {})
#     #     ret = []
#     #
#     #     for line in self:
#     #         company_currency = line.account_id.company_id.currency_id
#     #         ret_line = {
#     #             'id': line.id,
#     #             'name': line.name != '/' and line.move_id.name + ': ' + line.name or line.move_id.name,
#     #             'ref': line.move_id.ref or '',
#     #             # For reconciliation between statement transactions and already registered payments (eg. checks)
#     #             # NB : we don't use the 'reconciled' field because the line we're selecting is not the one that gets reconciled
#     #             'already_paid': line.account_id.internal_type == 'liquidity',
#     #             'account_code': line.account_id.code,
#     #             'account_name': line.account_id.name,
#     #             'account_type': line.account_id.internal_type,
#     #             'date_maturity': line.date_maturity,
#     #             'date': line.date,
#     #             'journal_name': line.journal_id.name,
#     #             'partner_id': line.partner_id.id,
#     #             'partner_name': line.partner_id.name,
#     #             # 'department': line.department_id.name,
#     #             'currency_id': (line.currency_id and line.amount_currency) and line.currency_id.id or False,
#     #         }
#     #
#     #         debit = line.debit
#     #         credit = line.credit
#     #         amount = line.amount_residual
#     #         amount_currency = line.amount_residual_currency
#     #
#     #         # For already reconciled lines, don't use amount_residual(_currency)
#     #         if line.account_id.internal_type == 'liquidity':
#     #             amount = abs(debit - credit)
#     #             amount_currency = abs(line.amount_currency)
#     #
#     #         # Get right debit / credit:
#     #         target_currency = target_currency or company_currency
#     #         line_currency = (line.currency_id and line.amount_currency) and line.currency_id or company_currency
#     #         amount_currency_str = ""
#     #         total_amount_currency_str = ""
#     #         if line_currency != company_currency and target_currency != company_currency:
#     #             total_amount = line.amount_currency
#     #             actual_debit = debit > 0 and amount_currency or 0.0
#     #             actual_credit = credit > 0 and -amount_currency or 0.0
#     #         else:
#     #             total_amount = abs(debit - credit)
#     #             actual_debit = debit > 0 and amount or 0.0
#     #             actual_credit = credit > 0 and -amount or 0.0
#     #         if line_currency != target_currency and target_currency != company_currency:
#     #             amount_currency_str = formatLang(self.env, abs(actual_debit or actual_credit),
#     #                                              currency_obj=line_currency)
#     #             total_amount_currency_str = formatLang(self.env, total_amount, currency_obj=line_currency)
#     #             ctx = context.copy()
#     #             ctx.update({'date': target_date or line.date})
#     #             total_amount = line_currency.with_context(ctx).compute(total_amount, target_currency)
#     #             actual_debit = line_currency.with_context(ctx).compute(actual_debit, target_currency)
#     #             actual_credit = line_currency.with_context(ctx).compute(actual_credit, target_currency)
#     #         amount_str = formatLang(self.env, abs(actual_debit or actual_credit), currency_obj=target_currency)
#     #         total_amount_str = formatLang(self.env, total_amount, currency_obj=target_currency)
#     #
#     #         ret_line['debit'] = abs(actual_debit)
#     #         ret_line['credit'] = abs(actual_credit)
#     #         ret_line['amount_str'] = amount_str
#     #         ret_line['total_amount_str'] = total_amount_str
#     #         ret_line['amount_currency_str'] = amount_currency_str
#     #         ret_line['total_amount_currency_str'] = total_amount_currency_str
#     #         ret.append(ret_line)
#     #     return ret
#
#     def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, department_id):
#         """
#         :param:
#                 accounts: the recordset of accounts
#                 init_balance: boolean value of initial_balance
#                 sortby: sorting by date or partner and journal
#                 display_account: type of account(receivable, payable and both)
#
#         Returns a dictionary of accounts with following key and value {
#                 'code': account code,
#                 'name': account name,
#                 'debit': sum of total debit amount,
#                 'credit': sum of total credit amount,
#                 'balance': total balance,
#                 'amount_currency': sum of amount_currency,
#                 'move_lines': list of move line
#         }
#         """
#         cr = self.env.cr
#         MoveLine = self.env['account.move.line']
#         move_lines = dict(map(lambda x: (x, []), accounts.ids))
#
#         # Prepare initial sql query and Get the initial move lines
#         if init_balance:
#             init_tables, init_where_clause, init_where_params = MoveLine.with_context(
#                 date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
#             init_wheres = [""]
#             if init_where_clause.strip():
#                 init_wheres.append(init_where_clause.strip())
#             init_filters = " AND ".join(init_wheres)
#             filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#             sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
#                     '' AS move_name, '' AS mmove_id, '' AS currency_code,\
#                     NULL AS currency_id,\
#                     '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
#                     '' AS partner_name\
#                     FROM account_move_line l\
#                     LEFT JOIN account_move m ON (l.move_id=m.id)\
#                     LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                     LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                     LEFT JOIN account_invoice i ON (m.id =i.move_id)\
#                     JOIN account_journal j ON (l.journal_id=j.id)\
#                     WHERE l.account_id IN %s" + filters + 'GROUP BY l.account_id')
#             params = (tuple(accounts.ids),) + tuple(init_where_params)
#             cr.execute(sql, params)
#             for row in cr.dictfetchall():
#                 move_lines[row.pop('account_id')].append(row)
#
#         sql_sort = 'l.date, l.move_id'
#         if sortby == 'sort_journal_partner':
#             sql_sort = 'j.code, p.name, l.move_id'
#
#         # Prepare sql query base on selected parameters from wizard
#         # if department_id:
#         #     print "come if"
#         #     tables, where_clause, where_params = MoveLine.with_context(department_id=department_id)._query_get()
#         # else:
#         #     print "come else"
#         #     tables, where_clause, where_params = MoveLine._query_get()
#
#         tables, where_clause, where_params = MoveLine._query_get()
#         wheres = [""]
#         if where_clause.strip():
#             wheres.append(where_clause.strip())
#
#         filters = " AND ".join(wheres)
#         filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#         filters_more = " AND l.department_id = " + str(department_id)
#
#         if not department_id:
#             sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, l.department_id AS ldept, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
#                                     m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name, d.name AS dept_name\
#                                     FROM account_move_line l\
#                                     JOIN account_move m ON (l.move_id=m.id)\
#                                     LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                                     LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                                     LEFT JOIN hr_department d ON (l.department_id=d.id)\
#                                     JOIN account_journal j ON (l.journal_id=j.id)\
#                                     JOIN account_account acc ON (l.account_id = acc.id) \
#                                     WHERE l.account_id IN %s ' + filters + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name, d.name ORDER BY ' + sql_sort)
#         else:
#             sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, l.department_id AS ldept, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
#                                     m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name, d.name AS dept_name\
#                                     FROM account_move_line l\
#                                     JOIN account_move m ON (l.move_id=m.id)\
#                                     LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                                     LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                                     LEFT JOIN hr_department d ON (l.department_id=d.id)\
#                                     JOIN account_journal j ON (l.journal_id=j.id)\
#                                     JOIN account_account acc ON (l.account_id = acc.id) \
#                                     WHERE l.account_id IN %s ' + filters + filters_more + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name, d.name ORDER BY ' + sql_sort)
#
#         params = (tuple(accounts.ids),) + tuple(where_params)
#         cr.execute(sql, params)
#         # cr.execute(sql)
#
#         for row in cr.dictfetchall():
#             balance = 0
#             for line in move_lines.get(row['account_id']):
#                 balance += line['debit'] - line['credit']
#             row['balance'] += balance
#             move_lines[row.pop('account_id')].append(row)
#
#         # Calculate the debit, credit and balance for Accounts
#         account_res = []
#         for account in accounts:
#             currency = account.currency_id and account.currency_id or account.company_id.currency_id
#             res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
#             res['code'] = account.code
#             res['name'] = account.name
#
#             res['move_lines'] = move_lines[account.id]
#             for line in res.get('move_lines'):
#                 res['debit'] += line['debit']
#                 res['credit'] += line['credit']
#                 res['balance'] = line['balance']
#             if display_account == 'all':
#                 account_res.append(res)
#             if display_account == 'movement' and res.get('move_lines'):
#                 account_res.append(res)
#             if display_account == 'not_zero' and not currency.is_zero(res['balance']):
#                 account_res.append(res)
#
#         return account_res
#
#     @api.multi
#     def render_html(self, data):
#         self.model = self.env.context.get('active_model')
#         docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
#
#         init_balance = data['form'].get('initial_balance', True)
#         sortby = data['form'].get('sortby', 'sort_date')
#         display_account = data['form']['display_account']
#         department_id = data['form']['department_id']
#         codes = []
#         if data['form'].get('journal_ids', False):
#             codes = [journal.code for journal in
#                      self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
#
#         accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
#         if department_id:
#             department_id = department_id[0]
#         else:
#             department_id = False
#         accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(accounts,
#                                                                                                        init_balance,
#                                                                                                        sortby,
#                                                                                                        display_account,
#                                                                                                        department_id)
#         docargs = {
#             'doc_ids': self.ids,
#             'doc_model': self.model,
#             'data': data['form'],
#             'docs': docs,
#             'time': time,
#             'Accounts': accounts_res,
#             'print_journal': codes,
#         }
#         return self.env['report'].render('account.report_generalledger', docargs)
    