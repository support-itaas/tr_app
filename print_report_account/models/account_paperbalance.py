# -*- coding: utf-8 -*-

import time
from odoo import api, models, fields
from datetime import datetime,timedelta,date
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class ReportPaperBalance(models.AbstractModel):
    _name = 'report.print_report_account.report_paperbalance'

    def left(self,s, amount):
        return str(s)[:amount]

    def right(self,s, amount):
        return str(s)[-amount:]

    def get_closing_year_end(self,date_from,date_to):
        result = False
        current_year_earning = 0

        move_line_ids = self.env['account.move.line'].search([('date','>=',date_from),('date','<=',date_to),('account_id.user_type_id','=','Current Year Earnings'),('is_year_end','=',True)])
        if move_line_ids:
            result = True
            for line in move_line_ids:
                current_year_earning += line.balance

        # print "GLYE"
        # print result
        # print current_year_earning
        return result,current_year_earning


    def _get_accounts(self, accounts, display_account,is_year_end,current_year_earning):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        # tables, where_clause, where_params = self.env['account.move.line']._query_get()
        # tables = tables.replace('"','')
        # if not tables:
        #     tables = 'account_move_line'
        # wheres = [""]
        # if where_clause.strip():
        #     wheres.append(where_clause.strip())
        # filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts

        for account in accounts.sorted(key=lambda a: a.code):

            if account.user_type_id.include_initial_balance:
                # print account.name
                # print "ACC CONTINUE YEEAR"
                tables, where_clause, where_params = self.env['account.move.line'].with_context(
                    date_from=False)._query_get()
            else:
                # print account.name
                # print "ACC RESET YEEAR"
                tables, where_clause, where_params = self.env['account.move.line']._query_get()

            tables = tables.replace('"', '')
            if not tables:
                tables = 'account_move_line'
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)

            request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                       " FROM " + tables + " WHERE account_id = " + str(account.id) + "AND account_move_line.is_year_end IS FALSE "+ filters + " GROUP BY account_id")
            params = tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                account_result[row.pop('id')] = row

        ##########this is function to detect closing year end##########
        # print "(account_result)"
        # print account_result
        # print accounts
        # print len(account_result)
        # print len(accounts)
        account_res = []
        for account in accounts.sorted(key=lambda a: a.code):
            #############this code to remove current year earning from the paper balance due to another calculation already done and should ignore this account
            #############however in case year end is close then we have to know amount of current year earning in order to deduct from "retain earning" account

            if account.user_type_id.name == 'Current Year Earnings':
                # print "FOUND CYE"
                continue
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
                if is_year_end and account.user_type_id.name == 'Ratain Earning':
                    # print "FOUND RE"
                    res['balance'] -= current_year_earning


            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.model
    def get_report_values(self, docids, data=None):
        # print "333333"
        is_year_end,current_year_earning = self.get_closing_year_end(data['form']['date_from'],data['form']['date_to'])
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account,is_year_end,current_year_earning)
        # print self.model
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'date_from': strToDate(data['form']['date_from']).strftime("%d/%m/%Y"),
            'date_to': strToDate(data['form']['date_to']).strftime("%d/%m/%Y"),
            'Accounts': account_res,
        }

        # # print "render_html"
        # # print data
        # # print docargs
        #
        # return self.env['report'].render('print_report_account.report_paperbalance', docargs)
