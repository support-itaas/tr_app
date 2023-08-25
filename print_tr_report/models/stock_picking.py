# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)


class StockPicking_inherit(models.Model):
    _inherit ="stock.picking"

    new_bill = fields.Char(string="NEW Bill")
    is_show_lot = fields.Boolean(string='Show Lot Report', default=True)

    def get_lines(self, data, max_line):
        # this function will count number of \n
        # print  data
        line_count = 0
        if data:
            line_count = data.count("\n")
            if not line_count:
                #  print "line 0 - no new line or only one line"
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
            print("final line")
            print(line_count)
        return line_count

    def get_break_line(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1

        for line in self.move_lines:

            # count += 1
            print(count)
            print(line.product_id.default_code)
            print(line.name)

            line_name = self.get_lines(line.product_id.name, max_line_lenght)
            line_move_line_ids = len(line.move_line_ids)
            print("line_move_line_ids")
            print(len(line.move_line_ids))

            if (line_name > line_move_line_ids):
                line_height = row_line_height + ((line_name) * new_line_height)
            else:
                line_height = row_line_height + ((line_move_line_ids) * new_line_height)

            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        print(break_page_line)
        return break_page_line

    def get_break_line_bill(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1

        for line in self.move_lines:

            line_name = self.get_lines(line.product_id.name, max_line_lenght)
            line_uom = self.get_lines(line.product_uom.name, 11)
            if self.is_show_lot:
                line_lot = 0.0
                for ml in line.move_line_ids:
                    if ml.lot_id:
                        line_lot += self.get_lines(ml.lot_id.name, 15)
                    else:
                        line_lot += self.get_lines(ml.lot_name, 15)
            else:
                line_lot = 1.0
            get_line_height = max(line_name,line_lot,line_uom)

            line_height = row_line_height + ((get_line_height) * new_line_height)

            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        return break_page_line

    def get_origin(self,origin):

        obj_origin = self.env['material.purchase.requisition'].search(
            [('sequence', '=', origin)], limit=1)
        product_name = obj_origin.mo_id.product_id.name
        product_id = obj_origin.mo_id.product_id.default_code
        print("---------")
        print("["+product_id+"]"+product_name)
        return "["+product_id+"] "+product_name

    def get_credit_and_due_date(self):
        credit_term = ""
        credit_term_day = 0
        if not self.force_date:
            due_date = self.scheduled_date
        else:
            due_date = self.force_date

        if self.partner_id and self.partner_id.property_supplier_payment_term_id and self.partner_id.property_supplier_payment_term_id.line_ids:
            credit_term = self.partner_id.property_supplier_payment_term_id.name
            credit_term_day = self.partner_id.property_supplier_payment_term_id.line_ids[0].days
        if credit_term and credit_term_day:
            # print('CREDIT')
            # print(credit_term_day)
            # print(self.force_date)
            due_date = (strToDate(due_date) + relativedelta(days=credit_term_day)).strftime('%d/%m/%Y')
        else:
            due_date = (strToDate(due_date)).strftime('%d/%m/%Y')
            # print(due_date)

        return credit_term, due_date