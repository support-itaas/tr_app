# -*- coding: utf-8 -*-

import time

from doc._extensions.pyjsparser.parser import unicode
from odoo import api, models, fields
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
import locale

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountFinancialReport(models.TransientModel):
    _inherit = "accounting.report"

    before_after_year_end = fields.Selection([('bf','Before Year End'),('at','After Year End')],default='bf',string='Before/After Year End')
    show_zero = fields.Boolean(string='Show Zero Amount Report',default=False)

    @api.model
    def default_get(self, fields):
        res = super(AccountFinancialReport, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, 1, 1).date() or False
        date_from_cmp = datetime(curr_date.year-1, 1, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        to_date_cmp = datetime(curr_date.year-1, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date),'date_from_cmp': str(date_from_cmp),'date_to_cmp': str(to_date_cmp)})
        return res


    def get_closing_year_end(self):
        result = False

        move = self.env['account.move'].search([('date','>=',self.date_from),('date','<=',self.date_to),('is_year_end','=',True)],limit=1)
        if move:
            result = True

        return result

    def get_ebit(self,data,get_account_lines):
        ebit = 0.0
        ebit_cmp = 0.0
        for line in get_account_lines:
            if line['show_summary'] == 'net_income' or line['show_summary'] == 'ebit' or line['show_summary'] == 'ebt':
                ebit = ebit + line['balance']
                if data['enable_filter']:
                    ebit_cmp = ebit_cmp + line['balance_cmp']

        return ebit,ebit_cmp

    def get_ebt(self,data,get_account_lines):
        ebt = 0.0
        ebt_cmp = 0.0
        for line in get_account_lines:
            if line['show_summary'] == 'net_income' or line['show_summary'] == 'ebt':
                ebt = ebt + line['balance']
                if data['enable_filter']:
                    ebt_cmp = ebt_cmp + line['balance_cmp']

        return ebt,ebt_cmp


    def get_current_year_earning(self,get_account_lines):
        current_year_earning = 0
        for line in get_account_lines:
            if line['account_type'] == 'account_report':
                current_year_earning = line['balance']
                break

        return current_year_earning

    def get_current_year_earning_compare(self,get_account_lines):
        current_year_earning = 0
        for line in get_account_lines:
            if line['account_type'] == 'account_report':
                current_year_earning = line['balance_cmp']
                break

        return current_year_earning

    # def get_gp(self, get_account_lines):
    #
    # def get_op(self, get_account_lines):

    def split_financial(self,data,get_account_lines):
        # print("eeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        # print(data)
        # print(get_account_lines)
        # print("hhhhhhhhhhhhhhhhhhhhhhhhh")
        new_get_account_lines = {}
        main_lines = []
        sub_lines = []
        line_last_level = False
        # print "length"
        # print len(get_account_lines)
        title_name = 'รวม'
        # title_name = unicode(str(title_name), 'utf-8')
        net_income = 'กำไร(ขาดทุน)สุทธิ'
        gp_title = 'กำไรขั้นต้น'
        op_title = 'กำไรจากการดำเนินงาน'
        type_ni_report = False
        root_data_tmp = {}
        gp_data_tmp = {}
        deduct_current_year_earning_balance = 0
        # deduct_current_year_earning_debit = 0
        # deduct_current_year_earning_credit = 0
        # gp_data_tmp = {}
        # print(str(title_name))
        count = 0
        for line in get_account_lines:
            count +=1
            # print "++++++++++++"
            # print line['name']
            # print line['balance']
            # print "++++++++++++"

            # print count
            # print "-----------------"
            # print line['level']
            # print line['parent']
            # print line['display_detail']
            # print line['show_summary']
            # print line['id']
            # print line['name']
            # print line['type']
            # print line['account_type']
            # print line['balance']
            # if data['debit_credit']:
            #     print line['debit']
            #     print line['credit']
            #
            # if data['enable_filter']:
            #     print line['balance_cmp']

            ########if closing year end done but would like to run report as before year end then need to deduct ratain earning account from current year earning
            if line['is_retain_earning'] and self.before_after_year_end == 'bf' and self.get_closing_year_end():
                line['balance'] -= self.get_current_year_earning(get_account_lines)

            #########deduct previous year if compare don't check closing or not as it is surely already close
            if line['is_retain_earning'] and self.before_after_year_end == 'bf' and data['enable_filter']:
                if strToDate(data['date_to_cmp']).month == self.company_id.fiscalyear_last_month and strToDate(data['date_to_cmp']).day == self.company_id.fiscalyear_last_day:
                    line['balance_cmp'] -= self.get_current_year_earning_compare(get_account_lines)

            if line['level'] == 0:
                type_ni_report = line['type_ni_report']

                ###### this mean profit and loss
                if type_ni_report:
                    if data['debit_credit']:
                        debit = line['debit']
                        credit = line['credit']
                    else:
                        debit = False
                        credit = False

                    if data['enable_filter']:
                        balance_cmp = line['balance_cmp']
                    else:
                        balance_cmp = False

                    root_data_tmp = {
                        'name': net_income,
                        'level': line['level']+1,
                        'type': line['type'],
                        'account_type': 'account_type',
                        'balance': line['balance'],
                        'debit': debit,
                        'credit': credit,
                        'show_deduct': False,
                        'new_line': True,
                        'balance_cmp': balance_cmp,
                    }

                ###### don't have type mean balance sheet, no special now

            if type_ni_report == 'gp' and line['show_summary'] == 'gp':
                if data['debit_credit']:
                    debit = line['debit']
                    credit = line['credit']
                else:
                    debit = False
                    credit = False

                if data['enable_filter']:
                    balance_cmp = line['balance_cmp']
                else:
                    balance_cmp = False

                gp_data_tmp = {
                    'name': gp_title,
                    'level': line['level']+1,
                    'type': line['type'],
                    'account_type': 'account_type',
                    'balance': line['balance'],
                    'debit': debit,
                    'credit': credit,
                    'show_deduct': line['show_deduct'],
                    'new_line': True,
                    'balance_cmp': balance_cmp,
                }




            if line_last_level and line['level'] < line_last_level['level']:
                for main_line in main_lines:
                    if line_last_level['parent'].id == main_line['id'].id and main_line['display_detail'] == 'no_detail' and main_line['level'] != 0 and type_ni_report != 'gp':

                        if data['debit_credit']:
                            debit = main_line['debit']
                            credit = main_line['credit']
                        else:
                            debit = False
                            credit = False

                        if data['enable_filter']:
                            balance_cmp = main_line['balance_cmp']
                        else:
                            balance_cmp = False

                        ##########to make line summary same level with line_last_level
                        val_temp = {
                            'name': title_name + main_line['name'],
                            'level': line_last_level['level'],
                            'type': main_line['type'],
                            'account_type': line_last_level['account_type'],
                            'balance': main_line['balance'],
                            'debit': debit,
                            'credit': credit,
                            'new_line': True,
                            'show_deduct': line['show_deduct'],
                            'balance_cmp': balance_cmp,
                        }
                        # print "title -1"
                        # print val_temp['name']
                        sub_lines.append(val_temp)

                        if line['level'] < main_line['level']:
                            for main_higher_line in main_lines:
                                if main_line['parent'].id == main_higher_line['id'].id and main_higher_line['display_detail'] == 'no_detail' and main_line['level'] != 0:
                                    if data['debit_credit']:
                                        debit = main_higher_line['debit']
                                        credit = main_higher_line['credit']
                                    else:
                                        debit = False
                                        credit = False

                                    if data['enable_filter']:
                                        balance_cmp = main_higher_line['balance_cmp']
                                    else:
                                        balance_cmp = False

                                    val_temp = {
                                        'name': title_name + main_higher_line['name'],
                                        'level': main_higher_line['level'],
                                        'type': main_higher_line['type'],
                                        'account_type': line_last_level['account_type'],
                                        'balance': main_higher_line['balance'],
                                        'debit': debit,
                                        'credit': credit,
                                        'show_deduct': line['show_deduct'],
                                        'new_line': True,
                                        'balance_cmp': balance_cmp,
                                    }
                                    # print "title -2"
                                    # print val_temp['name']
                                    sub_lines.append(val_temp)


                line_last_level = line

            else:
                line_last_level = line

            if line['account_type'] == 'sum':
                main_lines.append(line)

            if type_ni_report == 'gp' and (line['show_summary'] == 'ebit' or line['show_summary'] == 'ebt'):
                # if line['show_summary'] == 'ebit':
                #     value,value_compare = self.get_ebit(data,get_account_lines)
                #     title_name = 'กำไรจากการดำเนินงาน'
                if line['show_summary'] == 'ebt':
                    sub_lines.append(op_data_tmp)
                    # value, value_compare = self.get_ebt(data, get_account_lines)
                    # title_name = 'กำไรก่อนภาษี'

                # title_name = unicode(title_name, 'utf-8')
                # val_temp = {
                #     'name': title_name,
                #     'level': line['level'],
                #     'type': line['type'],
                #     'account_type': line['account_type'],
                #     'balance': value,
                #     'debit': 0,
                #     'credit': 0,
                #     'new_line': True,
                #     'balance_cmp': value_compare,
                # }
                # sub_lines.append(val_temp)

            if type_ni_report == 'gp' and line['show_summary'] == 'op':
                sub_lines.append(gp_data_tmp)
                if data['debit_credit']:
                    debit = line['debit']
                    credit = line['credit']
                else:
                    debit = False
                    credit = False

                if data['enable_filter']:
                    balance_cmp = line['balance_cmp']
                else:
                    balance_cmp = False

                op_data_tmp = {
                    'name': op_title,
                    'level': line['level']+1,
                    'type': line['type'],
                    'account_type': 'account_type',
                    'balance': gp_data_tmp['balance']-line['balance'],
                    'debit': debit,
                    'credit': credit,
                    'show_deduct': False,
                    'new_line': True,
                    'balance_cmp': balance_cmp,
                }

            if self.before_after_year_end == 'bf':
                if line['account_type'] == 'account_report':
                    deduct_current_year_earning_balance = line['balance']
                sub_lines.append(line)

            ###### mean after
            else:
                if line['account_type'] != 'account_report':
                    sub_lines.append(line)
                else:
                    deduct_current_year_earning_balance = line['balance']
                    # deduct_current_year_earning_debit = line['debit']
                    # deduct_current_year_earning_credit = line['credit']
                    # print "this is report account ignore"



            ##########last line
            if count == len(get_account_lines):
                if line_last_level['parent']:
                    for main_line in main_lines:
                        if line_last_level['parent'].id == main_line['id'].id and main_line['display_detail'] == 'no_detail' and main_line['level'] != 0 and type_ni_report != 'gp':
                            if data['debit_credit']:
                                debit = main_line['debit']
                                credit = main_line['credit']
                            else:
                                debit = False
                                credit = False

                            if data['enable_filter']:
                                balance_cmp = main_line['balance_cmp']
                            else:
                                balance_cmp = False

                            ##########to make line summary same level with line_last_level
                            val_temp = {
                                'name': title_name + main_line['name'],
                                'level': line_last_level['level'],
                                'type': main_line['type'],
                                'account_type': line_last_level['account_type'],
                                'balance': main_line['balance'],
                                'debit': debit,
                                'credit': credit,
                                'show_deduct': line['show_deduct'],
                                'new_line': True,
                                'balance_cmp': balance_cmp,
                            }
                            # print "title -3"
                            # print val_temp['name']
                            ########if close then deduct if not close then nothing to do
                            if self.get_closing_year_end():
                                # print val_temp['balance']
                                # print self.get_current_year_earning(get_account_lines)
                                val_temp['balance'] -= self.get_current_year_earning(get_account_lines)
                                # print val_temp['balance']

                            ####### if compare then the old one need to deduct as it surely already close
                            if data['enable_filter']:
                                # print "----------------------------------------"
                                # print val_temp['balance_cmp']
                                # print self.get_current_year_earning_compare(get_account_lines)
                                # print self.company_id.fiscalyear_last_month
                                # print self.company_id.fiscalyear_last_day
                                # print data['date_to_cmp']
                                # print strToDate(data['date_to_cmp']).month
                                # print strToDate(data['date_to_cmp']).day
                                if strToDate(data['date_to_cmp']).month == self.company_id.fiscalyear_last_month and strToDate(data['date_to_cmp']).day == self.company_id.fiscalyear_last_day:
                                    val_temp['balance_cmp'] -= self.get_current_year_earning_compare(get_account_lines)
                                # print val_temp['balance_cmp']



                            sub_lines.append(val_temp)

                            if main_line['parent']:
                                for main_higher_line in main_lines:
                                    if main_line['parent'].id == main_higher_line['id'].id and main_higher_line[
                                        'level'] != 0 and main_higher_line['display_detail'] == 'no_detail':
                                        if data['debit_credit']:
                                            debit = main_higher_line['debit']
                                            credit = main_higher_line['credit']
                                        else:
                                            debit = False
                                            credit = False

                                        if data['enable_filter']:
                                            balance_cmp = main_higher_line['balance_cmp']
                                        else:
                                            balance_cmp = False

                                        val_temp = {
                                            'name': title_name + main_higher_line['name'],
                                            'level': main_higher_line['level'],
                                            'type': main_higher_line['type'],
                                            'account_type': line_last_level['account_type'],
                                            'balance': main_higher_line['balance'],
                                            'debit': debit,
                                            'credit': credit,
                                            'show_deduct': line['show_deduct'],
                                            'new_line': True,
                                            'balance_cmp': balance_cmp,
                                        }
                                        # print "title -4"
                                        # print val_temp['name']

                                        ########if close then deduct if not close then nothing to do
                                        if self.get_closing_year_end():
                                            # print val_temp['balance']
                                            # print self.get_current_year_earning(get_account_lines)
                                            val_temp['balance'] -= self.get_current_year_earning(get_account_lines)
                                            # print val_temp['balance']

                                        ####### if compare then the old one need to deduct as it surely already close
                                        if data['enable_filter']:
                                            # print "----------------------------------------"
                                            # print val_temp['balance_cmp']
                                            # print self.get_current_year_earning_compare(get_account_lines)
                                            # print self.company_id.fiscalyear_last_month
                                            # print self.company_id.fiscalyear_last_day
                                            # print data['date_to_cmp']
                                            # print strToDate(data['date_to_cmp']).month
                                            # print strToDate(data['date_to_cmp']).day
                                            if strToDate(data['date_to_cmp']).month == self.company_id.fiscalyear_last_month and strToDate(data['date_to_cmp']).day == self.company_id.fiscalyear_last_day:
                                                val_temp['balance_cmp'] -= self.get_current_year_earning_compare(get_account_lines)
                                                # print val_temp['balance_cmp']

                                        sub_lines.append(val_temp)


                                        #########do the same in case PL has multi level

                if type_ni_report:
                    sub_lines.append(root_data_tmp)

        return sub_lines

