# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class PurchaseOrder_inherit(models.Model):
    _inherit ="purchase.order"

    confirm_uid = fields.Many2one('res.users', 'Confirm')
    purchasing_uid = fields.Many2one('res.users', 'Purchasing')
    delivery_address = fields.Text(string='Delivery address')

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
            print(count)
            print(line.product_id.default_code)
            print(line.name)

            if line.product_id.default_code:
                linename = "["+line.product_id.default_code+"] "+line.name
            else:
                linename = line.name

            line_name = self.get_lines(linename, max_line_lenght)
            line_product_id_inventory = self.get_lines(self.picking_type_id.default_location_dest_id.name, 10)

            if (line_name > line_product_id_inventory):
                line_height = row_line_height + ((line_name) * new_line_height)
            else:
                line_height = row_line_height + ((line_product_id_inventory) * new_line_height)

            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        print(break_page_line)
        return break_page_line


    def get_pr_id(self):

        order_line = self.order_line.filtered(lambda x: x.pr_id)
        # pr_ids = []
        if order_line:
            # word = ""
            # for line in pr_id:
            #     if line.pr_id.name not in pr_ids:
            #         pr_ids.append(line.pr_id.name)
            #         if len(pr_ids) == 1:
            #             word = line.pr_id.name
            #         else:
            #             word = word + ", " + line.pr_id.name
            return order_line[0].pr_id
        else:
            return False

    def button_confirm(self):
        print("button_confirm")
        self.confirm_uid = self.env.uid
        return super(PurchaseOrder_inherit, self).button_confirm()

    # def action_validate(self):
    #     self.validate_uid = self.env.uid
    #     return super(PurchaseOrder_inherit, self).action_validate()

    def baht_text(self, amount):
        amount = round(amount, 2)
        amount_text = str(amount).split('.')
        amount_text_before_point = amount_text[0]
        amount_text_before_ten_point = amount_text_before_point[len(amount_text_before_point) - 2]
        amount_text_before_last_point = amount_text_before_point[len(amount_text_before_point) - 1]
        if int(amount_text_before_ten_point) == 0 and int(amount_text_before_last_point) == 1:
            amount_text_before_point = bahttext(float(amount_text_before_point)).split('เอ็ดบาท')
            amount_text_before_point = amount_text_before_point[0] + 'บาท'
        else:
            amount_text_before_point = bahttext(float(amount_text_before_point))

        amount_text_after_point = '0.' + amount_text[1]
        amount_after_point = float(amount_text_after_point)
        if float(amount_text_after_point) != 0.0:
            # print('amount_text_after_point ',amount_text_after_point)
            # print('amount_text_after_point[2] ',amount_text_after_point[2])
            # print('amount_text_after_point[3] ',amount_text_after_point[3])
            if amount_text_after_point[2] == '0' and amount_text_after_point[3] == '1':
                amount_text_after_point = 'หนึ่งสตางค์'
            else:
                amount_text_after_point = bahttext(amount_after_point).split('บาท')
                amount_text_after_point = amount_text_after_point[1]
        else:
            amount_text_after_point = 'ถ้วน'

        baht_text = amount_text_before_point.split('ถ้วน')[0] + amount_text_after_point
        # print('baht_tex:',baht_text)

        return baht_text
