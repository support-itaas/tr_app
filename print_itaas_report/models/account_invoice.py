# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from bahttext import bahttext
from num2words import num2words
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from odoo.tools.misc import formatLang
import time
from datetime import datetime,timedelta,date
import math

class account_invoice_receipt_dot(models.Model):
    _inherit = 'account.invoice'

    # is_show_image_signature = fields.Boolean(string="Show Signature")

    def get_line(self, data, max_line):
        # this function will count number of \n
        line_count = data.count("\n")
        if not line_count:
            # print "line 0 - no new line or only one line"
            # lenght the same with line max
            if not len(data) % max_line:
                line_count = len(data) / max_line
            # lenght not the same with line max
            # if less than line max then will be 0 + 1
            # if more than one, example 2 line then will be 1 + 1
            else:
                line_count = len(data) / max_line + 1
        elif line_count:
            # print "line not 0 - has new line"
            # print line_count
            # if have line count mean has \n then will be add 1 due to the last row have not been count \n
            line_count += 1
            data_line_s = data.split('\n')
            for x in range(0, len(data_line_s), 1):
                # print data_line_s[x]
                if len(data_line_s[x]) > max_line:
                    # print "more than one line"
                    line_count += len(data_line_s[x]) / max_line
        print ("final line")
        print (line_count)
        return line_count


    def get_break_line(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1
        for line in self.invoice_line_ids:
            line_height = row_line_height + ((self.get_line(line.name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        print (break_page_line)
        return break_page_line

    def get_break_line_invoice(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1
        # print 'get_break_line_invoice'
        for line in self.invoice_line_ids:
            # print line.product_id
            # print line.product_id.default_code
            # default_code

            # print count
            line_height = row_line_height + ((self.get_line(line.name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)
        # print "break_page_line"
        # print break_page_line
        return break_page_line


class account_invoice_receipt_line(models.Model):
    _inherit = 'account.invoice.line'

    is_productname = fields.Boolean('Product Name')

    def action_productname(self):
        if self.is_productname:
            self.is_productname = False
        else:
            self.is_productname = True

