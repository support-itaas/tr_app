# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from bahttext import bahttext
from num2words import num2words
import locale
from odoo.tools.float_utils import float_compare, float_round
from odoo import models, fields, api, _
def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

class bahttxt_saleconvert(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    amount_total_text = fields.Char(string='Total(Text)', store=True, readonly=True, compute='amounttext',
                                    track_visibility='always')
    @api.one
    @api.depends('amount_total')
    def amounttext(self):

        amount_finaltext = bahttext(self.amount_total)
        self.amount_total_text = amount_finaltext


    def baht_text(self, amount_total):
        return bahttext(amount_total)

    @api.one
    @api.depends('amount_total')
    def amount_num2words_text(self):
        amount_num2words_text = num2words(self.amount_total)
        self.amount_total_num2words_text = amount_num2words_text

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                if amount_total_str[i] != ",":
                    before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new



class bahttxt_invoiceconvert(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    amount_total_invoice_text = fields.Char(string='Total(Text)', store=True, readonly=True, compute='amount_invoice_text',
                                            track_visibility='always')
    @api.one
    @api.depends('amount_total')
    def amount_invoice_text(self):

        amount_invoice_text = bahttext(self.amount_total)
        self.amount_total_invoice_text = amount_invoice_text

    def baht_text(self, amount):
        return bahttext(amount)

    @api.one
    @api.depends('amount_total')
    def amount_num2words_text(self):
        amount_num2words_text = num2words(self.amount_total)
        self.amount_total_num2words_text = amount_num2words_text

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        # print after_point
        # print after_point_str
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        # print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]
                # else:
                #     print "this is comma, then remove"

        # print n2w_origianl
        # print n2w_new
        return n2w_new

class bahttxt_invoicemove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    amount_total_invoice_text = fields.Char(string='Total(Text)', store=True, readonly=True, compute='amount_invoice_move_text',
                                            track_visibility='always')
    @api.one
    @api.depends('amount')
    def amount_invoice_move_text(self):

        amount_invoice_text = bahttext(self.amount)
        self.amount_total_invoice_text = amount_invoice_text

    def baht_text(self, amount):
        return bahttext(amount)

    @api.one
    @api.depends('amount')
    def amount_num2words_text(self):
        amount_num2words_text = num2words(self.amount)
        self.amount_total_num2words_text = amount_num2words_text

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new


class bahttxt_custombill(models.Model):
    _name = 'customer.billing'
    _inherit = 'customer.billing'

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    note = fields.Text(

        string="Shipping Notes",

        compute="compute_shipping_note",

    )

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    @api.depends('move_lines', 'state')
    def compute_shipping_note(self):

        for record in self:

            for move in record.move_lines:

                if move.sale_line_id and move.sale_line_id.order_id.sale_order_note:

                 record["note"] = move.sale_line_id.order_id.sale_order_note

            break
    # @api.multi
    # def action_confirm(self):
    #     res = super(stock_picking, self).action_confirm()
    #     for rec in self:
    #         rec.picking_ids.write({'note': rec.sale_order_note})
    #     return res

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new


class account_payment(models.Model):
    _inherit = 'account.payment'

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def num2_words(self, amount_total):
        before_point = ""
        amount_total_str = str(amount_total)
        for i in range(0,len(amount_total_str)):
            if amount_total_str[i] != ".":
                before_point += amount_total_str[i]
            else:
                break

        after_point = float(amount_total) - float(before_point)
        after_point = locale.format("%.2f", float(after_point), grouping=True)
        after_point = float(after_point)
        before_point = float(before_point)

        # print before_point
        # print after_point
        before_point_str = num2words(before_point)
        after_point_str = num2words(after_point)
        if after_point_str == 'zero':
            before_point_str += ' Only'
        else:
            for i in range(4,len(after_point_str)):
                before_point_str += after_point_str[i]

        n2w_origianl = before_point_str
        #print n2w_origianl
        # n2w_origianl = num2words(float(amount_total))
        n2w_new = ""
        for i in range(len(n2w_origianl)):
            if i == 0:
                n2w_new += n2w_origianl[i].upper()
            else:
                if n2w_origianl[i] != ",":
                    if n2w_origianl[i - 1] == " ":
                        n2w_new += n2w_origianl[i].upper()
                    else:
                        n2w_new += n2w_origianl[i]

        # print n2w_origianl
        # print n2w_new
        return n2w_new
