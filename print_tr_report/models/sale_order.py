# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class SaleOrder_inherit(models.Model):
    _inherit ="sale.order"

    confirm_uid = fields.Many2one('res.users', 'Confirm')

    def get_lines(self, data, max_line):
        # this function will count number of \n
        # print  data
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

        for line in self.order_line:

            # count += 1
            # print(count)
            # print(line.product_id.default_code)
            # print(line.name)
            line_height = row_line_height + ((self.get_lines(line.product_id.name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        print(break_page_line)
        return break_page_line

    def action_confirm(self):
        self.confirm_uid = self.env.uid
        return super(SaleOrder_inherit, self).action_confirm()

    def action_validate(self):
        self.validate_uid = self.env.uid
        return super(SaleOrder_inherit, self).action_validate()



class Sale_Order_Line_s(models.Model):
    _inherit ='sale.order.line'


    def get_lines(self, data, max_line):
        # this function will count number of \n
        # print  data
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

