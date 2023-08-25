#-*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import misc
from io import StringIO
import io
from io import BytesIO
import itertools
from lxml import etree
import time
import xlwt
from decimal import *
import pytz
import base64
import locale
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)



#this is for tax report section
class asset_report(models.TransientModel):
    _inherit = 'asset.report'


    account_id = fields.Many2one('account.account',string='Account')




    @api.multi
    def print_report(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
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
        cr, uid, context = self.env.args

        # user = self.env['res.users'].browse(uid)
        # company = user.company_id and user.company_id.name or ''
        # company_branch = user.company_id and user.company_id.name or ''
        # tax_id = user.company_id and user.company_id.vat or ''
        # branch_no = user.company_id and user.company_id.branch_no or ''

        #---------------------------- start ------------------------------

        worksheet = workbook.add_sheet('Asset')

        worksheet.row(0).height = 200
        worksheet.col(0).width = 3000
        worksheet.col(1).width = 3000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 3000
        worksheet.col(4).width = 3000
        worksheet.col(5).width = 3000
        worksheet.col(6).width = 3000
        worksheet.col(7).width = 3000
        worksheet.col(8).width = 3000
        worksheet.col(9).width = 3000

        # ---------------------------- End ------------------------------

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders
        # ---------------------------- start ------------------------------

        inv_row = 4
        depreciation_line_obj = self.env['account.asset.depreciation.line']

        worksheet.write_merge(0, 0, 0, 9, self.env.user.company_id.name, GREEN_TABLE_HEADER)
        worksheet.write_merge(1, 1, 0, 9, 'รายงานค่าเสื่อมราคา', GREEN_TABLE_HEADER)
        worksheet.write_merge(2, 2, 0, 9, 'รอบระยะเวลาบัญชีตั้งแต่ ' + strToDate(self.date_from).strftime(
            "%d/%m/%Y") + " - " + strToDate(self.date_to).strftime("%d/%m/%Y"), GREEN_TABLE_HEADER)
        if self.account_id:
            worksheet.write_merge(3, 3, 0, 9, str(self.account_id.code) + ':' + str(self.account_id.name), GREEN_TABLE_HEADER)

        worksheet.write(inv_row, 0, 'ลำดับ', for_center_bold)
        worksheet.write(inv_row, 1, 'รหัส', for_center_bold)
        worksheet.write(inv_row, 2, 'รายการทรัพย์สิน', for_center_bold)
        worksheet.write(inv_row, 3, 'วันที่ซื้อ', for_center_bold)
        worksheet.write(inv_row, 4, 'ราคาทรัพย์สิน', for_center_bold)
        worksheet.write(inv_row, 5, 'ร้อยละ', for_center_bold)
        worksheet.write(inv_row, 6, 'ทรัพย์สินต้นงวด-ยอดยกมา', for_center_bold)
        worksheet.write(inv_row, 7, 'ค่าเสื่อมราคาสะสม-ยกมาต้นปี', for_center_bold)
        worksheet.write(inv_row, 8, 'ค่าเสื่อมราคาสะสม-ระหว่างปี', for_center_bold)
        worksheet.write(inv_row, 9, 'ค่าเสื่อมราคาสะสมรวม', for_center_bold)
        worksheet.write(inv_row, 10, 'ทรัพย์สินสุทธิ-ยอดยกไป', for_center_bold)
        worksheet.write(inv_row, 11, 'มูลค่าซาก', for_center_bold)
        worksheet.write(inv_row, 12, 'วันที่ขาย', for_center_bold)
        worksheet.write(inv_row, 13, 'เลขที่บัญชี-ค่าเสื่อมราคาสะสม', for_center_bold)
        worksheet.write(inv_row, 14, 'เลขที่บัญชี-ค่าเสื่อมราคา', for_center_bold)
        worksheet.write(inv_row, 15, 'Serial Number', for_center_bold)

        if self.account_id:
            asset_category_ids = self.env['account.asset.category'].search([('account_asset_id','=',self.account_id.id)])
        elif self.category_id:
            asset_category_ids = self.category_id
        else:
            asset_category_ids = self.env['account.asset.category'].search([])



        for category_id in asset_category_ids:
            i = 0
            domain = [('move_check', '=', True), ('asset_id.state', 'in', ('open', 'close'))]
            if self.date_from:
                domain.append(('depreciation_date', '>=', self.date_from))
            if self.date_to:
                domain.append(('depreciation_date', '<=', self.date_to))
            if self.department_id:
                domain.append(('asset_id.department_id', '=', self.department_id.id))

            domain.append(('asset_id.category_id', '=', category_id.id))
            inv_row += 1
            # ------------start write to excel--------------------------
            worksheet.write_merge(inv_row, inv_row, 0, 9, category_id.name, for_left)
            depreciation_line_ids = depreciation_line_obj.search(domain,
                                                                 order='category_id asc,asset_id asc,depreciation_date')
            depreciation_lines = {}
            sum_purchase_value = sum_net_depreciated_amount = sum_previous_depreciated_amount = sum_start_year_depreciated_amount = sum_amount = sum_next_depreciated_amount = 0
            sum_savage_amount = 0
            asset_ids = []
            if depreciation_line_ids:
                print('depreciation_line_ids:',depreciation_line_ids)
                for line in depreciation_line_ids.sorted(key=lambda r:r.asset_id.purchase_date):
                    asset_id = line.asset_id

                    if asset_id.asset_disposal_date and asset_id.asset_disposal_date < self.date_from:
                        continue

                    if asset_id.id not in asset_ids:
                        asset_ids.append(asset_id.id)

                    if asset_id.id in depreciation_lines:
                        # this is another depreciation line in exsting line
                        depreciation_lines[asset_id.id]['amount'] += line.amount
                    else:
                        # last date mean, last post date before search date
                        domain_last_asset = [('move_check', '=', True), ('asset_id', '=', asset_id.id),
                                             ('depreciation_date', '<=', self.date_from)]
                        domain_next_asset = [('move_check', '=', True), ('asset_id', '=', asset_id.id),
                                             ('depreciation_date', '<=', self.date_to)]
                        last_date_record = depreciation_line_obj.search(domain_last_asset, limit=1,
                                                                        order='depreciation_date desc')
                        next_date_record = depreciation_line_obj.search(domain_next_asset, limit=1,
                                                                        order='depreciation_date desc')
                        disposal_date = False
                        # for last record before start date
                        if last_date_record:
                            previous_depreciated_amount = last_date_record.remaining_value + asset_id.salvage_value

                        ########### this is first year
                        elif asset_id.value == asset_id.asset_purchase_price:
                            previous_depreciated_amount = asset_id.value

                        ########## this is other year need to remove salgage value
                        ########## 26/12/2018, no need to deduct salvage_value
                        else:
                            previous_depreciated_amount = asset_id.value

                        # for last record before or the same with end date that depreciated
                        if next_date_record and next_date_record.remaining_value:
                            # print "00000000000000"
                            # print 'Test--------------1'
                            # next_depreciated_amount = next_date_record.remaining_value + asset_id.salvage_value
                            # next_depreciated_amount = float(next_date_record.remaining_value)
                            # next_depreciated_amount = next_date_record.asset_id.asset_purchase_price - next_date_record.asset_id.category_id.salvage_value

                            next_depreciated_amount = next_date_record.remaining_value + asset_id.salvage_value

                            # print next_depreciated_amount
                        elif next_date_record and not next_date_record.remaining_value:
                            # print "00000000000001"
                            # print 'Test--------------2'
                            # next_depreciated_amount = next_date_record.remaining_value + asset_id.salvage_value
                            next_depreciated_amount = asset_id.salvage_value

                            # print next_depreciated_amount
                        else:
                            # print "00000000000003"
                            # print 'Test--------------3'
                            next_depreciated_amount = asset_id.value_residual
                            # print next_depreciated_amount
                        # print "77777777777777"
                        disposal_date = asset_id.asset_disposal_date
                        # print disposal_date
                        # print self.date_to

                        if disposal_date and disposal_date < self.date_to:
                            # print 'Test--------------4'
                            next_depreciated_amount = 0.00
                            # print next_depreciated_amount
                        else:
                            disposal_date = asset_id.asset_disposal_date
                            ############This is change 27/08/2019
                            # disposal_date = next_date_record.asset_id.asset_disposal_date

                        number_of_year = (Decimal(
                            asset_id.category_id.method_number * asset_id.category_id.method_period)) / Decimal(12)
                        if number_of_year:
                            percent = Decimal(100) / number_of_year
                        else:
                            percent = 0

                        # print 'next_depreciated_amount====1'
                        # print  next_depreciated_amount

                        depreciation_lines[asset_id.id] = {
                            'name': asset_id.name,
                            'category_id': asset_id.category_id.id,
                            'code': asset_id.code,
                            'purchase_date': asset_id.purchase_date,
                            'date': asset_id.date,
                            'purchase_value': asset_id.asset_purchase_price,
                            'amount': line.amount,
                            'previous_depreciated_amount': previous_depreciated_amount,
                            'next_depreciated_amount': next_depreciated_amount,
                            'percent': percent,
                            'depreciated_value': line.depreciated_value,
                            'remaining_value': line.remaining_value,
                            'disposal_date': disposal_date,
                            'asset_depreciation_code': asset_id.category_id.account_depreciation_id.code,
                            'expense_depreciation_code': asset_id.category_id.account_depreciation_expense_id.code,
                            'salvage_value': asset_id.salvage_value,
                            'serial_number': asset_id.serial_number or "",
                        }

                depreciation_lines = [value for key, value in depreciation_lines.items()]

                # print ""
                # print depreciation_lines
                # print ('before',depreciation_lines)
                depreciation_lines = sorted(depreciation_lines, key=lambda l: l['purchase_date'])
                # print ('after',depreciation_lines)
                if depreciation_lines:
                    for line in depreciation_lines:
                        # print "LINE----"
                        # print line

                        inv_row += 1
                        i += 1
                        worksheet.write(inv_row, 0, i, for_center)
                        worksheet.write(inv_row, 1, line['code'], for_center)
                        worksheet.write(inv_row, 2, line['name'], for_center)
                        # print line['name']
                        if line['purchase_date']:
                            worksheet.write(inv_row, 3, strToDate(line['purchase_date']).strftime("%d/%m/%Y"),
                                            for_center)
                        else:
                            worksheet.write(inv_row, 3, strToDate(line['date']).strftime("%d/%m/%Y"), for_center)
                        worksheet.write(inv_row, 4, locale.format("%.2f", float(line['purchase_value']), grouping=True),
                                        for_right)
                        worksheet.write(inv_row, 5, locale.format("%.2f", float(line['percent']), grouping=True),
                                        for_center)
                        worksheet.write(inv_row, 6, locale.format("%.2f", float(line['previous_depreciated_amount']),
                                                                  grouping=True), for_right)

                        ###if all depreciation not equal to purchase value then show.
                        # print line['code']
                        if line['previous_depreciated_amount'] != line['purchase_value']:
                            ############ 26/12/2018
                            # print "11-------"
                            net_depreciated_amount = float(line['purchase_value']) - float(
                                line['previous_depreciated_amount'])

                            # if not line['disposal_date'] or (line['disposal_date'] and strToDate(line['disposal_date']) > strToDate(self.date_to)):
                            #     print "11-------"
                            #
                            # else:
                            #     print "222-------"
                            #     ############# This is already sold
                            #     net_depreciated_amount = 0.0
                        else:
                            # print "33333"
                            net_depreciated_amount = 0.0

                        worksheet.write(inv_row, 7, locale.format("%.2f", float(net_depreciated_amount), grouping=True),
                                        for_right)

                        worksheet.write(inv_row, 8, locale.format("%.2f", float(line['amount']), grouping=True),
                                        for_right)

                        worksheet.write(inv_row, 9, locale.format("%.2f", float(line['purchase_value']) - float(
                            line['previous_depreciated_amount']) + float(line['amount']), grouping=True), for_right)

                        worksheet.write(inv_row, 10,
                                        locale.format("%.2f", float(line['next_depreciated_amount']), grouping=True),
                                        for_right)
                        # print '================================4'
                        # print locale.format("%.2f", float(line['next_depreciated_amount']))






                        if line['disposal_date'] and strToDate(line['disposal_date']) < strToDate(self.date_to):
                            # print "-------1111"
                            # worksheet.write(inv_row, 9, locale.format("%.2f", float(line['purchase_value']), grouping=True), for_right)
                            worksheet.write(inv_row, 11, locale.format("%.2f", float(0.00), for_right))
                            worksheet.write(inv_row, 12, strToDate(line['disposal_date']).strftime("%d/%m/%Y"),
                                            for_center)

                        else:
                            # print "-------1222"
                            # worksheet.write(inv_row, 9, locale.format("%.2f", float(line['purchase_value']) - float(
                            #     line['previous_depreciated_amount']) + float(line['amount']), grouping=True), for_right)

                            worksheet.write(inv_row, 11,
                                            locale.format("%.2f", float(line['salvage_value']), grouping=True),
                                            for_right)
                            worksheet.write(inv_row, 12, '', for_center)

                            # worksheet.write(inv_row, 12, strToDate(line['disposal_date']).strftime("%d/%m/%Y"),
                            #                 for_center)

                        worksheet.write(inv_row, 13, line['asset_depreciation_code'], for_right)
                        worksheet.write(inv_row, 14, line['expense_depreciation_code'], for_right)
                        worksheet.write(inv_row, 15, line['serial_number'], for_right)

                        # summary all amount
                        sum_purchase_value += round(line['purchase_value'], 2)
                        sum_previous_depreciated_amount += round(line['previous_depreciated_amount'], 2)
                        sum_start_year_depreciated_amount += round(
                            line['purchase_value'] - line['previous_depreciated_amount'], 2)
                        sum_amount += round(line['amount'], 2)
                        sum_net_depreciated_amount += round(
                            (line['purchase_value'] - line['previous_depreciated_amount'] + line['amount']), 2)
                        sum_savage_amount += round(line['salvage_value'], 2)

                        # float(line['purchase_value']) - float(
                        #     line['previous_depreciated_amount']) + float(line['amount'])

                        sum_next_depreciated_amount += round(line['next_depreciated_amount'], 2)


                        # ------------ending write detail to excel--------------------------

            asset_obj = self.env['account.asset.asset']
            domain = [('state', '=', 'open'), ('category_id', '=', category_id.id), ('date', '<=', self.date_to)]
            if self.department_id:
                domain.append(('department_id', '=', self.department_id.id))

            asset_more_ids = asset_obj.search(domain, order='category_id asc,date asc,purchase_date asc')
            #########no depre but still keep as asset
            print('asset_more_ids:',asset_more_ids)
            asset_more_ids = sorted(asset_more_ids, key=lambda x:x.purchase_date)
            print('asset_more_ids_sort:',asset_more_ids)

            for asset_more in asset_more_ids:
                if asset_more.id not in asset_ids:
                    if asset_more.asset_disposal_date and asset_more.asset_disposal_date < self.date_from:
                        continue
                    print('asset_more:',asset_more)
                    i += 1
                    inv_row += 1

                    worksheet.write(inv_row, 0, i, for_center)
                    worksheet.write(inv_row, 1, asset_more.code, for_center)
                    worksheet.write(inv_row, 2, asset_more.name, for_center)
                    # print asset_more.name
                    if asset_more.purchase_date:
                        worksheet.write(inv_row, 3, strToDate(asset_more.purchase_date).strftime("%d/%m/%Y"),
                                        for_center)
                    else:
                        worksheet.write(inv_row, 3, strToDate(asset_more.date).strftime("%d/%m/%Y"), for_center)

                    worksheet.write(inv_row, 4,
                                    locale.format("%.2f", float(asset_more.asset_purchase_price), grouping=True),
                                    for_right)

                    number_of_year = (Decimal(
                        asset_more.category_id.method_number * asset_more.category_id.method_period)) / Decimal(12)
                    if number_of_year:
                        percent = Decimal(100) / number_of_year
                    else:
                        percent = 0

                    worksheet.write(inv_row, 5, locale.format("%.2f", float(percent), grouping=True),
                                    for_center)

                    worksheet.write(inv_row, 6,
                                    locale.format("%.2f", float(asset_more.salvage_value), grouping=True),
                                    for_right)

                    # if line['previous_depreciated_amount'] != line['purchase_value']:
                    #     net_depreciated_amount = float(line['purchase_value']) - float(
                    #         line['previous_depreciated_amount']) - float(line['salvage_value'])
                    # else:
                    #     net_depreciated_amount = 0.0

                    worksheet.write(inv_row, 7,
                                    locale.format("%.2f", float(asset_more.depreciated_amount), grouping=True),
                                    for_right)

                    worksheet.write(inv_row, 8, locale.format("%.2f", float(0.00), grouping=True),
                                    for_right)

                    if asset_more.asset_disposal_date and asset_more.asset_disposal_date < self.date_to:
                        worksheet.write(inv_row, 9, locale.format("%.2f", float(asset_more.depreciated_amount),
                                                                  grouping=True), for_right)
                        worksheet.write(inv_row, 10,
                                        locale.format("%.2f", 0.00, grouping=True),
                                        for_right)
                        # print '=============================3'
                        worksheet.write(inv_row, 11,
                                        locale.format("%.2f", 0.00, grouping=True),
                                        for_right)
                        worksheet.write(inv_row, 12, strToDate(asset_more.asset_disposal_date).strftime("%d/%m/%Y"),
                                        for_center)

                        sum_net_depreciated_amount += round(asset_more.depreciated_amount, 2)


                    else:
                        # print '================================1'
                        # print locale.format("%.2f", float(asset_more.salvage_value))
                        worksheet.write(inv_row, 9, locale.format("%.2f", float(asset_more.depreciated_amount),
                                                                  grouping=True), for_right)
                        worksheet.write(inv_row, 10,
                                        locale.format("%.2f", float(asset_more.salvage_value), grouping=True),
                                        for_right)
                        worksheet.write(inv_row, 11,
                                        locale.format("%.2f", float(asset_more.salvage_value), grouping=True),
                                        for_right)
                        worksheet.write(inv_row, 12, '', for_center)

                        sum_net_depreciated_amount += round(asset_more.depreciated_amount, 2)
                        sum_savage_amount += round(asset_more.salvage_value, 2)

                        sum_next_depreciated_amount += round(asset_more.salvage_value, 2)

                    worksheet.write(inv_row, 13, asset_more.category_id.account_depreciation_id.code, for_right)
                    worksheet.write(inv_row, 14, asset_more.category_id.account_depreciation_expense_id.code, for_right)
                    worksheet.write(inv_row, 15, asset_more.serial_number or "", for_right)



                    # summary all amount
                    sum_purchase_value += round(asset_more.asset_purchase_price, 2)
                    sum_previous_depreciated_amount += round(asset_more.salvage_value, 2)
                    sum_start_year_depreciated_amount += round(asset_more.depreciated_amount, 2)

            # ------------start write summary to excel--------------------------
            inv_row += 1
            worksheet.write_merge(inv_row, inv_row, 0, 3, 'รวม', for_center_bold)
            worksheet.write(inv_row, 4, locale.format("%.2f", float(sum_purchase_value), grouping=True),
                            for_right_bold)
            worksheet.write(inv_row, 5, '', for_center)
            worksheet.write(inv_row, 6,
                            locale.format("%.2f", float(sum_previous_depreciated_amount), grouping=True),
                            for_right_bold)
            worksheet.write(inv_row, 7,
                            locale.format("%.2f", float(sum_start_year_depreciated_amount), grouping=True),
                            for_right_bold)

            worksheet.write(inv_row, 8, locale.format("%.2f", float(sum_amount), grouping=True), for_right_bold)
            worksheet.write(inv_row, 9, locale.format("%.2f", float(sum_net_depreciated_amount), grouping=True),
                            for_right_bold)
            worksheet.write(inv_row, 10,
                            locale.format("%.2f", float(sum_next_depreciated_amount), grouping=True),
                            for_right_bold)
            worksheet.write(inv_row, 11,
                            locale.format("%.2f", float(sum_savage_amount), grouping=True),
                            for_right_bold)
            # print '===================================2'
            # print sum_next_depreciated_amount
            worksheet.write(inv_row, 12, '', for_center)
            worksheet.write(inv_row, 13, '', for_center)
            worksheet.write(inv_row, 14, '', for_center)
            # ------------ending write summary to excel--------------------------

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['asset.excel.export'].create(
            vals={'name': 'Asset Report.xls', 'report_file': ctx['report_file']})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'asset.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

        # ---------------------------- End ------------------------------