class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'


    def _compute_account_balance(self, accounts,data):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            if accounts[0].user_type_id.include_initial_balance:
                tables, where_clause, where_params = self.env['account.move.line'].with_context(date_from=False)._query_get()
            else:
                tables, where_clause, where_params = self.env['account.move.line']._query_get()

            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)

            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + "AND account_move_line.is_year_end IS FALSE " + filters + \
                      " GROUP BY account_id"



            params = (tuple(accounts._ids),) + tuple(where_params)


            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports, data):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids,data)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts,data)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                # print "**********account_report*********"
                # print report.account_report_id.name
                res2 = self._compute_report_balance(report.account_report_id,data)
                # print res2
                # print "-----------------"
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids,data)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports,data)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports,data)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'parent': report.parent_id,
                'id': report,
                'new_line': False,
                'show_summary': report.show_summary,
                'position': report.position,
                'display_detail': report.display_detail,
                'type_ni_report': report.type_ni_report,
                'show_deduct': report.show_deduct,
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
                'is_retain_earning': report.is_retain_earning,
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'parent': report.parent_id,
                        'id': report,
                        'new_line': False,
                        'show_summary': report.show_summary,
                        'position': report.position,
                        'display_detail': report.display_detail,
                        'type_ni_report': report.type_ni_report,
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                        'show_deduct': report.show_deduct,
                        'is_retain_earning': report.is_retain_earning,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        # print "***********get account line***************"
        # print lines
        return lines


class account_financial_report(models.Model):
    _inherit = "account.financial.report"

    show_summary = fields.Selection([('net_income','กำไร(ขาดทุนสุทธิ)'),('ebit','กำไรจากการดำเนินงาน-ebit'),('ebt','กำไรก่อนภาษี-ebt'),('gp','กำไรขั้นต้น-gp'),('op','กำไรจากการดำเนินงาน-op')],string='Show Summary')
    position = fields.Selection([('before','ก่อนหน้า'),('after','หลัง')],string='Postion')
    type_ni_report = fields.Selection([('gp','งบกำไรขาดทุนแบบแสดงกำไรขั้นต้น'),('normal','งบกำไรขาดทุนแบบทั่วไป')],string="Type of Income Statement")
    show_deduct = fields.Boolean(string="Show Deduct")
    is_retain_earning = fields.Boolean(string='Retain Earning')
