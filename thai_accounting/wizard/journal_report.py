# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from datetime import datetime
from odoo import tools
# from odoo.osv import fields, osv
from odoo.tools.translate import _
from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
#import xlwt
#import base64
from odoo.exceptions import UserError
from odoo.tools import misc



class journal_report(models.TransientModel):
    _name = 'wizard.journal.report'

    # journal_id = fields.Many2one('account.journal',string="สมุดบัญชี")
    journal_ids = fields.Many2many('account.journal',string="Journal",required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    type = fields.Selection([
        ('detail','Detail'),
        ('summary', 'Summary'),
    ],default='detail')

    @api.model
    def default_get(self, fields):
        res = super(journal_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def print_report_pdf(self, data):

        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'type', 'journal_ids'])[0]
        # return self.env['report'].get_action(self, 'thai_accounting.journal_daily_report', data=data)
        return self.env.ref('thai_accounting.action_debitcredit_report_detail').report_action(self, data=data, config=False)

    def print_report_summary_pdf(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'type', 'journal_ids'])[0]
        return self.env.ref('thai_accounting.action_debitcredit_report_summary').report_action(self, data=data,
                                                                                              config=False)
        # return self.env['report'].get_action(self, 'thai_accounting.journal_summary_report', data=data)

    @api.multi
    def print_report_excel(self):
        fl = StringIO()
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

        worksheet = workbook.add_sheet('Purchase')

        worksheet.row(0).height = 200
        worksheet.col(0).width = 1500
        worksheet.col(1).width = 3000
        worksheet.col(2).width = 7000
        worksheet.col(3).width = 7000
        worksheet.col(4).width = 3000
        worksheet.col(5).width = 3000
        worksheet.col(6).width = 3000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
        worksheet.col(10).width = 4000
        worksheet.col(11).width = 3000
        worksheet.col(12).width = 3000
        worksheet.col(13).width = 3000
        worksheet.col(14).width = 3000
        worksheet.col(15).width = 3000
        worksheet.col(16).width = 3000
        worksheet.col(17).width = 3000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        inv_row = 2
        customer_obj = self.env['purchase.order']

        # if self.agent_id.name == 'KLine':
        worksheet.write_merge(1, 1, 0, 17, 'รวมข้อมูลรายการจัดซื้อ', GREEN_TABLE_HEADER)

        worksheet.write(inv_row, 0, '#', for_center_bold)
        worksheet.write(inv_row, 1, 'Reference', for_center_bold)
        worksheet.write(inv_row, 2, 'Operation Date', for_center_bold)
        worksheet.write(inv_row, 3, 'Job Number', for_center_bold)
        worksheet.write(inv_row, 4, 'Job Order', for_center_bold)
        worksheet.write(inv_row, 5, 'Customer', for_center_bold)
        worksheet.write(inv_row, 6, 'Vendor', for_center_bold)
        worksheet.write(inv_row, 7, 'Payment Type', for_center_bold)
        worksheet.write(inv_row, 8, 'Quantity', for_center_bold)
        worksheet.write(inv_row, 9, 'Team Quantity', for_center_bold)
        worksheet.write(inv_row, 10, 'Drescription Name', for_center_bold)
        worksheet.write(inv_row, 11, 'Branch', for_center_bold)
        worksheet.write(inv_row, 12, 'Type Of Service', for_center_bold)
        worksheet.write(inv_row, 13, 'Operation Type', for_center_bold)
        worksheet.write(inv_row, 14, 'Withoding Tax', for_center_bold)
        worksheet.write(inv_row, 15, 'Status', for_center_bold)
        worksheet.write(inv_row, 16, 'Invoice Status', for_center_bold)
        worksheet.write(inv_row, 17, 'Untaxed', for_center_bold)
        worksheet.write(inv_row, 18, 'Total', for_center_bold)

        domain = []

        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))

        i = 0
        customer_rec = customer_obj.search(domain)
        # print len(customer_rec)

        if customer_rec:
            for exp in customer_rec:
                # print exp.user_id
                inv_row += 1
                i += 1
                worksheet.write(inv_row, 0, i, for_center)
                worksheet.write(inv_row, 1, exp.name, for_center)
                worksheet.write(inv_row, 2, exp.date_order1, for_center)
                worksheet.write(inv_row, 3, exp.project_id.job_code, for_center)
                worksheet.write(inv_row, 4, exp.product_id.name, for_center)
                if exp.customer_id.parent_id:
                    worksheet.write(inv_row, 5, exp.customer_id.parent_id.name, for_center)
                else:
                    worksheet.write(inv_row, 5, exp.customer_id.name, for_center)
                worksheet.write(inv_row, 6, exp.partner_id.name, for_center)
                worksheet.write(inv_row, 7, exp.payment_type.name, for_center)
                worksheet.write(inv_row, 8, exp.job_qty, for_center)
                worksheet.write(inv_row, 9, exp.team_qty, for_center)
                worksheet.write(inv_row, 10, exp.timesheet_id.name, for_center)
                worksheet.write(inv_row, 11, exp.task_id.branch_ids.name, for_center)
                worksheet.write(inv_row, 13, exp.jobtype, for_center)
                worksheet.write(inv_row, 14, exp.emp_wht, for_center)
                worksheet.write(inv_row, 15, exp.state, for_center)
                worksheet.write(inv_row, 16, exp.invoice_status, for_center)
                worksheet.write(inv_row, 17, exp.amount_untaxed, for_center)
                worksheet.write(inv_row, 18, exp.amount_total, for_center)
                # if exp.prod_categ_ids:
                produ = ""
                if exp.prod_categ_ids:
                    for prod in exp.prod_categ_ids:  # Second Example
                        # inv_row += 1
                        produ += prod.name
                        produ += ","

                worksheet.write(inv_row, 12, produ, for_center)
                # exp.prod_categ_ids.name
                # else:
                #     worksheet.write(inv_row, 12, '', for_center)

        else:
            raise UserError(_('There is record this date range.'))

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE addpurchase_excel_export CASCADE")
        wizard_id = self.env['addpurchase.excel.export'].create(vals={'name': 'Purchase Report.xls','report_file': ctx['report_file']})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'addpurchase.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class addpurchase_excel_export(models.TransientModel):
    _name = 'addpurchase.excel.export'

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
            'res_model': 'addpurchase.report',
            'target': 'new',
        }
