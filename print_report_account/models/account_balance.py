# -*- coding: utf-8 -*-

import time
from odoo import api, models, fields
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
import locale

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountBalanceReport(models.TransientModel):
    _inherit = 'account.balance.report'

    is_first_year = fields.Boolean(string='First Year')
    is_only_summary = fields.Boolean(string='Only Summary')

    def left(self,s, amount):
        return str(s)[:amount]

    def right(self,s, amount):
        return str(s)[-amount:]

    @api.model
    def default_get(self, fields):
        res = super(AccountBalanceReport, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['is_first_year'])[0])
        data['form'].update(self.read(['is_only_summary'])[0])
        records = self.env[data['model']].browse(data.get('ids', []))
        # return self.env['report'].get_action(records, 'account.report_trialbalance', data=data)
        return self.env.ref('account.action_report_trial_balance').report_action(records, data=data)

    def get_closing_year_end(self,date_from, date_to):
        result = False

        move = self.env['account.move'].search([('date','>=',date_from),('date','<=',date_to),('is_year_end','=',True)],limit=1)
        if move:
            result = True

        return result

    def _get_accounts_before(self, account_code, display_account,date_from=False,date_to=False,target_move=False,is_first_year=False):
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

        #########################this function call from the report ##################
        #date from ----> date_start_year
        #date_to --->  date_from_before ----> strToDate(date_from) - relativedelta(days=1)

        #########################
        account_result = {}
        accounts = self.env['account.account'].search([('code','=',account_code)],limit=1)
        # Prepare sql query base on selected parameters from wizard
        #########if not first year ---> continue year and it is account type forward balance
        if not is_first_year and accounts.user_type_id.include_initial_balance:
            # print "Account CODE F"
            # print accounts.code
            date_from = False
            tables, where_clause, where_params = self.env['account.move.line'].with_context(date_from=False)._query_get()
        elif not is_first_year and not accounts.user_type_id.include_initial_balance:
            # print "Account CODE NF"
            # print accounts.code
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
        ###### this is for first year
        else:
            # print "FIRST YER and ELSE"
            tables, where_clause, where_params = self.env['account.move.line']._query_get()

        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]

        if where_clause.strip():
            wheres.append(where_clause.strip())
        # if not where_clause:
        #     where_clause = ("account_move_line"."move_id"="account_move_line__move_id"."id") AND ((("account_move_line"."date" <= %s)  AND  ("account_move_line"."date" >= %s))  AND  ("account_move_line__move_id"."state" = %s))
        filters = " AND ".join(wheres)

        #######if first year, then 2 condition , call report from first day or during day in the fiscal year
        if is_first_year:
            ###############this is calling from first day then date_to is input date_from -1 and date_from is start day of the year
            ############### thne date_to < date_from
            if date_to < date_from:
                # print "1-1"
                date_to = date_from
                request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = " + str(accounts.id) + " AND account_move_line.is_beginning_balance IS TRUE " + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")
            else:
                #########if not call the report from first day, for example feb then report will not split beginning balacnce then report will collect
                #########date from = start day of the year and date to = input date_from - 1
                # print "2-1"
                request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = " + str(accounts.id) + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")

        else:
            #print "-----Continue the year------"
            ######## if continue year, if forward barlance then need move line <= date_to, as date_to is one day before date from
            ######## date from and to condition above in query_get condition
            request = (
                "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                " FROM " + tables + " WHERE account_id = " + str(accounts.id) + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")

        if where_params:
            # print "11"
            if where_params[0]:
                where_params[0] = date_to
            if where_params[1] and date_from:
                where_params[1] = date_from
        else:
            # print "22"
            where_params = []
            where_params.append(date_to)
            where_params.append(date_from)
            where_params.append(str(target_move))

        # print "from and to (before)"
        # print date_from
        # print date_to
        # print "where_clause and param"
        # print where_clause
        # print where_params

        params = tuple(where_params)
        self.env.cr.execute(request, params)
        # print "in Before"
        #print "Request:" + str(request)
        #print "Filter:" + str(filters)
        #print "Param:" + str(params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            account_res.append(res)
        # print "before"
        # print account_res
        return account_res



