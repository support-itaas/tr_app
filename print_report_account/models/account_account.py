from odoo import api, models
from datetime import datetime
from odoo.exceptions import UserError
from datetime import datetime,timedelta,date


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountAccount(models.Model):
    _inherit ='account.account'

    # def split(self,data):
    #     print data
    #     print data.split('.')[1]
    #     print data.left(2)
    #     return data.split('.')[1]

    def left(self,s, amount):
        return str(s)[:amount]

    def right(self,s, amount):
        return str(s)[-amount:]

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

        # print "-----------------get_accounts_before--------------"
        if is_first_year:
            # print "-----First Year---"
            # print date_from
            # print date_to
            # print date_to.month
            # print date_from.month
            # print "--------------------"
            ###############this is calling from first day then date_to is input date_from -1 and date_from is start day of the year
            ############### thne date_to < date_from
            if date_to < date_from:
                # print "1"
                date_to = date_from
                request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = " + str(accounts.id) + " AND account_move_line.is_beginning_balance IS TRUE " + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")
            else:
                # print "2"
                #########if not call the report from first day, for example feb then report will not split beginning balacnce then report will collect
                #########date from = start day of the year and date to = input date_from - 1
                request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = " + str(
                        accounts.id) + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")
        else:
            # print "-----Continue the year------"
            ######## if continue year, if forward barlance then need move line <= date_to, as date_to is one day before date from
            ######## date from and to condition above in query_get condition
            request = (
                "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                " FROM " + tables + " WHERE account_id = " + str(accounts.id) + "AND account_move_line.is_year_end IS FALSE " + filters + " GROUP BY account_id")

        if where_params:
            # print "11--"
            if where_params[0]:
                where_params[0] = date_to
            if where_params[1] and date_from:
                where_params[1] = date_from
        else:
            # print "22--"
            where_params = []
            where_params.append(date_to)
            where_params.append(date_from)
            where_params.append(str(target_move))

        # print "from and to (before)--"
        # print date_from
        # print date_to
        # print "where_clause and param--"
        # print where_clause
        # print where_params

        params = tuple(where_params)
        self.env.cr.execute(request, params)
        # print "in Before"
        # print request
        # print filters
        # print params
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

