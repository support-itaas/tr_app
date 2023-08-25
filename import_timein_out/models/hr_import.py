# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date
import pytz
from datetime import datetime
import xlrd
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
import base64


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))







class Hr_Import_So(models.Model):
    _name = 'hr.import.time'
    _description = 'HR import time'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    file_name = fields.Char('Name File',required=True)
    upload_file = fields.Binary('File Upload',required=True)

    @api.multi
    def read_file(self,options):
        upload_file = self.upload_file
        data = base64.b64decode(self.upload_file)
        with open('/tmp/' + self.file_name, 'wb') as file:
            file.write(data)
        xl_workbook = xlrd.open_workbook(file.name)
        sheet_names = xl_workbook.sheet_names()
        xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])

        # Number of columns
        num_cols = xl_sheet.ncols

        hr_attend_idz = self.env['hr.attendance.record']

        end_time = ''
        start_time = ''
        end_time_1 = ''
        start_time_1 = ''
        code = ''
        tz = pytz.timezone(self.env.user.tz)
        u_tz = pytz.timezone('UTC')

        for row_idx in range(1, xl_sheet.nrows):
            for col_idx in range(0 , num_cols):
                cell_obj = xl_sheet.cell(row_idx, col_idx)
                txt = str(cell_obj.value)
                if txt:
                    if col_idx >= 0 and row_idx == 0:
                        # print(txt)
                        # print('000')
                        continue
                    if col_idx == 0 and row_idx >= 1:
                        if row_idx:
                            code = txt
                            code = code.split('.')
                            code = code[0]
                    if col_idx == 1 and row_idx >=1:
                        date_att = txt
                        start_time = datetime.strptime(date_att, "%Y/%m/%d")
                        start_time.date()

                    if col_idx == 2 and row_idx >0:
                        time_att = txt
                        end_time = datetime.strptime(time_att,'%H:%M')
                        # end_time = end_time - relativedelta(hours=7)
                        end_time = end_time.time()

                    if col_idx == 3 and row_idx >=1:
                        timeout = txt
                        end_time_1 = datetime.strptime(timeout, '%H:%M')
                        # end_time_1 = end_time_1 - relativedelta(hours=7)
                        end_time_1 = end_time_1.time()

                    if col_idx == 4 and row_idx >=1:
                        text = txt

            finish_time_of_date = tz.localize(datetime.combine(start_time, end_time))
            finish_time_of_date = finish_time_of_date.astimezone(pytz.timezone('UTC'))
            finish_time_of_date_1 = tz.localize(datetime.combine(start_time, end_time_1))
            finish_time_of_date_1 = finish_time_of_date_1.astimezone(pytz.timezone('UTC'))


            vals = {
                'date_time': finish_time_of_date,
                'code': code,
            }

            valss = {
                'date_time': finish_time_of_date_1,
                'code': code,
            }

            # print(vals)
            hr_attend_idz.create(vals)

            hr_attend_idz.create(valss)




