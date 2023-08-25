# -*- coding: utf-8 -*-
from openerp import fields, api, models
from bahttext import bahttext
from datetime import datetime,date
from dateutil.relativedelta import relativedelta


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountInvoice_inherit(models.Model):
    _inherit ="account.invoice"

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def get_origin(self,origin):
        account = self.search([('number', '=', origin)], limit=1)
        return account.amount_untaxed

    def get_date_of_orgin(self, vals):
        print(vals)
        if vals:
            origin = self.search([('name', '=', vals), ], limit=1)
            date = origin.date_invoice
        print(origin.name)
        return date


class Account_cheque_statement(models.Model):
    _inherit ="account.cheque.statement"

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    name_for_cheque = fields.Char(string='Name for Cheque')

    @api.model
    def create(self, vals):
        if vals.get('partner_id', False):
            vals['name_for_cheque'] = self.env['res.partner'].browse(vals['partner_id']).name_for_cheque
        return super(Account_cheque_statement, self).create(vals)

    def get_uppercase(self, vals):
        if vals:
            val = vals.upper()
        else:
            val = vals
        print(val)
        return val

    def get_date_format(self, vals):
        new_date = strToDate(vals) + relativedelta(years=543)
        txt = str(new_date)
        for v in txt:
            txt_2 = str(txt[8]) + '   ' + str(txt[9]) + '   ' + str(txt[5])+ '   ' + str(txt[6]) + '   ' + str(txt[0])+ '   ' + str(txt[1]) + '   ' + str(txt[2]) + '   ' + str(txt[3])
            print(txt_2)


        return txt_2







