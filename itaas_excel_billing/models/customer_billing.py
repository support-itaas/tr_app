# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).

from odoo import models, fields, api
from io import BytesIO
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
import xlwt

class Customer_billing_excel_inherit(models.TransientModel):
    _name = 'customer.billing.excel'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    name_from = fields.Char(string='Name From')
    name_to = fields.Char(string='Name To')
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate'), ('confirm', 'Confirm'), ('cancel', 'Cancel')], string='State',default='draft')

    @api.multi
    def print_report(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center;")
        for_right.num_format_str = '#,##0.00'
        # for_right_bold = xlwt.easyxf(
        #     "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        # for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 200;  align: horiz left,vertical center;")

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

        # if self.state:
        #     customer_billing_ids = self.env['customer.billing'].sudo().search([
        #         ('state', '=' ,self.state),
        #         ('date_billing' ,'>=',self.date_from),
        #         ('date_billing' ,'<=',self.date_to)])
        # else:
        if self.name_from and self.name_to:
            customer_billing_ids = self.env['customer.billing'].sudo().search([
                ('name', '>=', self.name_from),
                ('name', '<=', self.name_to),
                ('type', '=', 'out_invoice'),
            ])

            print('customer_billing_ids:',customer_billing_ids)
        else:
            customer_billing_ids = self.env['customer.billing'].sudo().search([
                ('date_billing', '>=', self.date_from),
                ('date_billing', '<=', self.date_to),
                ('type', '=', 'out_invoice'),
            ])

        inv_row = 1
        worksheet = workbook.add_sheet('Customer Billing')
        worksheet.write_merge(0, 0, 0, 8, 'รายงาน Customer BIlling', GREEN_TABLE_HEADER)
        i = 0

        for customer_billing_id in customer_billing_ids:
            i += 1
            inv_row += 1
            worksheet.write(inv_row, 0, 'เลขที่', for_center_bold)
            worksheet.write(inv_row, 1, 'วันที่', for_center_bold)
            worksheet.write(inv_row, 2, 'ชื่อรายการ', for_center_bold)
            worksheet.write(inv_row, 3, 'ลูกค้า', for_center_bold)
            worksheet.write(inv_row, 4, 'Untaxed Amount', for_center_bold)
            worksheet.write(inv_row, 5, 'Tax', for_center_bold)
            worksheet.write(inv_row, 6, 'Total', for_center_bold)
            inv_row += 1

            worksheet.write(inv_row, 0, i, for_center)
            worksheet.write(inv_row, 1, customer_billing_id.date_billing, for_center)
            worksheet.write(inv_row, 2, customer_billing_id.name, for_center)
            worksheet.write(inv_row, 3, customer_billing_id.partner_id.name, for_center)
            worksheet.write(inv_row, 4, customer_billing_id.amount_untaxed, for_center)
            worksheet.write(inv_row, 5, customer_billing_id.amount_tax, for_center)
            worksheet.write(inv_row, 6, customer_billing_id.amount_total, for_center)

            inv_row += 1
            worksheet.write(inv_row, 1, 'Number', for_center_bold)
            worksheet.write(inv_row, 2, 'Company', for_center_bold)
            worksheet.write(inv_row, 3, 'Salesperson', for_center_bold)
            worksheet.write(inv_row, 4, 'Due Date', for_center_bold)
            worksheet.write(inv_row, 5, 'Source Document', for_center_bold)
            worksheet.write(inv_row, 6, 'Tax', for_center_bold)
            worksheet.write(inv_row, 7, 'Total in invoice Currency', for_center_bold)
            worksheet.write(inv_row, 8, 'Amount Due in invoice Currency', for_center_bold)

            for billing_line in customer_billing_id.invoice_ids:

                inv_row += 1
                worksheet.write(inv_row, 1, billing_line.number, for_center)
                worksheet.write(inv_row, 2, billing_line.company_id.name, for_center)
                worksheet.write(inv_row, 3, billing_line.user_id.name, for_center)
                worksheet.write(inv_row, 4, billing_line.date_due, for_center)
                worksheet.write(inv_row, 5, billing_line.origin, for_center)
                worksheet.write(inv_row, 6, billing_line.amount_tax, for_center)
                worksheet.write(inv_row, 7, billing_line.amount_total_signed, for_center)
                worksheet.write(inv_row, 8, billing_line.residual_signed, for_center)
            inv_row += 1
        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['customer.billing.export'].create(
            vals={'name': 'Customer Billing Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.billing.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }



class customer_billing_export(models.TransientModel):
    _name = 'customer.billing.export'

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
            'res_model': 'customer.billing.excel',
            'target': 'new',
        }

