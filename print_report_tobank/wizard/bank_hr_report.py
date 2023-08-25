# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

import base64
import xlwt
from io import BytesIO
from openerp import models, fields, api, _
from datetime import datetime, date
from openerp.exceptions import UserError
from openerp.tools import misc
from pytz import timezone
import pytz

class bank_support(models.Model):
    _name = "bank.support"

    name = fields.Char(string='Bank Name')
    code = fields.Char(string='Bank Code')
    branch = fields.Char(string='Bank Branch')
    reference = fields.Char(string='Bank Reference')

# this is for tax report section
class bank_hr_report(models.TransientModel):
    _name = 'bank.hr.report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    bank_type = fields.Many2one('bank.support',string='Bank')
    payment_type = fields.Selection([('payslip','Payslip')],default='payslip' ,required=True)
    # payment_type = fields.Selection([('payslip','Payslip'),('vendor','Vendor Payment')],required=True)

    @api.model
    def default_get(self, fields):
        res = super(bank_hr_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 0o1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def _get_subfix_word(self,word,num):
        word = word
        num = num
        sub = ""
        if not word:
            word = ""
            for count in range(0, num):
                sub += " "
            word = sub + word
        else:
            word = str(word)

        if word and len(word) < num:
            for count in range(len(word), num):
                sub += " "
            word = sub + word
            # print("if-1"+word)
        else:
            word_str = word
            word = word_str[0:num]
            # print("else-1"+word)
        return word

    def _get_prefix_word(self,word,num):
        word = word
        num = num
        pre = ""
        if not word:
            word = ""
            for count in range(0, num):
                pre += "0"
            word = pre + word
            # print("if-2" + word)
        else:
            word = str(word)
            # print("else-2" + word)

        if word and len(word) < num:
            for count in range(len(word), num):
                pre += "0"
            word = pre+word
            # print("if-2"+ word)
        else:
            word_str = word
            word = word_str[len(word)-num:len(word)]
            # print("else-2" + word)
        return word

    def _get_money(self, text):
        text_str = str("{0:.3f}".format(text)).split(".")
        test_re = text_str[0]+text_str[1]
        return test_re




    @api.multi
    def get_bank_report(self):
        print('def get_bank_report')
        context = dict(self._context or {})
        file_type = context.get('file')

        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')

        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,###.00'
        for_right_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz left,vertical center;")

        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name  Times New Roman, height 300,color black;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top thin, bottom thin, left thin, right thin;'
            'pattern:  pattern_fore_colour white, pattern_back_colour white'
        )

        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '#,###.00'
        cr, uid, context = self.env.args
        final_text = ""
        final_text_body = ""

        # -------------------------------------- SCB ----------------------------------------
        if self.bank_type.code == 'scb' or self.bank_type.code == 'SCB':
            # print ('step-1')
            if not self.payment_type:
                raise UserError(_('Please select one of the payment type first'))

            if self.payment_type == 'payslip':
                worksheet = workbook.add_sheet('report')
                worksheet_detail = workbook.add_sheet('report_detail')
                inv_row = 1
                salary = 0
                total = 0

                payslip_ids_all = self.env['hr.payslip'].search(
                    [('date_from', '>=', self.date_from),
                     ('date_to', '<=', self.date_to),
                     ('state', '=', 'done')])

                # print('step-2')
                # print (payslip_ids_all)
                payslip_ids = payslip_ids_all.filtered(lambda x: x.contract_id.wage_type == 'monthly'
                                                                 and x.employee_id.bank_account
                                                                 and x.employee_id.bank_name == self.bank_type.code
                                                                 and x.employee_id.bank_branch_code == self.bank_type.branch)
                # print('payslip_ids : ',len(payslip_ids))
                for ps in payslip_ids:
                    payroll = ""
                    date = ps.date_payment
                    salary += ps.total_net
                    bank_account = ps.employee_id.bank_account
                    test_cash = "{0:.2f}".format(ps.total_net)
                    cash = str(test_cash)
                    cash_temp = ""
                    temp = ""
                    for count in range(0, len(str(test_cash))):
                        if cash[count] != '.':
                            cash_temp += cash[count]
                    for count in range(len(cash_temp), 10):
                        temp += '0'
                    temp += cash_temp

                    employee_name = ps.employee_id.name

                    payroll += str(bank_account)
                    payroll += str(date[8]) + str(date[9]) + str(date[5]) + str(date[6]) + str(date[2]) + str(date[3])
                    payroll += str(temp)
                    payroll += '  '
                    payroll += employee_name

                    worksheet_detail.write(inv_row, 0, employee_name, for_left)
                    worksheet_detail.write(inv_row, 1, ps.total_net, for_left)

                    worksheet.write(inv_row, 0, payroll, for_left)
                    final_text_body = final_text_body + str(payroll) + "\r\n"

                    inv_row += 1
                    total += 1

                # ส่วนของผู้จ่ายเงินเดือน
                if payslip_ids:
                    header = ""
                    user = self.env['res.users'].browse(self.env.uid)
                    tz = pytz.timezone(user.tz)
                    today = pytz.utc.localize(datetime.now()).astimezone(tz)
                    dateofgen = today.strftime("%d%m%y")
                    test_cash = "{0:.2f}".format(salary)
                    cash = str(test_cash)
                    cash_temp = ""
                    temp = ""
                    for count in range(0, len(str(test_cash))):
                        if cash[count] != '.':
                            cash_temp += cash[count]
                    for count in range(len(cash_temp), 10):
                        temp += '0'
                    temp += cash_temp
                    #####hope this is difference between branch
                    header += self.bank_type.reference
                    # print (header)
                    header += str(dateofgen)
                    # print(header)
                    header += str(self._get_prefix_word(total, 5))
                    # print(header)
                    header += str(temp)
                    # print(header)
                    header += '|'
                    # print(header)

                    worksheet.write(0, 0, header, for_left)
                    final_text = str(header) + "\r\n" + final_text_body
                    worksheet_detail.write(0, 0, 'Name', for_center)
                    worksheet_detail.write(0, 1, 'Amount', for_center)

                else:
                    raise UserError(_('There is record this date range.'))

        # ------------------------------------ End BBL -------------------------------------------------

        if file_type == 'xls':

            workbook.save(fl)
            fl.seek(0)

            buf = base64.encodestring(fl.read())
            cr, uid, context = self.env.args
            ctx = dict(context)
            ctx.update({'report_file': buf})
            self.env.args = cr, uid, misc.frozendict(context)
            ## To remove those previous saved report data from table. To avoid unwanted storage
            self._cr.execute("TRUNCATE bank_hr_excel_export CASCADE")

            wizard_id = self.env['bank.hr.excel.export'].create(vals={'name': 'Bank Report.xls',
                                                                      'report_file': ctx['report_file']})

            # print (wizard_id)

            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bank.hr.excel.export',
                'target': 'new',
                'context': ctx,
                'res_id': wizard_id.id,
            }

        elif file_type == 'dat':
            # default encoding to utf-8
            string_utf = base64.b64encode((final_text).encode("utf_8"))

            # print result
            # print('The encoded utf_8 version is:', string_utf)
            string_ascii = final_text.encode("ascii", "ignore")
            # print('The encoded ascii version is:', string_ascii)

            # final_text
            values = {
                'name': "Text to Bank Report",
                'datas_fname': 'bankreport.dat',
                'res_model': 'ir.ui.view',
                'res_id': False,
                'type': 'binary',
                'public': True,
                'datas': string_utf,  ###ANSI ##utf_8 ##iso8859_11 ##TIS_620
                # 'datas': file_data.encode('utf8').encode('base64'),
            }

            # create as attachment
            attachment_id = self.env['ir.attachment'].sudo().create(values)
            # Prepare your download URL
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')

            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
            }

        else:
            # default encoding to utf-8
            string_utf = base64.b64encode((final_text).encode("utf_8"))

            # print result
            # print('The encoded utf_8 version is:', string_utf)
            string_ascii = final_text.encode("ascii", "ignore")
            # print('The encoded ascii version is:', string_ascii)

            values = {
                'name': "Text to Bank Report",
                'datas_fname': 'bankreport.txt',
                'res_model': 'ir.ui.view',
                'res_id': False,
                'type': 'binary',
                'public': True,
                'datas': string_utf,
                # 'datas': file_data.encode('utf8').encode('base64'),
            }

            # create as attachment
            attachment_id = self.env['ir.attachment'].sudo().create(values)
            # Prepare your download URL
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')

            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
            }


class bank_hr_excel_export(models.TransientModel):
    _name = 'bank.hr.excel.export'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'bank.hr.report',
            'target': 'new',
        }

