#-*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
from io import BytesIO
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
import locale
from datetime import datetime,timedelta,date

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

# this is for tax report section
class creditor_report(models.TransientModel):
    _name = 'creditor.report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    vendor_id = fields.Many2one('res.partner',string='Supplier/Employee')
    status_id = fields.Selection([('draft','Draft'),('open','Open'),('paid','Paid')],default='open',string='Status')

    @api.model
    def default_get(self, fields):
        res = super(creditor_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    ###############################
    # @api.model
    # def default_get(self, fields):
    #     res = super(customer_report, self).default_get(fields)
    #     curr_date = datetime.now()
    #     from_date = datetime(curr_date.year, curr_date.month, 01).date() or False
    #     to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
    #     res.update({'date_from': str(from_date), 'date_to': str(to_date)})
    #     return res
    ###############################

    def get_analytic_account(self,invoice_id):
        # print invoice_id.number
        project_ids = []
        project_str = ""
        count = 0
        for line in invoice_id.invoice_line_ids:
            count +=1
            # print count
            if line.account_analytic_id and line.account_analytic_id not in project_ids:
                project_ids.append(line.account_analytic_id)
                # print line.account_analytic_id.name


        if project_ids:
            # print len(project_ids)
            for project in project_ids:
                project_str += project.name
                project_str += ","
                # print project.name

        return project_str


    @api.multi
    def print_report(self):
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


        worksheet = workbook.add_sheet('AP Report')


        worksheet.row(0).height = 200
        worksheet.col(0).width = 1500
        worksheet.col(1).width = 3000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4000
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
        worksheet.col(18).width = 7000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        inv_row = 4
        customer_obj = self.env['account.invoice']

        worksheet.write_merge(1, 1, 0, 12, self.env.user.company_id.name, GREEN_TABLE_HEADER)

        if self.date_from and self.date_to:
            worksheet.write_merge(2, 2, 0, 12, datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d/%m/%Y') + ' - ' + datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d/%m/%Y'), GREEN_TABLE_HEADER)
        elif self.date_to:
            worksheet.write_merge(2, 2, 0, 12,' Date: ' + datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d/%m/%Y'),
                                  GREEN_TABLE_HEADER)
        worksheet.write_merge(3, 3, 0, 9, 'ตารางเจ้าหนี้', GREEN_TABLE_HEADER)

        worksheet.write(inv_row, 0, 'No.', for_center_bold)
        worksheet.write(inv_row, 1, 'Vendor', for_center_bold)
        worksheet.write(inv_row, 2, 'Bill Date', for_center_bold)
        worksheet.write(inv_row, 3, 'Due Date', for_center_bold)
        worksheet.write(inv_row, 4, 'Number', for_center_bold)
        worksheet.write(inv_row, 5, 'Untax (Amount)', for_center_bold)
        worksheet.write(inv_row, 6, 'Tax (Amount)', for_center_bold)
        worksheet.write(inv_row, 7, 'Total', for_center_bold)
        worksheet.write(inv_row, 8, 'Bill ReferenceNumber', for_center_bold)
        worksheet.write(inv_row, 9, 'Source Document', for_center_bold)
        worksheet.write(inv_row, 10, 'Over Due', for_center_bold)
        worksheet.write(inv_row, 11, 'Current Status', for_center_bold)
        worksheet.write(inv_row, 12, 'ยอดค้างชำระ', for_center_bold)




        domain = ['|',('type', '=', 'in_invoice'),('type', '=', 'in_refund')]

        if self.date_from:
            domain.append(('date_due','>=',self.date_from))
        if self.date_to:
            domain.append(('date_due','<=',self.date_to))
        if self.vendor_id:
            domain.append(('partner_id','=',self.vendor_id.id))

        if self.status_id:
            domain.append(('state', '=', self.status_id))
        else:
            domain.append(('state', 'not in', ('draft','cancel')))



        i = 0
        customer_rec = customer_obj.search(domain,order='partner_id asc,date_due asc')
            # print len(customer_rec)
        date_today = datetime.today().date()
        sum_untaxed = 0.0
        sum_tax = 0.0
        sum_total = 0.0
        sum_all_untaxed = 0.0
        sum_all_tax = 0.0
        sum_all_total = 0.0
        sum_pending = 0
        if customer_rec:
            for exp in customer_rec:
                if exp.state == 'paid' and exp.payment_move_line_ids:
                    if exp.payment_move_line_ids[0].date < self.date_to:
                        continue
                # print exp.user_id
                inv_row += 1
                i += 1
                worksheet.write(inv_row, 0, i, for_center)
                if exp.partner_id:
                    worksheet.write(inv_row, 1, exp.partner_id.name, for_left)
                else:
                    worksheet.write(inv_row, 1, '', for_center)
                if exp.date_invoice:
                    worksheet.write(inv_row, 2, datetime.strptime(exp.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),for_center)
                else:
                    worksheet.write(inv_row, 2, "", for_center)
                if exp.date_due:
                    worksheet.write(inv_row, 3, datetime.strptime(exp.date_due, '%Y-%m-%d').strftime('%d/%m/%Y'),for_center)
                else:
                    worksheet.write(inv_row, 3, "",for_center)
                if exp.number:
                    worksheet.write(inv_row, 4, exp.number, for_center)
                else:
                    worksheet.write(inv_row, 4, '', for_center)

                if exp.type == 'in_invoice':

                    if exp.currency_id.id != exp.company_id.currency_id.id:

                        new_amount_untaxed = exp.currency_id.with_context(date=exp.date_invoice).compute(exp.amount_untaxed, exp.company_id.currency_id)
                        new_amount_tax = exp.currency_id.with_context(date=exp.date_invoice).compute(exp.amount_tax, exp.company_id.currency_id)
                        new_amount_total = exp.currency_id.with_context(date=exp.date_invoice).compute(exp.amount_total, exp.company_id.currency_id)

                        new_residual = exp.currency_id.with_context(date=exp.date_invoice).compute(
                            exp.residual,
                            exp.company_id.currency_id)


                        worksheet.write(inv_row, 5, locale.format("%.2f", float(new_amount_untaxed), grouping=True),
                                        for_right)
                        sum_untaxed += new_amount_untaxed
                        worksheet.write(inv_row, 6, locale.format("%.2f", float(new_amount_tax), grouping=True), for_right)
                        sum_tax += new_amount_tax
                        worksheet.write(inv_row, 7, locale.format("%.2f", float(new_amount_total), grouping=True),
                                        for_right)
                        sum_total += new_amount_total

                        worksheet.write(inv_row, 12,
                                        locale.format("%.2f", float(new_residual), grouping=True), for_right)
                        sum_pending += round(new_residual, 2)



                    else:
                        worksheet.write(inv_row, 5, locale.format("%.2f", float(exp.amount_untaxed), grouping=True), for_right)
                        sum_untaxed += exp.amount_untaxed
                        worksheet.write(inv_row, 6, locale.format("%.2f", float(exp.amount_tax), grouping=True), for_right)
                        sum_tax += exp.amount_tax
                        worksheet.write(inv_row, 7, locale.format("%.2f", float(exp.amount_total), grouping=True), for_right)
                        sum_total += exp.amount_total
                        worksheet.write(inv_row, 12,
                                        locale.format("%.2f", float(exp.residual), grouping=True), for_right)
                        sum_pending += round(exp.residual, 2)


                else:
                    if exp.currency_id.id != exp.company_id.currency_id.id:

                        new_amount_untaxed = exp.currency_id.with_context(date=exp.date_invoice).compute(
                            exp.amount_untaxed, exp.company_id.currency_id)
                        new_amount_tax = exp.currency_id.with_context(date=exp.date_invoice).compute(exp.amount_tax,
                                                                                                     exp.company_id.currency_id)
                        new_amount_total = exp.currency_id.with_context(date=exp.date_invoice).compute(exp.amount_total,
                                                                                                       exp.company_id.currency_id)

                        new_residual = exp.currency_id.with_context(date=exp.date_invoice).compute(
                            exp.residual,
                            exp.company_id.currency_id)
                        worksheet.write(inv_row, 5, locale.format("%.2f", float(new_amount_untaxed*(-1)), grouping=True),
                                        for_right)
                        sum_untaxed += new_amount_untaxed*(-1)
                        worksheet.write(inv_row, 6, locale.format("%.2f", float(new_amount_tax*(-1)), grouping=True),
                                        for_right)
                        sum_tax += new_amount_tax*(-1)
                        worksheet.write(inv_row, 7, locale.format("%.2f", float(new_amount_total*(-1)), grouping=True),
                                        for_right)
                        sum_total += new_amount_total*(-1)


                        worksheet.write(inv_row, 12,
                                        locale.format("%.2f", float(new_residual * (-1)), grouping=True), for_right)
                        sum_pending += round(new_residual* (-1), 2)

                    else:
                        worksheet.write(inv_row, 5, locale.format("%.2f", float(exp.amount_untaxed*(-1)), grouping=True),
                                        for_right)
                        sum_untaxed += exp.amount_untaxed*(-1)
                        worksheet.write(inv_row, 6, locale.format("%.2f", float(exp.amount_tax*(-1)), grouping=True),
                                        for_right)
                        sum_tax += exp.amount_tax*(-1)
                        worksheet.write(inv_row, 7, locale.format("%.2f", float(exp.amount_total*(-1)), grouping=True),
                                        for_right)
                        sum_total += exp.amount_total*(-1)
                        worksheet.write(inv_row, 12,
                                        locale.format("%.2f", float(exp.residual * (-1)), grouping=True), for_right)
                        sum_pending += round(exp.residual * (-1), 2)

                if exp.billing_id.name:
                    worksheet.write(inv_row, 8, exp.billing_id.name, for_center)
                else:
                    worksheet.write(inv_row, 8, exp.reference, for_center)
                if exp.origin:
                    worksheet.write(inv_row, 9, exp.origin, for_center)
                else:
                    worksheet.write(inv_row, 9, '', for_center)

                if exp.date_due:
                    date_due = exp.date_due
                else:
                    date_due = exp.date_invoice

                over_due = str((strToDate(self.date_to) - strToDate(date_due)).days)

                if int(over_due) <= 0:
                    worksheet.write(inv_row, 10, '0', for_center)
                else:
                    worksheet.write(inv_row, 10, over_due, for_center)


                worksheet.write(inv_row, 11, exp.state, for_center)


            inv_row +=1
            worksheet.write(inv_row, 4, "Total", for_center)
            worksheet.write(inv_row, 5, locale.format("%.2f", float(sum_untaxed), grouping=True), for_right)
            sum_all_untaxed += sum_untaxed
            worksheet.write(inv_row, 6, locale.format("%.2f", float(sum_tax), grouping=True), for_right)
            sum_all_tax += sum_tax
            worksheet.write(inv_row, 7, locale.format("%.2f", float(sum_total), grouping=True), for_right)
            worksheet.write(inv_row, 12, locale.format("%.2f", float(sum_pending), grouping=True), for_right)
            sum_all_total += sum_total

        else:
            raise UserError(_('There is record this date range.'))

        # inv_row += 1
        # worksheet.write_merge(inv_row, inv_row, 0, 4, 'รวม', for_right)
        # worksheet.write(inv_row, 5, locale.format("%.2f", float(sum_all_untaxed), grouping=True), for_right)
        # worksheet.write(inv_row, 6, locale.format("%.2f", float(sum_all_tax), grouping=True), for_right)
        # worksheet.write(inv_row, 7, locale.format("%.2f", float(sum_all_total), grouping=True), for_right)

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE creditor_excel_export CASCADE")
        wizard_id = self.env['creditor.excel.export'].create(vals={'name': 'Creditor Report.xls','report_file': ctx['report_file']})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'creditor.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class creditor_excel_export(models.TransientModel):
    _name = 'creditor.excel.export'

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
            'res_model': 'creditor.report',
            'target': 'new',
        }