class ReportTrialBalance(models.AbstractModel):
    _inherit = 'report.account.report_trialbalance'

    def left(self, s, amount):
        return str(s)[:amount]

    def right(self, s, amount):
        return str(s)[-amount:]

    def get_closing_year_end(self,date_from, date_to):
        result = False
        current_year_earning = 0
        move = self.env['account.move'].search([('date','>=',date_from),('date','<=',date_to),('is_year_end','=',True)],limit=1)
        if move:
            result = True
            for line in move.line_ids:
                if line.account_id.user_type_id.name == 'Current Year Earnings':
                    current_year_earning = line.balance
                    break

        #print "get_closing_year_end"
        #print result
        #print current_year_earning
        #print "--------------------"
        return result,current_year_earning


    def _get_accounts_year(self, account_code, display_account, date_from=False, date_to=False,
                             target_move=False):

        account_result = {}
        accounts = self.env['account.account'].search([('code', '=', account_code)], limit=1)
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # print "where_clause"
        # print where_clause
        # compute the balance, debit and credit for the provided accounts
        request = (
            "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
            " FROM " + tables + " WHERE account_id = " + str(accounts.id) + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")

        if where_params:
            if where_params[0]:
                where_params[0] = date_to
            if where_params[1]:
                where_params[1] = date_from
        else:
            where_params = []
            where_params.append(date_to)
            where_params.append(date_from)
            where_params.append(str(target_move))
        # print "where params after"
        # print where_params
        # print tuple(where_params)
        params = tuple(where_params)
        # print request
        # print filters
        # print params
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:


            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            account_res.append(res)

        return account_res

    def _get_accounts(self, data,accounts, display_account,date_start_year=False,date_from=False,date_to=False,target_move=False):
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
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())


        filters = " AND ".join(wheres)


        ##########if it is jan, mean it is the same of first year month then need to split between beginning balance and january transaction
        if date_start_year.year == strToDate(date_from).year and date_start_year.month == strToDate(date_from).month:
            #print '----------NOT INLCUDE BEGINNING BALANCE---------'
            request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                       " FROM " + tables + " WHERE account_id IN %s " + "AND account_move_line.is_beginning_balance IS FALSE " + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")
        ###################it is not january then beginning balance condition has not been checked but check year end instead that should not include in anything
        else:
            #print "----------INCLUDE BEGINNING BALANCE-------------"
            request = (
            "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
            " FROM " + tables + " WHERE account_id IN %s " + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")


        params = (tuple(accounts.ids),) + tuple(where_params)
        #print "CURRENT SEARCH"
        #print request
        #print filters
        #print params
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []

        is_year_end, current_year_earning = self.get_closing_year_end(date_from,date_to)

        for account in accounts:


            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
                # if is_year_end and account.user_type_id.name == 'Current Year Earnings':
                #     print "SKIP CURRENT YEAR EARNING"
                #     continue
                # if is_year_end and account.user_type_id.name == 'Retain Earning':
                #     print "DEDUCT RETAIN EARNING"
                #     res['balance'] -= current_year_earning
            if display_account == 'all':
                account_res.append(res)
            else:
                balance_year = self.with_context(data.get('used_context'))._get_accounts_year(account.code,display_account,date_start_year,date_to,target_move)

                if display_account == 'not_zero' and not currency.is_zero(balance_year[0]['balance']):
                    account_res.append(res)
                if display_account == 'movement' and (not currency.is_zero(balance_year[0]['debit']) or not currency.is_zero(balance_year[0]['credit'])):
                    account_res.append(res)
        # print "----current---"
        # print account_res
        return account_res

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        is_first_year = data['form'].get('is_first_year')
        date_from = data['form'].get('date_from')
        date_to = data['form'].get('date_to')
        target_move = data['form'].get('target_move')
        #print "RENDER HTML"
        date_start_year = datetime(strToDate(date_from).year, 1, 1).date() or False
        #print date_start_year


        # fiscalyear_last_day = self.company_id.
        # date_start_year = '2017-01-01'
        date_from_before = strToDate(date_from) - relativedelta(days=1)
        # date_from_before = str(date_from_before.year)+"-"+str(date_from_before.month)+"-"+str(date_from_before.day)
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        ######## current period#########
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(data['form'],accounts, display_account,date_start_year,date_from,date_to,target_move)

        #print "is first year"
        #print is_first_year
        #print "---------------"
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'date_from': strToDate(data['form']['date_from']).strftime("%d/%m/%Y"),
            'date_to': strToDate(data['form']['date_to']).strftime("%d/%m/%Y"),
            'target_move':target_move,
            'date_start_year': date_start_year,
            'date_to_before': date_from_before,
            'display_account': display_account,
            'is_first_year': is_first_year,
            # 'Accounts_before': account_res_before,
            'Accounts': account_res,
        }
        # return self.env['report'].render('account.report_trialbalance', docargs)
