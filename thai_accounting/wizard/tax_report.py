# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
from io import BytesIO
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
import xlwt
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def get_total_amount_multi_currency(self, move_id):
        total_amount = 0.0
        for line in move_id.line_ids:
            total_amount += abs(line.debit)

        # print "total amount"
        # print total_amount
        return total_amount

    def get_tax_amount_multi_currency(self, move_id):
        tax_amount = 0.0
        for line in move_id.line_ids:
            if line.account_id.sale_tax_report:
                tax_amount += abs(line.balance)

        #print "tax amount"
        #print tax_amount
        return tax_amount

#this is for tax report section
class tax_report(models.TransientModel):
    _name = 'tax.report'

    def _get_year(self):
        curr_date = datetime.now()
        last_year = curr_date.year - 1 + 543
        current_year = curr_date.year + 543
        next_year = curr_date.year + 1 + 543

        return [(last_year, last_year), (current_year, current_year), (next_year, next_year)]

    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    month = fields.Selection([
        (1,'มกราคม'),
        (2,'กุมภาพันธ์'),
        (3, 'มีนาคม'),
        (4, 'เมษายน'),
        (5, 'พฤษภาคม'),
        (6, 'มิถุนายน'),
        (7, 'กรกฏาคม'),
        (8, 'สิงหาคม'),
        (9, 'กันยายน'),
        (10, 'ตุลาคม'),
        (11, 'พฤศจิกายน'),
        (12, 'ธันวาคม'),
    ],string='Month',required=True)
    year = fields.Integer(string='Year')
    report_type = fields.Selection([('sale','ภาษีขาย'),('purchase','ภาษีซื้อ')],default='sale',string='Report Type', required=True)
    #partner_id = fields.Many2one('res.partner', string='Partner')
    tax_id = fields.Many2one('account.tax', string='Tax Type')
    disable_excel_tax_report = fields.Boolean(string="Disable Tax Report in Excel Format")
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit')
    company_id = fields.Many2one('res.company')
    include_no_vat = fields.Boolean(string='Include No Vat')



    @api.model
    def default_get(self, fields):
        res = super(tax_report,self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year,curr_date.month,1).date() or False
        to_date = datetime(curr_date.year,curr_date.month,calendar.monthrange(curr_date.year, curr_date.month)[1]).date() or False
        year = curr_date.year + 543
        disable_excel_tax_report = self.env.user.company_id.disable_excel_tax_report
        company_id = self.env.user.company_id.id
        res.update({'year': year,'month':curr_date.month,'date_from': str(from_date), 'date_to': str(to_date),'company_id': company_id,'disable_excel_tax_report': disable_excel_tax_report})
        print ('default get')
        print (res)
        return res

    @api.onchange('month','year')
    def onchange_month_year(self):
        if self.month and self.year:
            select_month = self.month
            select_year = self.year - 543
            month_day = calendar.monthrange(select_year, select_month)[1]
            from_date = datetime(select_year, select_month, 1).date() or False
            to_date = datetime(select_year, select_month, month_day).date() or False
            self.date_from = from_date
            self.date_to = to_date

    @api.onchange('report_type')
    def onchange_report_type(self):
        result = {}
        if self.report_type == 'sale':
            self.tax_id = self.env['account.tax'].search([('type_tax_use','=','sale'),('company_id','=',self.company_id.id),('tax_report','=',True)],limit=1)
            result['domain'] = {'tax_id': [('type_tax_use','=','sale'),('wht','=',False)]}
        if self.report_type == 'purchase':
            self.tax_id = self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('tax_report', '=', True)],
                limit=1)
            result['domain'] = {'tax_id': [('type_tax_use','=','purchase'),('wht','=',False)]}

        return result

    def print_report_pdf(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'report_type', 'tax_id', 'operating_unit_id','company_id','include_no_vat'])[0]

        if data['form']['report_type'] == 'sale':
            # return self.env['report'].get_action(self, 'thai_accounting.sale_tax_report_id', data=data)
            return self.env.ref('thai_accounting.action_sale_tax_report_id').report_action(self, data=data,
                                                                                           config=False)
        else:
            # return self.env['report'].get_action(self, 'thai_accounting.purchase_tax_report_id', data=data)
            return self.env.ref('thai_accounting.action_purchase_tax_report_id').report_action(self, data=data,
                                                                                               config=False)


    def get_amount_multi_currency(self,move_id):
        total_amount = 0.0
        tax_amount = 0.0
        for line in move_id.line_ids:
            total_amount += abs(line.debit)
            if line.account_id.sale_tax_report:
                tax_amount += abs(line.balance)

        return total_amount,tax_amount

    def get_amount_from_adjust_move_id(self,move_id):
        total_amount = 0.0
        tax_amount = 0.0
        for line in move_id.line_ids.filtered(lambda x: x.account_id.sale_tax_report):
            total_amount += abs(line.invoice_id.amount_total)
            tax_amount += abs(line.balance)
            # if line.account_id.sale_tax_report:
            #     tax_amount += abs(line.balance)
        return total_amount,tax_amount



    @api.multi
    def print_report(self):
        # fl = StringIO()
        fl = BytesIO()
        company_id = self.env.user.company_id
        # ir_values = self.env['ir.values']
        IrDefault = self.env['ir.default']
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf("font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,###.00'
        for_right_bold = xlwt.easyxf("font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf("font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf("font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf("font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf("font: bold 1, name  Times New Roman, color black, height 180;  align: horiz left,vertical center;")

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
        cr, uid , context=self.env.args

        if self.operating_unit_id:
            operating_unit_id = self.operating_unit_id
            company = self.operating_unit_id.company_id.name

            company_branch = operating_unit_id.partner_id and operating_unit_id.partner_id.name or ''
            company_address = ''
            if operating_unit_id.partner_id.street:
                company_address += operating_unit_id.partner_id.street + " "
            if operating_unit_id.partner_id.street2:
                company_address += operating_unit_id.partner_id.street2 + " "
            if operating_unit_id.partner_id.sub_district_id.name:
                if operating_unit_id.partner_id.state_id.code == 'BKK':
                    company_address += "แขวง" + operating_unit_id.partner_id.sub_district_id.name + " "
                else:
                    company_address += "ต." + operating_unit_id.partner_id.sub_district_id.name + " "
            if operating_unit_id.partner_id.district_id.name:
                if operating_unit_id.partner_id.state_id.code == 'BKK':
                    company_address += "เขต" + operating_unit_id.partner_id.district_id.name + " "
                else:
                    company_address += "อ." + operating_unit_id.partner_id.district_id.name + " "
            if operating_unit_id.partner_id.state_id:
                if operating_unit_id.partner_id.state_id.code == 'BKK':
                    company_address += operating_unit_id.partner_id.state_id.name + " "
                else:
                    company_address += "จ." + operating_unit_id.partner_id.state_id.name + " "
            if operating_unit_id.partner_id.zip:
                company_address += operating_unit_id.partner_id.zip + " "
            tax_id = operating_unit_id.partner_id.vat or ''
            branch_no = operating_unit_id.partner_id.branch_no or ''
        else:
            user = self.env['res.users'].browse(uid)
            company = user.company_id and user.company_id.name or ''
            company_branch = user.company_id and user.company_id.name or ''
            company_address = user.company_id and user.company_id.get_company_full_address_text() or ''
            tax_id = user.company_id and user.company_id.vat or ''
            branch_no = user.company_id and user.company_id.branch_no or ''

        taxes_id = IrDefault.sudo().get('product.template', 'taxes_id', company_id=self.company_id.id)
        supplier_taxes_id = IrDefault.sudo().get('product.template', 'supplier_taxes_id',company_id=self.company_id.id)

        t_id = self.env['account.tax'].browse(taxes_id)
        s_id = self.env['account.tax'].browse(supplier_taxes_id)

        if self.report_type == 'sale':
            worksheet.row(0).height = 200
            worksheet.col(0).width = 2000
            worksheet.col(1).width = 4000
            worksheet.col(2).width = 3500
            worksheet.col(3).width = 6000
            worksheet.col(4).width = 6000
            worksheet.col(5).width = 3000
            worksheet.col(6).width = 2000
            worksheet.col(7).width = 3000
            worksheet.col(8).width = 3000

        if self.report_type == 'purchase':
            worksheet.row(0).height = 200
            worksheet.col(0).width = 2000
            worksheet.col(1).width = 4000
            worksheet.col(2).width = 3500
            worksheet.col(3).width = 6000
            worksheet.col(4).width = 6000
            worksheet.col(5).width = 3000
            worksheet.col(6).width = 2000
            worksheet.col(7).width = 3000
            worksheet.col(8).width = 3000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        inv_row = 11
        year = int(datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%Y'))
        year += 543

        month = int(datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%m'))
        if month == 1:
            monthth = 'มกราคม'
        elif month == 2:
            monthth = 'กุมภาพันธ์'
        elif month == 3:
            monthth = 'มีนาคม'
        elif month == 3:
            monthth = 'มีนาคม'
        elif month == 4:
            monthth = 'เมษายน'
        elif month == 5:
            monthth = 'พฤษภาคม'
        elif month == 6:
            monthth = 'มิถุนายน'
        elif month == 7:
            monthth = 'กรกฏาคม'
        elif month == 8:
            monthth = 'สิงหาคม'
        elif month == 9:
            monthth = 'กันยายน'
        elif month == 10:
            monthth = 'ตุลาคม'
        elif month == 11:
            monthth = 'พฤศจิกายน'
        else:
            monthth = 'ธันวาคม'


        #option 2, generate tax report from account.invoice
        # this is first option to get all customer tax invoice from "account.invoice" with "sale tax account"
        inv_row_merge_head = inv_row + 1
        # sale
        customer_invoice_obj = self.env['account.invoice']
        pos_session_obj = self.env['pos.session']
        # purchase
        invoice_obj = self.env['account.move.line']

        if self.report_type == 'sale':
            invoice_all = []
            # print t_id
            # if self.tax_id.tax_report:
            worksheet.write_merge(0, 1, 0, 8, "รายงานภาษีขาย", GREEN_TABLE_HEADER)
            # else:
            #     worksheet.write_merge(0, 1, 0, 8, "รายงานภาษีขายยังไม่ถึงกำหนด", GREEN_TABLE_HEADER)

            worksheet.write(3, 1, 'เดือนภาษี', for_left_bold_no_border)
            worksheet.write(3, 2, monthth, for_left_bold_no_border)
            worksheet.write(3, 4, 'ปี', for_left_bold_no_border)
            worksheet.write(3, 5, year, for_left_bold_no_border)

            worksheet.write(5, 1, 'ชื่อผู้ประกอบการ', for_left_bold_no_border)
            worksheet.write(5, 2, company, for_left_bold_no_border)
            worksheet.write(5, 4, 'เลขประจำผู้เสียภาษีอากร', for_left_bold_no_border)
            worksheet.write(5, 5, tax_id, for_left_bold_no_border)

            worksheet.write(7, 1, 'ชื่อสถานประกอบการ', for_left_bold_no_border)
            worksheet.write(7, 2, company_branch, for_left_bold_no_border)
            worksheet.write(7, 4, 'สำนักงานใหญ่ / สาขา', for_left_bold_no_border)
            worksheet.write(7, 5, branch_no, for_left_bold_no_border)

            worksheet.write(9, 1, 'สถานประกอบการ', for_left_bold_no_border)
            worksheet.write(9, 2, company_address, for_left_bold_no_border)
            worksheet.write(9, 4, 'หน้าที่', for_left_bold_no_border)
            # worksheet.write(9, 5, branch_no, for_left_bold_no_border)

            worksheet.write_merge(inv_row, inv_row_merge_head, 0, 0, "ลำดับที่", for_center_bold)
            worksheet.write_merge(inv_row, inv_row, 1, 2, "ใบกำกับภาษี", for_center_bold)
            worksheet.write(inv_row_merge_head, 1, 'วัน เดือน ปี', for_center_bold)
            worksheet.write(inv_row_merge_head, 2, 'เลขที่', for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 3, 3, "ชื่อผู้ซื้อสินค้า/ผู้รับบริการ",for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 4, 4,
                                  'เลขประจำตัวผู้เสียภาษีอากรของผู้ซื้อสินค้า/ผู้รับบริการ', for_center_bold)
            worksheet.write_merge(inv_row, inv_row, 5, 6, "สถานประกอบการ", for_center_bold)
            worksheet.write(inv_row_merge_head, 5, 'สำนักงานใหญ่', for_center_bold)
            worksheet.write(inv_row_merge_head, 6, 'สาขาที่', for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 7, 7, "มูลค่าสินค้าหรือบริการ", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 8, 8, "จำนวนเงินภาษีมูลค่าเพิ่ม", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 9, 9, "รายการมูลค่าสินค้าหรือบริการ ภาษีอัตรา 0 %",for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 10, 10, "จำนวนเงินรวม", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 11, 11, "หมายเหตุ", for_center_bold)
            data = {}
            inv_row += 1
            sum_0 = 0.0
            sl_no = 1
            untaxed_total = tax_total = 0.0
            total_colum_10 = 0.0

            data['form'] = self.read(['date_from', 'date_to', 'report_type', 'tax_id', 'operating_unit_id', 'company_id', 'include_no_vat'])[0]
            pos_session_ids = self.env['report.thai_accounting.sale_tax_report_id'].get_report_values(self, data=data)

            invoices = pos_session_ids['docs']
            print('invoices:',invoices)
            check_tax_inv  = []
            print('--------pos_session_ids----')
            print('pos:',pos_session_ids['pos'])
            print(len(pos_session_ids))
            sum_total = 0
            if pos_session_ids and pos_session_ids['docs']:
                for inv in pos_session_ids['docs']:
                    inv_row += 1
                    worksheet.write(inv_row, 0, sl_no, for_center)
                    worksheet.write(inv_row, 1, inv['date'] or '', for_center)
                    worksheet.write(inv_row, 2, inv['name'] or '', for_left)

                    worksheet.write(inv_row, 3, inv['partner_id'].name or '', for_left)
                    worksheet.write(inv_row, 4, inv['vat'] or '', for_left)

                    if int(inv['is_branch_no']):
                        worksheet.write(inv_row, 5, ' ', for_left)
                        worksheet.write(inv_row, 6, inv['is_branch_no'] or '', for_left)
                    else:
                        worksheet.write(inv_row, 5, inv['is_branch_no'] or '', for_left)
                        worksheet.write(inv_row, 6, ' ', for_left)

                    if inv['state'] in ('open', 'paid'):
                        if inv['type'] == 'out_refund':
                            if inv['amount_tax'] == 0:
                                worksheet.write(inv_row, 7, '', for_right)
                            elif inv['amount_tax'] != 0:
                                worksheet.write(inv_row, 7, inv['amount_untaxed'] * (-1), for_right)
                                untaxed_total += inv['amount_untaxed'] * (-1)
                        else:
                            if inv['amount_tax'] == 0:
                                worksheet.write(inv_row, 7, '', for_right)
                            elif inv['amount_tax'] != 0:
                                worksheet.write(inv_row, 7, inv['amount_untaxed'], for_right)
                                untaxed_total += inv['amount_untaxed']

                        if inv['type'] == 'out_refund':
                            worksheet.write(inv_row, 8, inv['amount_tax'] * (-1), for_right)
                            tax_total += inv['amount_tax'] * (-1)

                        else:
                            worksheet.write(inv_row, 8, inv['amount_tax'], for_right)
                            tax_total += inv['amount_tax']

                        if inv['type'] == 'out_refund':
                            if inv['amount_tax'] == 0:
                                worksheet.write(inv_row, 9, inv['amount_untaxed'] * (-1), for_right)
                                sum_total += inv['amount_untaxed'] * (-1)
                            else:
                                worksheet.write(inv_row, 9, '', for_right)
                        else:
                            if inv['amount_tax'] == 0:
                                worksheet.write(inv_row, 9, inv['amount_untaxed'], for_right)
                                sum_total += inv['amount_untaxed']
                            else:
                                worksheet.write(inv_row, 9, '', for_right)
                        if inv['type'] == 'out_refund':
                            worksheet.write(inv_row, 10, (inv['amount_untaxed'] + inv['amount_tax']) * (-1), for_right)
                        else:
                            worksheet.write(inv_row, 10, inv['amount_untaxed'] + inv['amount_tax'], for_right)
                        if inv['state'] == 'cancel':
                            worksheet.write(inv_row, 11, 'ยกเลิก', for_right)
                        else:
                            worksheet.write(inv_row, 11, inv['invoice'], for_right)


                    if inv['state'] == 'cancel':
                        worksheet.write(inv_row, 7, "0", for_right)
                        worksheet.write(inv_row, 8, "0", for_right)
                        worksheet.write(inv_row, 9, "0", for_right)
                        worksheet.write(inv_row, 10, "0", for_right)

                    sl_no += 1

            if pos_session_ids and pos_session_ids['pos']:
                print('pos_session_ids/pos_session_ids/pos_session_ids')
                print('pos_session_ids:',pos_session_ids)
                for inv in pos_session_ids['pos']:
                    session_info = inv.get_order_line()
                    if not session_info:
                        continue
                    elif session_info and not session_info[0]:
                        continue
                    inv_row += 1

                    tax_inv_date = datetime.strptime(inv.start_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

                    worksheet.write(inv_row, 0, sl_no, for_center)
                    worksheet.write(inv_row, 1, tax_inv_date, for_center)
                    if inv.order_ids:
                        if inv.order_ids[0].account_move:
                            worksheet.write(inv_row, 2, inv.order_ids[0].account_move.name, for_left)
                        else:
                            worksheet.write(inv_row, 2, inv.order_ids[0].invoice_id.number, for_left)

                    else:
                        worksheet.write(inv_row, 2, inv.name, for_left)
                    worksheet.write(inv_row, 3, 'Cash', for_center)

                    if session_info[0][0].order_id.partner_id:
                        is_branch_no = session_info[0][0].order_id.partner_id.branch_no
                    else:
                        is_branch_no = '00000'

                    worksheet.write(inv_row, 4, ' ', for_left)
                    if int(is_branch_no):
                        worksheet.write(inv_row, 5, ' ', for_left)
                        worksheet.write(inv_row, 6, is_branch_no or '', for_left)
                    else:
                        worksheet.write(inv_row, 5, is_branch_no or ' ', for_left)
                        worksheet.write(inv_row, 6, ' ', for_left)

                    worksheet.write(inv_row, 7, session_info[1], for_right)
                    worksheet.write(inv_row, 8, session_info[2], for_right)
                    worksheet.write(inv_row, 9, '', for_right)
                    worksheet.write(inv_row, 10, session_info[1] + session_info[2], for_right)
                    untaxed_total += session_info[1]
                    tax_total += session_info[2]

                    sl_no += 1

            if not pos_session_ids and not invoices:
                raise UserError(_('There is invoices between this date range.'))

            inv_row += 1
            worksheet.write(inv_row, 6, 'Total', for_center_bold)
            worksheet.write(inv_row, 7, untaxed_total, for_right_bold)
            worksheet.write(inv_row, 8, tax_total, for_right_bold)
            worksheet.write(inv_row, 9, sum_total, for_right_bold)
            worksheet.write(inv_row, 10, untaxed_total + tax_total + sum_total , for_right_bold)


            # end of the file

        if self.report_type == 'purchase':
            invoice_all = []

            # if self.tax_id.tax_report:
            worksheet.write_merge(0, 1, 0, 8, "รายงานภาษีซื้อ", GREEN_TABLE_HEADER)
            # else:
            #     worksheet.write_merge(0, 1, 0, 8, "รายงานภาษีซื้อยังไม่ถึงกำหนด", GREEN_TABLE_HEADER)

            worksheet.write(3, 1, 'เดือนภาษี', for_left_bold_no_border)
            worksheet.write(3, 2, monthth, for_left_bold_no_border)
            worksheet.write(3, 4, 'ปี', for_left_bold_no_border)
            worksheet.write(3, 5, year, for_left_bold_no_border)

            worksheet.write(5, 1, 'ชื่อผู้ประกอบการ', for_left_bold_no_border)
            worksheet.write(5, 2, company, for_left_bold_no_border)
            worksheet.write(5, 4, 'เลขประจำผู้เสียภาษีอากร', for_left_bold_no_border)
            worksheet.write(5, 5, tax_id, for_left_bold_no_border)

            worksheet.write(7, 1, 'ชื่อสถานประกอบการ', for_left_bold_no_border)
            worksheet.write(7, 2, company_branch, for_left_bold_no_border)
            worksheet.write(7, 4, 'สำนักงานใหญ่ / สาขา', for_left_bold_no_border)
            worksheet.write(7, 5, branch_no, for_left_bold_no_border)

            worksheet.write(9, 1, 'สถานประกอบการ', for_left_bold_no_border)
            worksheet.write(9, 2, company_address, for_left_bold_no_border)

            worksheet.write_merge(inv_row, inv_row_merge_head, 0, 0, "ลำดับที่", for_center_bold)
            worksheet.write_merge(inv_row, inv_row, 1, 2, "ใบกำกับภาษี", for_center_bold)
            worksheet.write(inv_row_merge_head, 1, 'วัน เดือน ปี', for_center_bold)
            worksheet.write(inv_row_merge_head, 2, 'เลขที่', for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 3, 3, "ชื่อผู้ขายสินค้า/ผู้ให้บริการ", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 4, 4,
                                  'เลขประจำตัวผู้เสียภาษีอากรของผู้ขายสินค้า/ผู้ให้บริการ', for_center_bold)
            worksheet.write_merge(inv_row, inv_row, 5, 6, "สถานประกอบการ", for_center_bold)
            worksheet.write(inv_row_merge_head, 5, 'สำนักงานใหญ่', for_center_bold)
            worksheet.write(inv_row_merge_head, 6, 'สาขาที่', for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 7, 7, "มูลค่าสินค้าหรือบริการ", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 8, 8, "จำนวนเงินภาษีมูลค่าเพิ่ม", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 9, 9, "จำนวนเงินรวม", for_center_bold)
            worksheet.write_merge(inv_row, inv_row_merge_head, 10, 10, "หมายเหตุ", for_center_bold)
            #############################  Case 1 #####################################
            domain = [('is_closing_month','=',False)]
            if self.date_from:
                domain.append(('date', '>=', self.date_from))
            if self.date_to:
                domain.append(('date', '<=', self.date_to))
            if self.tax_id:
                domain.append(('account_id', '=', self.tax_id[0].account_id.id))
            else:
                domain.append(('account_id.purchase_tax_report', '=', True))

            if self.operating_unit_id:
                domain.append(('operating_unit_id', '=', self.operating_unit_id.id))

            inv_row += 1
            print('Execl Domain' + str(domain))
            invoices = invoice_obj.search(domain)
            invoices = invoices.filtered(lambda m: m.date == m.date_maturity)

            print('invoices:',invoices)
            if invoices:
                for invoice_id in invoices:
                    if not invoice_id.date_maturity:
                        raise UserError(_("Please check date for item %s" % invoice_id.move_id.name))
                    date_maturity = datetime.strptime(invoice_id.date_maturity, '%Y-%m-%d')
                    if not invoice_id.invoice_date:
                            raise UserError(_("Please check date for item %s" % invoice_id.move_id.name))
                    invoice_date = datetime.strptime(invoice_id.invoice_date, '%Y-%m-%d')

                    date = invoice_id.invoice_date

                    # case old
                    # if date_maturity.month != invoice_date.month:
                    #     date = invoice_id.date_maturity
                    # elif date_maturity.month == invoice_date.month:
                    #     date = invoice_id.invoice_date
                    # else:
                    #     date = invoice_id.date

                    name = invoice_id.ref
                    # if invoice_id.operating_unit_id:
                    #     is_branch_no = invoice_id.operating_unit_id.partner_id.branch_no
                    # elif not invoice_id.operating_unit_id.partner_id.branch_no:
                    #     is_branch_no = invoice_id.operating_unit_id.name
                    # else:
                    #     is_branch_no = invoice_id.partner_id.branch_no

                    if invoice_id.partner_id:
                        partner = invoice_id.partner_id
                        vat = invoice_id.partner_id.vat
                        is_branch_no = invoice_id.partner_id.branch_no
                    else:
                        partner = invoice_id.move_id.supplier_name_text
                        vat = invoice_id.move_id.supplier_taxid_text
                        is_branch_no = invoice_id.operating_unit_id.partner_id.branch_no

                    vals = {
                        'date': date or '',
                        'name': name or '',
                        'partner_id': partner,
                        'vat': vat,
                        'is_branch_no': is_branch_no,
                        'invoice_id': invoice_id.invoice_id,
                        'debit': invoice_id.debit,
                        'credit': invoice_id.credit,
                        'amount_before_tax': invoice_id.amount_before_tax,
                        'move_id': invoice_id.move_id,
                    }
                    invoice_all.append(vals)
            #############################  Case 2 #####################################
            domain = [('is_closing_month', '=', False)]
            if self.date_from:
                domain.append(('date_maturity', '>=', self.date_from))
            if self.date_to:
                domain.append(('date_maturity', '<=', self.date_to))
            if self.tax_id:
                domain.append(('account_id', '=', self.tax_id[0].account_id.id))
            else:
                domain.append(('account_id.purchase_tax_report', '=', True))

            if self.operating_unit_id:
                domain.append(('operating_unit_id', '=', self.operating_unit_id.id))
            inv_row += 1
            invoices = invoice_obj.search(domain)
            invoices = invoices.filtered(lambda m: m.date_maturity != m.date)
            print('invoices:', invoices)
            if invoices:
                for invoice_id in invoices:
                    date = invoice_id.invoice_date
                    name = invoice_id.ref
                    if invoice_id.partner_id:
                        partner = invoice_id.partner_id
                        vat = invoice_id.partner_id.vat
                        is_branch_no = invoice_id.partner_id.branch_no
                    else:
                        partner = invoice_id.move_id.supplier_name_text
                        vat = invoice_id.move_id.supplier_taxid_text
                        is_branch_no = invoice_id.move_id.supplier_branch_text

                    vals = {
                        'date': date or '',
                        'name': name or '',
                        'partner_id': partner,
                        'vat': vat,
                        'is_branch_no': is_branch_no,
                        'invoice_id': invoice_id.invoice_id,
                        'debit': invoice_id.debit,
                        'credit': invoice_id.credit,
                        'amount_before_tax': invoice_id.amount_before_tax,
                        'move_id': invoice_id.move_id,

                    }
                    invoice_all.append(vals)
            invoice_all.sort(key=lambda k: (k['date'], k['name']), reverse=False)
            if invoice_all:
                sl_no = 1
                untaxed_total = tax_total = 0.0
                amount_tax = 0.0
                amount_untax = 0.0
                for inv in invoice_all:
                    inv_row += 1
                    worksheet.write(inv_row, 0, sl_no, for_center)
                    worksheet.write(inv_row, 1, datetime.strptime(inv['date'], '%Y-%m-%d').strftime('%d/%m/%Y') or '', for_center)
                    worksheet.write(inv_row, 2, inv['name'] or '', for_left)
                    if inv['partner_id']:
                        worksheet.write(inv_row, 3, inv['partner_id'].name or '', for_left)
                        worksheet.write(inv_row, 4, inv['partner_id'].vat or '', for_left)
                    else:
                        worksheet.write(inv_row, 3, inv['move_id'].supplier_name_text or '', for_left)
                        worksheet.write(inv_row, 4, inv['move_id'].supplier_taxid_text or '', for_left)

                    if inv['partner_id']:
                        is_branch_no = inv['partner_id'].branch_no
                    else:
                        if inv['invoice_id']:
                            is_branch_no = inv['invoice_id'].operating_unit_idbranch_no
                        else:
                            is_branch_no = inv['move_id'].supplier_branch_text

                    if int(is_branch_no):
                        worksheet.write(inv_row, 5, ' ', for_left)
                        worksheet.write(inv_row, 6, is_branch_no or '', for_left)
                    else:
                        worksheet.write(inv_row, 5, is_branch_no or '', for_left)
                        worksheet.write(inv_row, 6, ' ', for_left)

                    if inv['debit']:
                        amount_tax = inv['debit']
                    elif inv['credit']:
                        amount_tax = inv['credit'] * (-1)
                    else:
                        amount_tax = 0

                    if inv['amount_before_tax']:
                        # print "1"
                        amount_untax = inv['amount_before_tax']
                    elif inv['invoice_id'] and inv['invoice_id'].amount_untaxed:
                        # print "2"
                        amount_untax = inv['invoice_id'].amount_untaxed
                    else:
                        # print "3"
                        amount_untax = amount_tax*100/7

                    # amount_untax = amount_tax*100/7

                    worksheet.write(inv_row, 7, amount_untax, for_right)
                    worksheet.write(inv_row, 8, amount_tax, for_right)
                    worksheet.write(inv_row, 9, amount_untax + amount_tax, for_right)
                    worksheet.write(inv_row, 10, inv['move_id'].name, for_right)
                    sl_no += 1
                    untaxed_total += amount_untax
                    tax_total += amount_tax

                inv_row += 1
                worksheet.write(inv_row, 6, 'Total', for_center_bold)
                worksheet.write(inv_row, 7, untaxed_total, for_right_bold)
                worksheet.write(inv_row, 8, tax_total, for_right_bold)
                worksheet.write(inv_row, 9, untaxed_total + tax_total, for_right_bold)
            else:
                raise UserError(_('There is no invoices between this date range.'))

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE tax_excel_export CASCADE")
        wizard_id = self.env['tax.excel.export'].create(vals={'name': 'Tax Report.xls','report_file': ctx['report_file']})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tax.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class tax_excel_export(models.TransientModel):
    _name = 'tax.excel.export'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)

    # @api.model
    # def create(self, vals):
    #     print vals
    #     return super(tax_excel_export, self).create(vals)

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tax.report',
            'target': 'new',
        }


class pnd53_report(models.TransientModel):
    _name = 'pnd53.report'
    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    report_type = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53')],string='Report Type', required=True)
    month = fields.Char(string='Month')
    company_id = fields.Many2one('res.company')

    @api.model
    def default_get(self, fields):
        res = super(pnd53_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def print_pnd53_report(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'report_type', 'month','company_id'])[0]

        if data['form']['report_type'] == 'company':
            # return self.env['report'].get_action(self, 'thai_accounting.report_pnd53_id', data=data)
            return self.env.ref('thai_accounting.action_report_pnd53_id').report_action(self, data=data,
                                                                                        config=False)
        elif data['form']['report_type'] == 'personal':
            # return self.env['report'].get_action(self, 'thai_accounting.report_pnd3_id', data=data)
            return self.env.ref('thai_accounting.action_report_pnd3_id').report_action(self, data=data,
                                                                                       config=False)
        else:
            # return self.env['report'].get_action(self, 'thai_accounting.report_pnd2_id', data=data)
            return self.env.ref('thai_accounting.action_report_pnd2_id').report_action(self, data=data,
                                                                                       config=False)
