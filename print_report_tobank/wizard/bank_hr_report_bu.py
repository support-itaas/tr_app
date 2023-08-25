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


# this is for tax report section
class bank_hr_report(models.TransientModel):
    _name = 'bank.hr.report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    bank_type = fields.Selection([('scb','SCB-Bank'),('bbl','BBL-Bank')],default='scb' ,string='Bank')
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

        # -------------------------------------- BBL ----------------------------------------
        if self.bank_type == 'scb':

            if not self.payment_type:
                raise UserError(_('Please select one of the payment type first'))

            if self.payment_type == 'payslip':
                # sheet = workbook.add_worksheet('TaxCal')
                worksheet = workbook.add_sheet('report')
                worksheet_detail = workbook.add_sheet('report_detail')
                inv_row = 1
                salary = 0
                total = 0

                # payslip_ids = self.env['hr.payslip'].sudo().search([('date_from','>=',self.date_from),('date_to','<=',self.date_to),('wage_type','=','monthly'),('state','=','done')])
                payslip_ids_all = self.env['hr.payslip'].search(
                    [('date_from', '>=', self.date_from),
                     ('date_to', '<=', self.date_to),
                     ('state', '=', 'done')])

                payslip_ids = payslip_ids_all.filtered(lambda x: x.contract_id.wage_type == 'monthly')
                # payslip_date_pay = payslip_ids_all.filtered(lambda x: x.contract_id.wage_type == 'monthly')
                num_rec = 0
                total_net_salaly = net_salaly = 0.000
                date_pay_em_list = []

                inv_row = 0
                # ส่วนของผู้จ่ายเงินเดือน
                for ps in payslip_ids:
                    inv_row = inv_row + 1
                    num_rec = num_rec+1
                    name = ps.employee_id.name
                    code = ps.employee_id.employee_code
                    # 004
                    identification_id = ps.employee_id.identification_id
                    employee_name = ps.employee_id.name
                    home_address = ps.employee_id.home_address
                    mobile_phone = ps.employee_id.mobile_phone
                    work_email = ps.employee_id.work_email
                    bank_branch_code = ps.employee_id.bank_branch_code
                    net_salaly = self._get_money(ps.total_revenue_summary_net)
                    total_net_salaly = total_net_salaly + ps.total_revenue_summary_net

                    date_pay_em = ps.date_payment

                    if date_pay_em not in date_pay_em_list:
                        date_pay_em_list.append(date_pay_em)

                    credit_detail = "003" + \
                                    self._get_prefix_word(num_rec, 6) + self._get_subfix_word(identification_id, 25) + \
                                    self._get_prefix_word(net_salaly, 16) + "THB" + \
                                    self._get_prefix_word("1", 8) + self._get_subfix_word("N", 1) + \
                                    self._get_subfix_word("N", 1) + self._get_subfix_word("N", 1) + \
                                    self._get_subfix_word(False, 1) + self._get_subfix_word(False, 4) + \
                                    self._get_prefix_word("0", 2) + self._get_subfix_word(False, 14) + \
                                    self._get_prefix_word("0", 6) + self._get_prefix_word("0", 2) + \
                                    self._get_prefix_word("0", 16) + self._get_prefix_word("0", 6) + \
                                    self._get_prefix_word("0", 16) + self._get_prefix_word("0", 1) + \
                                    self._get_subfix_word(False, 40) + self._get_subfix_word(False, 8) + \
                                    "140"+ self._get_subfix_word(False, 35) + \
                                    self._get_subfix_word(bank_branch_code, 4) + self._get_subfix_word(False, 35) + \
                                    self._get_subfix_word(False, 1) + self._get_subfix_word(False, 1) + \
                                    self._get_subfix_word(False, 20) + self._get_subfix_word(False, 1) + \
                                    self._get_subfix_word(False, 3) + self._get_subfix_word(False, 2) + \
                                    self._get_subfix_word(False, 50) + self._get_subfix_word(False, 18) + \
                                    self._get_subfix_word(False, 2)
                    # record_type + credit_seq + credit_account_no + credit_amount + credit_currency

                    payee_details = "004"+self._get_prefix_word(1,8)\
                                    +self._get_prefix_word(num_rec,6)+self._get_subfix_word(identification_id,15)\
                                    +self._get_subfix_word(employee_name, 100)+self._get_subfix_word(home_address, 70)\
                                    +self._get_subfix_word(False, 70)+self._get_subfix_word(False, 70)\
                                    +self._get_subfix_word(False, 70)+self._get_subfix_word(False, 10)\
                                    +self._get_subfix_word(False, 10)+self._get_subfix_word(mobile_phone, 10)\
                                    +self._get_subfix_word(work_email, 64)+self._get_subfix_word(False, 100)\
                                    +self._get_subfix_word(False, 70)+self._get_subfix_word(False, 70)\
                                    +self._get_subfix_word(False, 70)
                    # record_type,internal_ref, credit_seq,identification_id, employee_name, home_address1,
                    # home_address2, home_address3, taxid, employee_name_eng,fax, mobile_phone,
                    # work_email, payee2_name, payee2_add1,payee2_add2, payee2_add3

                    # wht_details = "005"+self._get_short_word(False,8)\
                    #                 +self._get_short_word(False,6)+self._get_short_word(False,2)\
                    #                 +self._get_short_word(False,16)+self._get_short_word(False,5)\
                    #                 +self._get_short_word(False,77)+self._get_short_word(False,5)\
                    #                 +self._get_short_word(False,16)
                    # record_type1,Internal Reference,Credit Sequence No.,WHT Sequence No.
                    # WHT Amount,WHT Income Type,Income Description,WHT Deduct Rate,Income Type Amount

                    # invoice_details = "006"+self._get_short_word(False,8)\
                    #                 +self._get_short_word(False,6)+self._get_short_word(False,6)\
                    #                 +self._get_short_word(False,15)+self._get_short_word(False,16)\
                    #                 +self._get_short_word(False,8)+self._get_short_word(False,70)\
                    #                 +self._get_short_word(False,15)+self._get_short_word(False,16)\
                    #                 +self._get_short_word(False,16)+self._get_short_word(False,16)\
                    #                 +self._get_short_word(False,1)
                    # record_type,Internal Reference,Credit Sequence No.,Invoice Sequence No.
                    # Invoice Number,Invoice Amount,Invoice Date,Invoice Description
                    # PO Number,VAT Amount,Payee Charge Amount,WHT Amount,Print Language

                    final_text_body += credit_detail + "\r\n"
                    final_text_body += payee_details + "\r\n"
                    # final_text_body += wht_details + "\r\n"
                    # final_text_body += invoice_details+ "\r\n"

                    worksheet_detail.write(inv_row, 0, employee_name, for_left)
                    worksheet_detail.write(inv_row, 1, ps.total_revenue_summary_net, for_right)

                if payslip_ids:
                    ps = payslip_ids[0]
                    # Company Id
                    comapany_name = ps.company_id.eng_address
                    customer_ref = ps.company_id.vat
                    customer_scb_code = ps.company_id.scb_code
                    customer_bank_ac = ps.company_id.bank_ac

                    payslip_date_pay = payslip_ids.search([], limit=1, order='date_payment desc')
                    date_pay_str = (str(payslip_date_pay.date_payment)).split("-")
                    date_pay = date_pay_str[2]+date_pay_str[1]+date_pay_str[0]

                    total_salaly = self._get_money(total_net_salaly)

                    # print(x.strftime("%d%m%Y"))

                    if not customer_bank_ac:
                        customer_bank_ac_3 = ""
                        customer_bank_ac_1to3 = ""
                    else :
                        customer_bank_ac_3 = customer_bank_ac[3]
                        customer_bank_ac_1to3 = customer_bank_ac[0:3]

                    user = self.env['res.users'].browse(self.env.uid)
                    tz = pytz.timezone(user.tz)
                    today = pytz.utc.localize(datetime.now()).astimezone(tz)
                    dateofgen = today.strftime("%d%m%Y")
                    # timeofgen = today.strftime("%H%M%S")
                    timeofgen = today.strftime("00000000")

                    header = "001"+self._get_subfix_word(customer_scb_code,12)+\
                                   self._get_subfix_word(dateofgen,32)+dateofgen+\
                                   timeofgen+'BCM'+self._get_subfix_word(dateofgen,32)
                    # record_type + comapany_name + customer_ref + dateofgen + timeofgen + BCM + Batch
                    debit_detail = "002"+self._get_subfix_word("PAY",3)+\
                                   date_pay+self._get_subfix_word(customer_bank_ac,25)+\
                                   self._get_subfix_word("0"+customer_bank_ac_3,2)+self._get_subfix_word("0"+customer_bank_ac_1to3,4)+\
                                   "THB"+self._get_prefix_word(total_salaly,16)+\
                                   self._get_prefix_word("1",8)+self._get_prefix_word(len(payslip_ids),6)+\
                                   self._get_subfix_word(customer_bank_ac,15)+self._get_subfix_word(False,9)+\
                                   self._get_subfix_word(False,1)+self._get_subfix_word("0"+customer_bank_ac_3,2)+\
                                   self._get_subfix_word("0"+customer_bank_ac_1to3,4)
                    # record_type + product_code + value_date + debit_account_no

                    trailer = "999"+self._get_prefix_word(len(date_pay_em_list),6)+self._get_prefix_word(len(payslip_ids),6)+self._get_prefix_word(total_salaly,16)
                    # record_type + Total No. of Debits + Total No. of Credits + Total Amount

                    worksheet.write(0, 0, header, for_left)
                    worksheet.write(1, 0, debit_detail, for_left)

                    worksheet_detail.write(0, 0, 'Name', for_center)
                    worksheet_detail.write(0, 1, 'Amount', for_center)

                    # final_text = str(header) + "\r\n" + final_text_body
                    final_text += str(header)+ "\r\n"
                    final_text += str(debit_detail) + "\r\n"
                    # final_text += str(credit_detail) + "\r\n"
                    final_text += final_text_body
                    final_text += str(trailer)

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

            print (wizard_id)

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
            # final_text
            values = {
                'name': "Tex to Bank Report",
                'datas_fname': 'bankreport.dat',
                'res_model': 'ir.ui.view',
                'res_id': False,
                'type': 'binary',
                'public': True,
                'datas': base64.b64encode((final_text).encode("utf-8")),
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
            values = {
                'name': "Text to Bank Report",
                'datas_fname': 'bankreport.txt',
                'res_model': 'ir.ui.view',
                'res_id': False,
                'type': 'binary',
                'public': True,
                'datas': base64.b64encode((final_text).encode("utf-8")),
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

