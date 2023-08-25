# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import datetime,date
from datetime import timedelta
import calendar
import xlwt
from io import BytesIO
import base64
from odoo.tools import misc


from odoo import fields, models, api, _
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class payroll_wizard(models.Model):
    _name = 'payroll.wizard.detail'

    period_id = fields.Many2one('hr.period', string='Period')
    operating_unit = fields.Many2one('operating.unit', string="Operating Unit")
    con_branch_id = fields.Many2one('contract.branch', string='Contract Branch')
    salary_struct = fields.Many2one('hr.payroll.structure',string='Salary Structures')


    def print_report_pdf(self, data):
        data = {}
        data['form'] = self.read(['period_id', 'con_branch_id', 'salary_struct','operating_unit'])[0]
        return self.env.ref('wizard_payroll_report.action_payroll_salary_wizard').report_action(self, data=data, config=False)


    def print_report_excel(self):
        data = {}
        data['form'] = self.read(['period_id', 'con_branch_id', 'salary_struct','operating_unit'])[0]
        print('data:',data)
        report_values = self.env['report.wizard_payroll_report.payroll_salary_report'].get_report_values(self,data=data)
        print('report_values_all:',report_values)
        report_values_docs = report_values.get('docs')
        report_values_rule_ids = report_values.get('rule_ids')
        print('report_values_docs:',report_values_docs)
        print('report_values_rule_ids:',report_values_rule_ids)
        fl = BytesIO()
        company_id = self.env.user.company_id
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet 1')
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
        for_left_new = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_left_new.num_format_str = '#,###.00'
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name  Times New Roman, height 300,color black;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top thin, bottom thin, left thin, right thin;'
            'pattern:  pattern_fore_colour white, pattern_back_colour white'
        )


        inv_row = 3
        inv_colum_rule = 5
        worksheet.write_merge(0, 1, 0, 4, "รายงานเงินเดือนรายงวด", GREEN_TABLE_HEADER)
        worksheet.write(2, 0,'รหัส', for_center_bold)
        worksheet.write(2, 1,'ชื่อพนักงาน', for_center_bold)
        worksheet.write(2, 2,'ตำแหน่ง', for_center_bold)
        worksheet.write(2, 3,'งวดที่', for_center_bold)
        worksheet.write(2, 4,'ปิดงวดรับที่', for_center_bold)
        for rule_ids in report_values_rule_ids:
            worksheet.write(2, inv_colum_rule, rule_ids.name, for_center_bold)
            inv_colum_rule += 1
        worksheet.write(2, inv_colum_rule,'ยอดเงินสุทธิ', for_center_bold)
        print('report_values_docs:',report_values_docs)
        for docs in report_values_docs:
            print('docscccc:',docs)
            count = 0
            inv_colum_doc = 0
            sum_line = 0
            for doc in docs:
                if count >= 5:
                    sum_line += doc
                if inv_colum_doc == 1:
                    worksheet.write(inv_row, inv_colum_doc, doc  or '', for_left)
                elif inv_colum_doc == 3:
                    name = str(doc) + '/12'
                    worksheet.write(inv_row, inv_colum_doc, name  or '', for_center)
                elif inv_colum_doc == 4:
                    date_edit = datetime.strptime(doc, "%Y-%m-%d").strftime('%d/%m/%Y')
                    worksheet.write(inv_row, inv_colum_doc, date_edit or '', for_center)
                elif inv_colum_doc > 4:
                    worksheet.write(inv_row, inv_colum_doc, doc or '0.00', for_right_bold)
                else:
                    worksheet.write(inv_row, inv_colum_doc, doc or '', for_center)

                inv_colum_doc += 1
                count += 1
            worksheet.write(inv_row, inv_colum_doc, sum_line or '', for_right_bold)

            inv_row += 1

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE tax_excel_export CASCADE")
        wizard_id = self.env['payroll.excel.export'].create(
            vals={'name': 'Payroll Report.xls', 'report_file': ctx['report_file']})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

class payroll_excel_export(models.TransientModel):
    _name = 'payroll.excel.export'

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
            'res_model': 'payroll.wizard.detail',
            'target': 'new',
        }

