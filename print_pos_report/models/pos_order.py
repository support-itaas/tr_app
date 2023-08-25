# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
import pytz
from datetime import datetime, timedelta, date


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'



    #-------------------------updata 2020-08-05---------------------------#
class PosOrderInherit(models.Model):
    _inherit = 'pos.order'

    def _lang(self):
        print('_lang')
        user_lang = self.env['res.users'].browse(self._uid).lang
        # th_TH , en_US ,False
        # print self._uid
        # print user_lang
        # print self.env.uid
        if user_lang:
            return user_lang
        else:
            return 'th_TH'

    def _referent(self, value_txt):
        if not value_txt:
            return
        txt = value_txt.split(' ')
        if len(txt) > 1:
            return txt[1]
        else:
            return

    def _date_time(self, date):
        print('_date_time')
        user_lang = self.env['res.users'].browse(self._uid).lang
        # th_TH , en_US ,False
        obj_user = self.env['res.users'].search([('id', '=', 1)])
        if not obj_user.tz:
            tzs = 'Asia/Bangkok'
        else:
            tzs = obj_user.tz
        tz = pytz.timezone(tzs) or pytz.utc
        date_from = str(pytz.utc.localize(datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")).astimezone(tz))
        th = str(datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        # en = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        print(date_from)
        if user_lang:
            if user_lang == 'th_TH':
                # th_TH , en_US ,False
                txt = date_from.split(' ')
                txt_date = txt[0].split('-')

                txt_time = txt[1].split(':')
                txt_subtract = str(txt_time[0]) + ' นาฟิกา ' + str(str(txt_time[1])) + ' นาที'
                txt_date_time = str(txt_date[2]) + '/' + str(txt_date[1]) + '/' + str(txt_date[0]) + ' ' + str(
                    txt_subtract)
                return txt_date_time
            else:
                print('en_US')
                print(date_from)
                txt = date_from.split(' ')
                txt_date = txt[0].split('-')

                txt_time = txt[1].split(':')
                txt_time_en = ''
                if int(txt_time[0]) > 12:
                    txt_time_en = 'PM'
                else:
                    txt_time_en = 'AM'
                txt_subtract = str(txt_time[0]) + ':' + str(str(txt_time[1])) + ' ' + str(txt_time_en)
                txt_date_time = str(txt_date[2]) + '/' + str(txt_date[1]) + '/' + str(txt_date[0]) + ' ' + str(
                    txt_subtract)
                return txt_date_time
        else:
            txt = date_from.split(' ')
            txt_date = txt[0].split('-')

            txt_time = txt[1].split(':')
            txt_subtract = str(txt_time[0]) + ' นาฟิกา ' + str(str(txt_time[1])) + ' นาที'
            txt_date_time = str(txt_date[2]) + '/' + str(txt_date[1]) + '/' + str(txt_date[0]) + ' ' + str(
                txt_subtract)
            return txt_date_time

class Pos_configInherit(models.Model):
    _inherit = 'pos.config'

    pos_id = fields.Char(string='POS ID')
    rml_header1 = fields.Char(string='Company Tagline')
    tax_header = fields.Boolean(string='ใบเสร็จรับเงิน/ใบกำกับภาษีอย่างย่อ', default=True)
    branch_no = fields.Char(string='Branch No')

    def branch_name(self):
        print('ffff')
        if not self:
            return
        for line in self:
            if line.company_id:
                line.branch_no = line.company_id.branch_no
                # line.write({'branch_no':line.company_id.branch_no,})


class pos_session(models.Model):
    _inherit = 'pos.session'

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def get_order_line(self):
        session_info = []
        order_line_ids = []
        untaxed_amount = tax_amount = total_amount = 0
        for order_id in self.order_ids.filtered(lambda x: not x.invoice_id):
            for line in order_id.lines:
                order_line_ids.append(line)

            tax_amount += order_id.amount_tax
            total_amount += order_id.amount_total

        untaxed_amount = total_amount - tax_amount
        print ('--XXX')
        print (order_line_ids)
        session_info.append(order_line_ids)
        session_info.append(untaxed_amount)
        session_info.append(tax_amount)
        session_info.append(total_amount)
        print (session_info)
        return session_info


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
        print("final line", line_count)
        return line_count

    def get_break_line_tax_pos(self, line_ids, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1
        print ('--LINE--')
        print (line_ids)
        for line in line_ids:
            line_height = row_line_height + ((self.get_line(line.name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1

        break_page_line.append(count - 1)
        return break_page_line