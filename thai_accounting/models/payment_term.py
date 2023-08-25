# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
from decimal import *

def isodd(x):
    return bool(x % 2)

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


class payment(models.Model):

    _inherit = "account.payment.term.line"

    date = fields.Integer(string="Date")
    type_invoice = fields.Selection([('invoice_month', 'Invoice Month'), ('next_month', 'Next Invoice Month'),('bill_month', 'Bill Month'),('bill_next_month', 'Next Bill Month')])
    days = fields.Integer(string='Number of Days', default=0)
    option = fields.Selection([
        ('day_after_invoice_date', 'Day(s) after the invoice date'),
        ('fix_day_following_month', 'Day(s) after the end of the invoice month (Net EOM)'),
        ('last_day_following_month', 'Last day of following month'),
        ('last_day_current_month', 'Last day of current month'),
    ],
        default='day_after_invoice_date', required=False,string='Options'
    )


    @api.onchange('type_invoice','date')
    def onchange_type_invoice(self):

        if self.type_invoice:
            self.option = False
            self.days = 0

    @api.onchange('option')
    def _onchange_option(self):

        if self.option:
            self.type_invoice = False
            self.date = 0

        if self.option in ('last_day_current_month', 'last_day_following_month'):
            self.days = 0

class AccountPaymentTerm(models.Model):

    _inherit = "account.payment.term"

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        prec = currency.decimal_places
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'percent':
                amt = round(value * (line.value_amount / 100.0), prec)
            elif line.value == 'balance':
                amt = round(amount, prec)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                elif line.option == 'fix_day_following_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'last_day_following_month':
                    next_date += relativedelta(day=31, months=1)  # Getting last day of next month
                elif line.option == 'last_day_current_month':
                    next_date += relativedelta(day=31, months=0)  # Getting last day of next month
                # elif line.type_invoice == 'invoice_month':
                #     next_date += relativedelta(days=line.date, month=1)

                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        # amount = reduce(lambda x, y: x + y[1], result, 0.0)
        amount = sum(amt for _, amt in result)
        dist = round(value - amount, prec)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bill_date = fields.Integer(string='Bill Date of the Month',default=0)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('payment_term_id', 'date_invoice','bill_date')
    def _onchange_payment_term_date_invoice(self):
        bill_date = False
        date_invoice = False
        bill_date_temp = False
        if self.date_invoice:
            date_invoice = strToDate(self.date_invoice)
        if self.bill_date:
            bill_date = strToDate(self.bill_date)
        if not date_invoice:
            date_invoice = strToDate(fields.Date.context_today(self))

        if not bill_date and self.partner_id and self.partner_id.bill_date:
            bill_date_temp = self.partner_id.bill_date
            self.bill_date = date(date_invoice.year, date_invoice.month, bill_date_temp)
            bill_date = strToDate(self.bill_date)

        if bill_date and date_invoice:
            if date_invoice > bill_date:
                self.bill_date = bill_date + relativedelta(months=1)

        if not self.payment_term_id:
            # When no payment term defined
            self.date_due = self.date_due or self.date_invoice
        else:
            pterm = self.payment_term_id
            if pterm.line_ids and pterm.line_ids[0].days:
                # print "date due by day"
                pterm_list = \
                pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=str((date_invoice)))[0]
                self.date_due = max(line[0] for line in pterm_list)

            #this is payment term not by day but by date instead
            elif pterm.line_ids and not pterm.line_ids[0].days and pterm.line_ids[0].date and pterm.line_ids[0].type_invoice:
                if pterm.line_ids[0].type_invoice == 'invoice_month':
                    # print "date due by date invoice month"
                    self.date_due = date(date_invoice.year, date_invoice.month, pterm.line_ids[0].date)
                    if strToDate(self.date_invoice) > strToDate(self.date_due):
                        self.date_due = self.date_due + relativedelta(months=1)
                elif pterm.line_ids[0].type_invoice == 'next_month':
                    # print "date due by date invoice next month"
                    self.date_due = date(date_invoice.year, date_invoice.month, pterm.line_ids[0].date)
                elif pterm.line_ids[0].type_invoice == 'bill_month':
                    # print "date due by date bill month"
                    if not self.bill_date:
                        raise UserError(_('Please assign bill date to calculate due date'))
                    else:
                        bill_date = strToDate(self.bill_date)
                        self.date_due = date(bill_date.year, bill_date.month, pterm.line_ids[0].date)
                        if strToDate(self.date_due) < strToDate(self.bill_date):
                            self.date_due = strToDate(self.date_due) + relativedelta(months=1)
                elif pterm.line_ids[0].type_invoice == 'bill_next_month':
                    # print "date due by date bill next month"
                    if not self.bill_date:
                        raise UserError(_('Please assign bill date to calculate due date'))
                    else:
                        bill_date = strToDate(self.bill_date)
                        self.date_due = date(bill_date.year, bill_date.month, pterm.line_ids[0].date) + relativedelta(months=1)


