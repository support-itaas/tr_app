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
from dateutil.relativedelta import relativedelta

# this is for tax report section
class export_edi_report(models.TransientModel):
    _name = 'export.edi.report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    customer = fields.Many2one('res.partner', string='Customer')

    @api.model
    def default_get(self, fields):
        res = super(export_edi_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 0o1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        customer = self.env['res.partner'].sudo().search([('name', 'like', 'บริษัท บิ๊กซี'),] , limit=1)
        res.update({'date_from': str(from_date), 'date_to': str(to_date), 'customer':customer.id})
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
                pre += " "
            word = pre + word
            # print("if-2" + word)
        else:
            word = str(word)
            # print("else-2" + word)

        if word and len(word) < num:
            for count in range(len(word), num):
                pre += " "
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
    def get_edi_report(self):
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

        # get-----------------------------------------------------------------------------------------

        domain = [('date_invoice', '>=', self.date_from),
                  ('date_invoice', '<=', self.date_to),
                  ('state', '=', 'open'),
                  ('type', '=', 'out_invoice')]

        if self.customer:
            domain.append(('partner_id', '=', self.customer.id))

        # print(domain)

        invoice_all = self.env['account.invoice'].sudo().search(domain)
        invoice_all_id = [x.id for x in invoice_all]
        invoice_line = self.env['account.invoice.line'].sudo().search(
            [('invoice_id', 'in', invoice_all_id)], order='invoice_id asc')

        worksheet = workbook.add_sheet('report')

        number_old = ""

        worksheet.write(1, 0, "Date From", for_center_bold)
        worksheet.write(1, 1, self.date_from, for_left)
        worksheet.write(1, 8, "Date To", for_center_bold)
        worksheet.write(1, 9, self.date_to, for_left)

        worksheet.write(3, 0, "Number", for_center_bold)
        worksheet.write(3, 1, "Amount Total", for_center_bold)
        worksheet.write(3, 2, "Date Invoice", for_center_bold)
        worksheet.write(3, 3, "No.", for_center_bold)
        worksheet.write(3, 4, "Source doc", for_center_bold)
        worksheet.write(3, 5, "Amount Untax", for_center_bold)
        worksheet.write(3, 6, "7.00", for_center_bold)
        worksheet.write(3, 7, "Product Code", for_center_bold)
        worksheet.write(3, 8, "Qty", for_center_bold)
        worksheet.write(3, 9, "Unit Price", for_center_bold)

        inv_row = 3

        if invoice_line:
            for il in sorted(invoice_line, key=lambda line: line.invoice_id.number):
                number = il.invoice_id.number
                amount_total = self._get_prefix_word(str("{0:.5f}".format(il.invoice_id.amount_total)),16)
                date = (datetime.strptime(il.invoice_id.date_invoice , "%Y-%m-%d") + relativedelta(years=543)).strftime("%d/%m/%Y")
                date_invoice = str(date)

                if number_old == number:
                    num_invoice_line = num_invoice_line+1
                else:
                    num_invoice_line = 1
                    number_old = number
                num = self._get_prefix_word(num_invoice_line,3)
                source_doc = il.invoice_id.name or ""
                amount_untax = self._get_prefix_word(str("{0:.5f}".format(il.invoice_id.amount_untaxed)),16)
                product_code =  il.product_id.barcode or ""
                qty = self._get_prefix_word(str("{0:.3f}".format(il.quantity)),9)
                unit_price = str(self._get_prefix_word(str("{0:.5f}".format(il.price_unit)),15))

                final_text_body = number + ",,," + amount_total + ",1,1,0205539002146,,," \
                                  + date_invoice + "," + num + "," \
                                  + source_doc + "," + amount_untax +","+ amount_total \
                                  + ", 7.00," + product_code + "," + qty + "," + unit_price+", " + "0"

                final_text += final_text_body + "\r\n"

                inv_row = inv_row+1

                worksheet.write(inv_row, 0, number, for_left)
                worksheet.write(inv_row, 1, amount_total, for_right)
                worksheet.write(inv_row, 2, date_invoice, for_left)
                worksheet.write(inv_row, 3, num, for_right)
                worksheet.write(inv_row, 4, source_doc, for_left)
                worksheet.write(inv_row, 5, amount_untax, for_right)
                worksheet.write(inv_row, 6, "7.00", for_right)
                worksheet.write(inv_row, 7, product_code, for_right)
                worksheet.write(inv_row, 8, qty, for_right)
                worksheet.write(inv_row, 9, unit_price, for_right)

        else:
            raise UserError(_('There is record this date range.'))

        # ------------------------------------ End -------------------------------------------------

        if file_type == 'xls':

            workbook.save(fl)
            fl.seek(0)

            buf = base64.encodestring(fl.read())
            cr, uid, context = self.env.args
            ctx = dict(context)
            ctx.update({'report_file': buf})
            self.env.args = cr, uid, misc.frozendict(context)
            ## To remove those previous saved report data from table. To avoid unwanted storage
            self._cr.execute("TRUNCATE export_edi_excel_export CASCADE")

            wizard_id = self.env['export.edi.excel.export'].create(vals={'name': 'EDI Report.xls',
                                                                      'report_file': ctx['report_file']})

            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'export.edi.excel.export',
                'target': 'new',
                'context': ctx,
                'res_id': wizard_id.id,
            }

        elif file_type == 'dat':
            # final_text
            values = {
                'name': "Export to EDI Report",
                'datas_fname': 'Edireport.dat',
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
                'name': "Export to EDI Report",
                'datas_fname': 'Edireport.txt',
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


class export_edi_excel_export(models.TransientModel):
    _name = 'export.edi.excel.export'

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
            'res_model': 'export.edi.report',
            'target': 'new',
        }

