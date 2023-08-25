# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta,date

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class ReportAgedPartnerBalance(models.AbstractModel):

    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length,partner_detail_id,is_detail,user_id,difference_period,period_text):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear

        print ('------------NEW AGEING 01')
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")

        if difference_period:
            periods_text_ids = period_text.split(',')
            if len(periods_text_ids) < 4:
                raise UserError(_('Period is not correct %s') % (period_text))
            lenght = 0
            for i in range(5)[::-1]:
                if i != 0:
                    stop = start - relativedelta(days=int(periods_text_ids[lenght]))
                    period_length = periods_text_ids[lenght]
                lenght += 1
                # print('xx')
                if i == 4:
                    name_from = '0'
                    name_to = period_length
                    name_to_str = "-" + name_to
                elif i != 0:
                    name_from = str(int(name_to) + 1)
                    name_to = str(int(period_length) + int(name_to))
                    name_to_str = "-" + name_to
                else:
                    name_from = str(int(name_to) + 1)
                    name_to = ""
                    name_to_str = ""


                periods[str(i)] = {
                    'name': str(name_from) + str(name_to_str),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }

                start = stop - relativedelta(days=1)
        else:
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length)
                print('START', start)
                print('STOP', stop)
                periods[str(i)] = {
                    'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                print ('periods[str(i)]',periods[str(i)])
                start = stop - relativedelta(days=1)

        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']

        # if account_type == 'payable':
        #     code = '22-01-01-01'
        # else:
        #     code = '12-01-01-01'

        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, res_partner.ref
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.code in %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY res_partner.ref'''

        cr.execute(query, arg_list)

        partners = cr.dictfetchall()

        # print (partners)
        # print (x)x
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query

        ################################ if specific partner ##########

        if partner_detail_id:
            # print ('-----111')

            if isinstance(partner_detail_id, (int)):
                # print ('--11-1')
                partner_ids = [partner_detail_id]
                partners = [
                    {
                        'partner_id': partner_detail_id,
                    }
                ]
            else:
                print ('--11-2')
                partner_ids = partner_detail_id
                partners = []

                for pn in partner_detail_id:
                    partners.append({
                        'partner_id': pn,
                    })


        ############################# if not, follow the original #########
        else:
            print ('-----333')
            partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]

        ############## the same depend on partners
        lines = dict((partner['partner_id'] or False, []) for partner in partners)


        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.code IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids).sorted(lambda x: x.date):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
            if user_currency.is_zero(line_amount):
                continue
            if not line.invoice_id:
                continue

            #############if user has been define, then invoice without this user also ignore
            elif line.invoice_id and user_id and line.invoice_id.user_id.id != user_id:
                continue

            for partial_line in line.matched_debit_ids:
                if partial_line.debit_move_id.date[:10] <= date_from:
                    line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if partial_line.credit_move_id.date[:10] <= date_from:
                    line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)

            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                ####################################### add detail ##############
                number = ""
                sale = ""
                date_invoice = ""
                date_due = ""
                over_due = ''
                # print ('IS DETAIL')
                # print (is_detail)

                if is_detail and line.invoice_id:
                    number = line.invoice_id.number
                    sale = line.invoice_id.user_id.name
                    date_invoice = line.invoice_id.date_invoice
                    date_due = line.invoice_id.date_due

                    if not date_due:
                        date_due = date_invoice

                    over_due_date = str((strToDate(date_from) - strToDate(date_due)).days)
                    if int(over_due_date) > 0:
                        over_due = over_due_date
                    else:
                        over_due = ''

                elif is_detail and not line.invoice_id:
                    number = line.move_id.name
                    date_invoice = line.date
                    date_due = line.date_maturity
                    over_due_date = str((strToDate(date_from) - strToDate(date_due)).days)
                    if int(over_due_date) > 0:
                        over_due = over_due_date
                    else:
                        over_due = ''
                ####################################### add detail ##############

                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'number': number,
                    'sale': sale,
                    'date_invoice': date_invoice,
                    'date_due': date_due,
                    'over_due': over_due,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        # print ('-------------GROUP to LENGTH --------------------')
        for i in range(5):
            # print ('-------------I---------------' + str(i))
            # print ('-STG-0')
            # print ('LENGTH:' + str(i))
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.code IN %s)
                        AND ((l.partner_id IN %s))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''


            cr.execute(query, args_list)
            # print ('-STG-1')
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            # print ('------AML-----------------')
            # print self.env['account.move.line'].browse(aml_ids).sorted(lambda x: x.name)
            for line in self.env['account.move.line'].browse(aml_ids).sorted(lambda x: x.date):
                # print ('AML:' + str(line))
                # print (line.partner_id.id)
                ####################################### add detail ##############
                number = ""
                sale = ""
                date_invoice = ""
                date_due = ""
                over_due = ''
                # print ('IS DETAIL')
                # print (is_detail)
                # print ('-AML-1')
                if not line.invoice_id:
                    continue

                #############if user has been define, then invoice without this user also ignore
                ############# Jatupong - 28/05/2020 ###########################################
                elif line.invoice_id and user_id and line.invoice_id.user_id.id != user_id:
                    continue

                if is_detail and line.invoice_id:
                    number = line.invoice_id.number
                    sale = line.invoice_id.user_id.name
                    date_invoice = line.invoice_id.date_invoice
                    date_due = line.invoice_id.date_due

                    if not date_due:
                        date_due = date_invoice

                    over_due_date = str((strToDate(date_from) - strToDate(date_due)).days)
                    if int(over_due_date) > 0:
                        over_due = over_due_date
                    else:
                        over_due = ''

                    # print ('-AML-2')

                elif is_detail and not line.invoice_id:
                    number = line.move_id.name
                    date_invoice = line.date
                    date_due = line.date_maturity
                    over_due_date = str((strToDate(date_from) - strToDate(date_due)).days)
                    if int(over_due_date) > 0:
                        over_due = over_due_date
                    else:
                        over_due = ''

                    # print ('-AML-3')
                ####################################### add detail ##############
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    # print ('-AML-3-1')
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    # print ('-AML-3-2')
                    try:
                        if partial_line.debit_move_id and partial_line.debit_move_id.date[:10] <= date_from:
                            line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
                            # print ('-AML-3-3')
                    except:
                        continue
                for partial_line in line.matched_credit_ids:
                    # print ('-AML-3-4-1')
                    # print (partial_line.credit_move_id)
                    try:
                        if partial_line.credit_move_id and partial_line.credit_move_id.date[:10] <= date_from:
                            line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
                            # print ('-AML-3-4-00')
                    except:
                        continue

                # print ('-AML-4')
                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount

                    lines[partner_id].append({
                        'line': line,
                        'number': number,
                        'sale': sale,
                        'date_invoice': date_invoice,
                        'date_due': date_due,
                        'over_due':over_due,
                        'amount': line_amount,
                        'period': i + 1,
                        })

                # print ('-----------END-------------------')
            history.append(partners_amount)


        # print ('------------GROUP to Partner----------------')
        # print (history)
        # print (lines)
        # print (partners)
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['name'] = "[" + str(browsed_partner.ref) + "]" + str(values['name'])
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        # print ('--------------------RETURN')
        # print res
        # print total
        # print lines
        # print (x)
        # print lines
        # print lines[184185]
        return res, total, lines

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            # account_type = ['receivable']
            account_type = ['12-01-01-01']
        elif data['form']['result_selection'] == 'supplier':
            # account_type = ['payable']
            account_type = ['22-01-01-01']
        else:
            # account_type = ['payable', 'receivable']
            account_type = ['12-01-01-01','22-01-01-01']

        if data['form']['partner_id']:
            partner_id = data['form']['partner_id'][0]
            user_id = False
        elif data['form']['category_ids']:
            all_partner_ids = []
            print ('category',data['form']['category_ids'])
            partner_ids_1 = self.env['res.partner'].search([('category_id','in',data['form']['category_ids'])])
            if partner_ids_1:
                for pn in partner_ids_1:
                    all_partner_ids.append(pn.id)


            partner_id = all_partner_ids
            user_id = False
        elif data['form']['user_id']:
            user_id = data['form']['user_id'][0]
            all_partner_ids = []
            partner_ids_1 = self.env['res.partner'].search([('user_id', '=', data['form']['user_id'][0])])


            invoice_partner_ids_2 = self.env['account.invoice'].search([('user_id', '=', data['form']['user_id'][0])])

            # print ('1:')
            # print partner_ids_1
            #
            # print ('2:')
            # print invoice_partner_ids_2

            # if partner_ids_1:
            #     for pn in partner_ids_1:
            #         all_partner_ids.append(pn.id)

            if invoice_partner_ids_2:
                for pn_inv in invoice_partner_ids_2:
                    if pn_inv.partner_id.id not in all_partner_ids:
                        all_partner_ids.append(pn_inv.partner_id.id)


            partner_id = all_partner_ids

            if not partner_id:
                raise UserError(_("ไม่มีรายการของพนักงานขายคนนี้"))

        else:
            user_id = False
            partner_id = False

        # print ('-------------TEST----')
        # print partner_id
        # print data['form']['is_detail']
        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move, data['form']['period_length'],partner_id,data['form']['is_detail'],user_id,data['form']['difference_period'],data['form']['period_text'])


        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'detail': dummy,
        }


