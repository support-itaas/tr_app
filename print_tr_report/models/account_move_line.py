# -*- coding: utf-8 -*-
from odoo import api,fields, models
import math



class account_move_line_inherit(models.Model):
    _inherit ='account.move.line'

    def address_sum(self, address):

        a1 = ""
        if address.street and address.street2 and address.city and address.state_id and address.zip:
            a1 = address.street + address.street2 + address.city + address.state_id.name + address.zip
        elif address.street and address.street2 and address.city and address.state_id and not address.zip:
            a1 = address.street + address.street2 + address.city + address.state_id.name
        elif address.street and address.street2 and address.city and not address.state_id and not address.zip:
            a1 = address.street + address.street2 + address.city
        elif address.street and address.street2 and not address.city and not address.state_id and not address.zip:
            a1 = address.street + address.street2
        elif address.street and not address.street2 and not address.city and not address.state_id and not address.zip:
            a1 = address.street

        elif address.street and address.street2 and not address.city and address.state_id and address.zip:
            a1 = address.street + address.street2 + address.state_id.name + address.zip
        elif address.street and address.street2 and not address.city and address.state_id and not address.zip:
            a1 = address.street + address.street2 + address.state_id.name
        elif address.street and address.street2 and not address.city and not address.state_id and address.zip:
            a1 = address.street + address.street2 + address.zip


        elif address.street and address.street2 and address.city and not address.state_id and address.zip:
            a1 = address.street + address.street2 + address.city + address.zip
        elif address.street and address.street2 and address.city and not address.state_id and not address.zip:
            a1 = address.street + address.street2 + address.city

        elif address.street and address.street2 and address.city and address.state_id and not address.zip:
            a1 = address.street + address.street2 + address.city + address.state_id.name


        elif address.street and not address.street2 and address.city and address.state_id and address.zip:
            a1 = address.street + address.city + address.state_id.name + address.zip
        elif address.street and not address.street2 and not address.city and address.state_id and address.zip:
            a1 = address.street + address.state_id.name + address.zip
        elif address.street and not address.street2 and not address.city and not address.state_id and address.zip:
            a1 = address.street + address.zip

        print(a1)
        return a1



    def roundup_itaas(self,number):
        number = math.ceil(number)
        print(number)
        return number



    def test_funciton(self,docs):
        item_length = len(docs) / 10
        print ('-------LEND---')
        print (math.ceil(item_length))
        return math.ceil(item_length)

    def get_break_account_invoice_report_payment(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1

        for line in self:
            print(line)
            line_height = row_line_height + (
                        (self.get_lines(line.partner_id.vat, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        print(break_page_line)
        return break_page_line

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

    def action_update(self):
        invoice_date_id = self.env['account.move.line'].search([('invoice_date','=',False,)],)
        print('invoice_date_id :',invoice_date_id)
        for line in invoice_date_id:
            line.invoice_date = line.date


