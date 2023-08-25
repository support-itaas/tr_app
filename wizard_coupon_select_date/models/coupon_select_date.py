# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import xlsxwriter
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class wizard_log(models.Model):
    _name = 'wizard.log'

    start = fields.Char(string='Start')
    ava_time = fields.Char(string='Available')
    redeem_time = fields.Char(string='Redeem')
    expire_time = fields.Char(string='Expire')
    session_time = fields.Char(string='Session')
    gl_time = fields.Char(string='GL')
    total_time = fields.Char(string='Total')




class Wizard_Select_Date(models.TransientModel):
    _name = 'wizard.select.date'

    date_from = fields.Date(string='From Date')
    date = fields.Date(string='Date', required=True)
    company_id = fields.Many2one('res.company',string='Company')
    is_detail = fields.Boolean(string='Show Detail')
    project_id = fields.Many2one('project.project',string='Branch')
    coupon_id = fields.Many2one('product.product',string='Coupon')
    account_id = fields.Many2one('account.account',string='Account')
    is_fix = fields.Boolean(string='Fix by Session')
    is_use_detail = fields.Boolean(string='Show Use Detail')
    is_gl_balance = fields.Boolean(string='GL Balance')

    @api.multi
    def return_order_coupon(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,##0.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")

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

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Coupon')
        worksheet.col(0).width = 4000
        # worksheet.col(1).width = 10000
        worksheet.write_merge(0, 0, 0, 1,
                              'รายงาน Return Order และ คูปองซ้ำ วันที่ ' + strToDate(self.date_from).strftime(
                                  "%d/%m/%Y") + ' - ' + strToDate(self.date).strftime("%d/%m/%Y"), GREEN_TABLE_HEADER)
        params = (self.date_from, self.date,)
        query = """SELECT pos_reference, count(*)
                                                                               FROM pos_order
                                                                               WHERE date_order >= %s and date_order <= %s and state not in ('new','cancel')                                                                               GROUP BY pos_reference
                                                                               HAVING COUNT(*) > 1
                                                                                """
        self.env.cr.execute(query, params)
        res = self.env.cr.fetchall()
        col = 0
        row = 1

        for line in res:
            if line[0]:
                print ('Line',line[0])
                order_ids = self.env['pos.order'].search([('pos_reference','=',line[0])])
                print ('Order_ids',order_ids)
                # .filtered(lambda o: o.coupon_ids)
                if order_ids:
                    # for order in order_ids:
                    for order in order_ids.filtered(lambda o: o.coupon_ids):
                        col = 0
                        row += 1
                        worksheet.write(row, col, order.name, for_left)

        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['coupon.select.excel.export'].create(
            vals={'name': 'Coupon Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coupon.select.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

    @api.multi
    def claim_coupon(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,##0.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")

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

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Coupon')
        worksheet.col(0).width = 4000
        worksheet.col(1).width = 10000
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
        worksheet.col(10).width = 4000

        branch_ids = self.env['project.project'].sudo().search([('company_id','=',self.company_id.sudo().id),('active','=',True)])
        other_branch_ids = self.env['project.project'].sudo().search([('active','=',True),('id','not in',branch_ids.ids)])
        # print ('BRNACH')
        # print (branch_ids)
        # print (other_branch_ids.sudo())
        worksheet.write_merge(0, 0, 0, 20, 'รายงานการเคลมคูปองระหว่างบริษัท วันที่ ' + strToDate(self.date_from).strftime("%d/%m/%Y") + ' - ' + strToDate(self.date).strftime("%d/%m/%Y"), GREEN_TABLE_HEADER)
        row = 1
        header_col = 0
        for other_branch_id in other_branch_ids:
            header_col +=1
            worksheet.write(row, header_col, other_branch_id.sudo().name, for_center_bold)
        worksheet.write(row, header_col+1, 'รวม', for_center_bold)
        sum_amount_all = 0
        for branch in branch_ids:
            col = 0
            row +=1
            # print ('BRANCH',branch.name)
            worksheet.write(row, col, branch.sudo().name, for_center_bold)
            # print (branch.name)
            data_temp = []
            sum_amount = 0
            for other_branch_id in other_branch_ids:
                col +=1
                params = (self.date_from,self.date,branch.id,other_branch_id.id,)
                query = """SELECT distinct(aml.branch_id),sum(aml.destination_branch_amount)
                                       FROM wizard_coupon AS aml
                                       WHERE aml.state = 'redeem' and aml.redeem_date >= %s and aml.redeem_date <= %s and aml.order_branch_id= %s and aml.branch_id= %s and aml.active = True
                                        GROUP BY aml.branch_id
                                        """
                self.env.cr.execute(query, params)
                res = self.env.cr.fetchall()
                if res:


                    try:
                        sum_amount += round(res[0][1],2)
                        worksheet.write(row, col, round(res[0][1],2), for_right)

                    except:
                        sum_amount += 0.00
                        worksheet.write(row, col, 0.00, for_right)

                else:
                    # print ('ELSE')
                    worksheet.write(row, col, 0.00, for_right)

            sum_amount_all += sum_amount
            worksheet.write(row, col+1, sum_amount, for_right)

        worksheet.write(row+1, len(other_branch_ids.sudo()) + 1, sum_amount_all, for_right)

        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['coupon.select.excel.export'].create(
            vals={'name': 'Coupon Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coupon.select.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


    def gl_balance(self,date,account_id):

        params = (account_id.id, self.date,)
        aml_query = """SELECT sum(aml.credit) as sum_credit,sum(aml.debit) as sum_debit
                                                                                       FROM account_move_line AS aml
                                                                                       JOIN account_move m ON aml.move_id = m.id
                                                                                       WHERE aml.account_id = %s and m.state = 'posted' and aml.date <= %s
                                                                                        GROUP BY aml.account_id
                                                                                        """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES',res)
        if res:
            end_balance = res[0][0] - res[0][1]
        else:
            end_balance = 0.00

        # to_date = strToDate(date) + relativedelta(days=1)
        # to_date = str(to_date)
        # params = (account_id.id, to_date,)
        # aml_query = """SELECT aml.id
        #                                                                                FROM account_move_line AS aml
        #                                                                                JOIN account_move m ON aml.move_id = m.id
        #                                                                                WHERE aml.account_id = %s and m.state = 'posted' and aml.date < %s
        #                                                                                 GROUP BY aml.account_id, aml.id
        #                                                                                 """
        #
        # self.env.cr.execute(aml_query, params)
        # res = self.env.cr.fetchall()
        # sum_debit = sum_credit = 0
        #
        # for line in res:
        #     aml = self.env['account.move.line'].browse(line[0])
        #     sum_debit += aml.debit
        #     sum_credit += aml.credit
        # end_balance = sum_credit - sum_debit
        return end_balance

    #coupon balance
    @api.multi
    def print_report(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,##0.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")

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





        if self.is_detail:
            data_temp = []

            #case#1-available

            #case#2-reedeem

            #case#3-expired

            product_ids = []

            if self.coupon_id:
                product_ids.append(self.coupon_id.id)
            elif self.account_id:
                coupon_product_ids = self.env['product.product'].search([('property_account_income_id','=',self.account_id.id),('is_coupon','=',True)])
                for coupon_product_id in coupon_product_ids:
                    product_ids.append(coupon_product_id.id)
            else:
                raise UserError(_('เลือกคูปอง หรือ เลือกรหัสบัญชี และ วันที่ ก่อนเรียกรายงาน'))

        #     # ----------------HEADDER-------------------------------------
            if product_ids:
                ########### DRAFT OVER DATE ##############
                # case1-draft
                # print ('Product',product)
                product_all_ids = self.env['product.product'].browse(product_ids)

                params_1 = (self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                      FROM wizard_coupon AS aml
                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                      WHERE aml.state = 'draft' and aml.purchase_date <= %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                      GROUP BY aml.product_id, aml.id
                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_all_ids = []
                for line in res:
                    coupon_all_ids.append(line[0])

                # case2-redeem
                params_1 = (self.date, self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                                      FROM wizard_coupon AS aml
                                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                                      WHERE aml.state = 'redeem' and aml.purchase_date <= %s and aml.redeem_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                                      GROUP BY aml.product_id, aml.id
                                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                for line in res:
                    coupon_all_ids.append(line[0])

                # case3-expire
                ########### Expire OVER DATE ##############
                params_1 = (
                    self.date, self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                                                      FROM wizard_coupon AS aml
                                                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                                                      WHERE aml.state = 'expire' and aml.purchase_date <= %s and aml.expiry_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                                                      GROUP BY aml.product_id, aml.id
                                                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                for line in res:
                    coupon_all_ids.append(line[0])

            data_all_temp = self.env['wizard.coupon'].sudo().browse(coupon_all_ids)
            page_no = 0
            sum_all_amount = sum(coupon_id.amount for coupon_id in data_all_temp)


            for product in product_ids:
                product_id = self.env['product.product'].browse(product)
        #
                worksheet = workbook.add_sheet(str(product_id.default_code) + '-' + str(product_id.id))


                worksheet.col(0).width = 4000
                worksheet.col(1).width = 10000
                worksheet.col(2).width = 3000
                worksheet.col(3).width = 4500
                worksheet.col(4).width = 6000
                worksheet.col(5).width = 6000
                worksheet.col(6).width = 4000
                worksheet.col(7).width = 4000
                worksheet.col(8).width = 4000
                worksheet.col(9).width = 4000
                worksheet.col(10).width = 4000

                ########### DRAFT OVER DATE ##############
                # case1-draft
                # print ('Product',product)
                params_1 = (self.date, tuple(product_id.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                      FROM wizard_coupon AS aml
                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                      JOIN res_company c ON p.company_id = c.id
                                                                      WHERE aml.state = 'draft' and aml.purchase_date <= %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                      GROUP BY aml.product_id, aml.id
                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_ids = []
                for line in res:
                    coupon_ids.append(line[0])


                #case2-redeem
                params_1 = (self.date, self.date, tuple(product_id.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                      FROM wizard_coupon AS aml
                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                      WHERE aml.state = 'redeem' and aml.purchase_date <= %s and aml.redeem_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                      GROUP BY aml.product_id, aml.id
                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                for line in res:
                    coupon_ids.append(line[0])

                # case3-expire
                ########### Expire OVER DATE ##############
                params_1 = (
                    self.date, self.date, tuple(product_id.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                                      FROM wizard_coupon AS aml
                                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                                      WHERE aml.state = 'expire' and aml.purchase_date <= %s and aml.expiry_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                                      GROUP BY aml.product_id, aml.id
                                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                for line in res:
                    coupon_ids.append(line[0])

                date = strToDate(self.date).strftime("%d/%m/%Y")
                inv_row = 1
                worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่' + ' ' + date, GREEN_TABLE_HEADER)
                worksheet.write(inv_row, 0, 'คูปอง', for_center_bold)
                worksheet.write(inv_row, 1, 'ลูกค้า', for_center_bold)
                worksheet.write(inv_row, 2, 'สาขาที่ซื้อ', for_center_bold)
                worksheet.write(inv_row, 3, 'สาขาที่ใช้', for_center_bold)
                worksheet.write(inv_row, 4, 'วันที่ซื้อ', for_center_bold)
                worksheet.write(inv_row, 5, 'วันที่หมดอายุ', for_center_bold)
                worksheet.write(inv_row, 6, 'วันที่ใช้', for_center_bold)
                worksheet.write(inv_row, 7, 'มูลค่า', for_center_bold)
                worksheet.write(inv_row, 8, 'POS Order', for_center_bold)
                worksheet.write(inv_row, 9, 'POS Session', for_center_bold)
                worksheet.write(inv_row, 10, 'Package', for_center_bold)
                worksheet.write(inv_row, 11, 'สถานะ', for_center_bold)

                # print (len(data_temp))
                # print ('data_temp',data_temp)
                # index = 0
                total = 0
                data_temp = self.env['wizard.coupon'].sudo().browse(coupon_ids)
                page_no = 0
                sum_amount = sum(coupon_id.amount for coupon_id in data_temp)

                gl_end_balance = self.gl_balance(self.date, product_id.property_account_income_id)
                product_end_balance = (sum_amount / sum_all_amount) * gl_end_balance

                if self.date == '2021-12-31':
                    if product_id.default_code == 'CWW6208000060':
                        product_end_balance = 1023840.63
                    elif product_id.default_code == 'CWZ6202000550':
                        product_end_balance = 37878.67
                    elif product_id.default_code == 'CWZ6202000540':
                        product_end_balance = 9601.61
                    elif product_id.default_code == 'CWZ6202000530':
                        product_end_balance = 7489003.21
                    elif product_id.default_code == 'CWZ6202000510':
                        product_end_balance = 2499420.20
                    elif product_id.default_code == 'CWW6310000220':
                        product_end_balance = 2122.62
                    elif product_id.default_code == 'CWW64010000180':
                        product_end_balance = 449714.89
                    elif product_id.default_code == 'CWZ6406000050':
                        product_end_balance = 1149.96
                    elif product_id.default_code == 'CWZ6404000230':
                        product_end_balance = 69124.61
                    elif product_id.default_code == 'CWZ6202000720':
                        product_end_balance = 491601.49
                    elif product_id.default_code == 'CWZ6202000730':
                        product_end_balance = 227481.56


                for coupon_id in data_temp:
                    inv_row += 1
                    worksheet.write(inv_row, 0, coupon_id.name, for_center)
                    worksheet.write(inv_row, 1, coupon_id.partner_id.name, for_left)
                    worksheet.write(inv_row, 2, coupon_id.order_branch_id and coupon_id.order_branch_id.name or "", for_left)
                    worksheet.write(inv_row, 3, coupon_id.branch_id and coupon_id.branch_id.name or "",for_left)
                    worksheet.write(inv_row, 4, coupon_id.purchase_date,for_left)
                    worksheet.write(inv_row, 5, coupon_id.expiry_date,for_left)
                    worksheet.write(inv_row, 6, coupon_id.redeem_date or "",for_left)
                    if self.is_gl_balance and sum_amount:
                        worksheet.write(inv_row, 7, coupon_id.amount * (product_end_balance/sum_amount), for_right)
                    else:
                        worksheet.write(inv_row, 7, coupon_id.amount, for_right)
                    worksheet.write(inv_row, 8, coupon_id.order_id and coupon_id.order_id.name or "",for_left)
                    worksheet.write(inv_row, 9, coupon_id.order_id and coupon_id.order_id.session_id.name or "",for_left)
                    worksheet.write(inv_row, 10, coupon_id.package_id and coupon_id.package_id.name or "", for_left)
                    worksheet.write(inv_row, 11, coupon_id.state or "", for_left)
                    total += coupon_id.amount
                    if inv_row > 65530:
                        page_no +=1
                        worksheet = workbook.add_sheet(str(product_id.default_code) + '-' + str(product_id.id) + '-P'+ str(page_no))


                inv_row+=1
                worksheet.write(inv_row, 0, 'Total', for_right)
                if self.is_gl_balance:
                    worksheet.write(inv_row, 7, product_end_balance, for_right)

                else:
                    worksheet.write(inv_row, 7, total, for_right)

        elif self.is_use_detail:
            product_ids = []

            if self.coupon_id:
                product_ids.append(self.coupon_id.id)
            elif self.account_id:
                coupon_product_ids = self.env['product.product'].search(
                    [('property_account_income_id', '=', self.account_id.id), ('is_coupon', '=', True)])
                for coupon_product_id in coupon_product_ids:
                    product_ids.append(coupon_product_id.id)
            else:
                raise UserError(_('เลือกคูปอง หรือ เลือกรหัสบัญชี และ วันที่ ก่อนเรียกรายงาน'))

            #     # ----------------HEADDER-------------------------------------
            # if product_ids:
            #     ########### DRAFT OVER DATE ##############
            #     # case1-expire and redeem under date period
            #     # print ('Product',product)
            #     product_all_ids = self.env['product.product'].browse(product_ids)
            #
            #     params_1 = (self.date_from,self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
            #     query = """SELECT aml.id
            #                                                                                       FROM wizard_coupon AS aml
            #                                                                                       JOIN pos_order p ON aml.order_id = p.id
            #                                                                                       JOIN res_company c ON p.company_id = c.id
            #                                                                                       WHERE aml.state IN ['expire','redeem'] and aml.redeem_date >= %s and aml.redeem_date <= %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
            #                                                                                       GROUP BY aml.product_id, aml.id
            #                                                                                        """
            #     self.env.cr.execute(query, params_1)
            #     res = self.env.cr.fetchall()
            #     coupon_all_ids = []
            #     for line in res:
            #         coupon_all_ids.append(line[0])

                # # case2-redeem
                # params_1 = (self.date, self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
                # query = """SELECT aml.id
                #                                                                                                   FROM wizard_coupon AS aml
                #                                                                                                   JOIN pos_order p ON aml.order_id = p.id
                #                                                                                                   JOIN res_company c ON p.company_id = c.id
                #                                                                                                   WHERE aml.state = 'redeem' and aml.purchase_date <= %s and aml.redeem_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                #                                                                                                   GROUP BY aml.product_id, aml.id
                #                                                                                                    """
                # self.env.cr.execute(query, params_1)
                # res = self.env.cr.fetchall()
                # for line in res:
                #     coupon_all_ids.append(line[0])
                #
                # # case3-expire
                # ########### Expire OVER DATE ##############
                # params_1 = (
                #     self.date, self.date, tuple(product_all_ids.ids), self.env.user.company_id.id,)
                # query = """SELECT aml.id
                #                                                                                                                   FROM wizard_coupon AS aml
                #                                                                                                                   JOIN pos_order p ON aml.order_id = p.id
                #                                                                                                                   JOIN res_company c ON p.company_id = c.id
                #                                                                                                                   WHERE aml.state = 'expire' and aml.purchase_date <= %s and aml.expiry_date > %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                #                                                                                                                   GROUP BY aml.product_id, aml.id
                #                                                                                                                    """
                # self.env.cr.execute(query, params_1)
                # res = self.env.cr.fetchall()
                # for line in res:
                #     coupon_all_ids.append(line[0])

            # data_all_temp = self.env['wizard.coupon'].sudo().browse(coupon_all_ids)
            # page_no = 0
            # sum_all_amount = sum(coupon_id.amount for coupon_id in data_all_temp)

            for product in product_ids:
                product_id = self.env['product.product'].browse(product)
                #
                worksheet = workbook.add_sheet(str(product_id.default_code) + '-' + str(product_id.id))

                worksheet.col(0).width = 4000
                worksheet.col(1).width = 10000
                worksheet.col(2).width = 3000
                worksheet.col(3).width = 4500
                worksheet.col(4).width = 6000
                worksheet.col(5).width = 6000
                worksheet.col(6).width = 4000
                worksheet.col(7).width = 4000
                worksheet.col(8).width = 4000
                worksheet.col(9).width = 4000
                worksheet.col(10).width = 4000

                ########## DRAFT OVER DATE ##############
                # case1 expire and redeem
                print ('Product',product)
                params_1 = (self.date_from,self.date, tuple(product_id.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                  FROM wizard_coupon AS aml
                                                                                  JOIN pos_order p ON aml.order_id = p.id
                                                                                  JOIN res_company c ON p.company_id = c.id
                                                                                  WHERE aml.state IN ('expire','redeem') and aml.redeem_date >= %s and aml.redeem_date <= %s and aml.product_id in %s and aml.active = True and aml.move_id is not Null and aml.order_id is not Null and c.id = %s
                                                                                  GROUP BY aml.product_id, aml.id
                                                                                   """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_ids = []
                for line in res:
                    coupon_ids.append(line[0])


                date = strToDate(self.date).strftime("%d/%m/%Y")
                inv_row = 1
                worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่' + ' ' + date, GREEN_TABLE_HEADER)
                worksheet.write(inv_row, 0, 'คูปอง', for_center_bold)
                worksheet.write(inv_row, 1, 'ลูกค้า', for_center_bold)
                worksheet.write(inv_row, 2, 'สาขาที่ซื้อ', for_center_bold)
                worksheet.write(inv_row, 3, 'สาขาที่ใช้', for_center_bold)
                worksheet.write(inv_row, 4, 'วันที่ซื้อ', for_center_bold)
                worksheet.write(inv_row, 5, 'วันที่หมดอายุ', for_center_bold)
                worksheet.write(inv_row, 6, 'วันที่ใช้', for_center_bold)
                worksheet.write(inv_row, 7, 'มูลค่า', for_center_bold)
                worksheet.write(inv_row, 8, 'POS Order', for_center_bold)
                worksheet.write(inv_row, 9, 'POS Session', for_center_bold)
                worksheet.write(inv_row, 10, 'Package', for_center_bold)
                worksheet.write(inv_row, 11, 'สถานะ', for_center_bold)

                # print (len(data_temp))
                # print ('data_temp',data_temp)
                # index = 0
                total = 0
                data_temp = self.env['wizard.coupon'].sudo().browse(coupon_ids)
                page_no = 0
                sum_amount = sum(coupon_id.amount for coupon_id in data_temp)

                # gl_end_balance = self.gl_balance(self.date, product_id.property_account_income_id)
                # product_end_balance = (sum_amount / sum_all_amount) * gl_end_balance

                # if self.date == '2021-12-31':
                #     if product_id.default_code == 'CWW6208000060':
                #         product_end_balance = 1023840.63
                #     elif product_id.default_code == 'CWZ6202000550':
                #         product_end_balance = 37878.67
                #     elif product_id.default_code == 'CWZ6202000540':
                #         product_end_balance = 9601.61
                #     elif product_id.default_code == 'CWZ6202000530':
                #         product_end_balance = 7489003.21
                #     elif product_id.default_code == 'CWZ6202000510':
                #         product_end_balance = 2499420.20
                #     elif product_id.default_code == 'CWW6310000220':
                #         product_end_balance = 2122.62
                #     elif product_id.default_code == 'CWW64010000180':
                #         product_end_balance = 449714.89
                #     elif product_id.default_code == 'CWZ6406000050':
                #         product_end_balance = 1149.96
                #     elif product_id.default_code == 'CWZ6404000230':
                #         product_end_balance = 69124.61
                #     elif product_id.default_code == 'CWZ6202000720':
                #         product_end_balance = 491601.49
                #     elif product_id.default_code == 'CWZ6202000730':
                #         product_end_balance = 227481.56

                gl_balance = 0.00
                for coupon_id in data_temp:
                    inv_row += 1
                    worksheet.write(inv_row, 0, coupon_id.name, for_center)
                    worksheet.write(inv_row, 1, coupon_id.partner_id.name, for_left)
                    worksheet.write(inv_row, 2, coupon_id.order_branch_id and coupon_id.order_branch_id.name or "",
                                    for_left)
                    worksheet.write(inv_row, 3, coupon_id.branch_id and coupon_id.branch_id.name or "", for_left)
                    worksheet.write(inv_row, 4, coupon_id.purchase_date, for_left)
                    worksheet.write(inv_row, 5, coupon_id.expiry_date, for_left)
                    worksheet.write(inv_row, 6, coupon_id.redeem_date or "", for_left)

                    if self.is_gl_balance and coupon_id.move_id:
                        gl_balance += coupon_id.move_id.amount
                        worksheet.write(inv_row, 7, coupon_id.move_id.amount, for_right)
                    else:
                        gl_balance += coupon_id.move_id.amount
                        worksheet.write(inv_row, 7, coupon_id.amount, for_right)

                    worksheet.write(inv_row, 8, coupon_id.order_id and coupon_id.order_id.name or "", for_left)
                    worksheet.write(inv_row, 9, coupon_id.order_id and coupon_id.order_id.session_id.name or "",
                                    for_left)
                    worksheet.write(inv_row, 10, coupon_id.package_id and coupon_id.package_id.name or "", for_left)
                    worksheet.write(inv_row, 11, coupon_id.state or "", for_left)
                    total += coupon_id.amount
                    if inv_row > 65530:
                        page_no += 1
                        worksheet = workbook.add_sheet(
                            str(product_id.default_code) + '-' + str(product_id.id) + '-P' + str(page_no))

                inv_row += 1
                worksheet.write(inv_row, 0, 'Total', for_right)
                if self.is_gl_balance:
                    worksheet.write(inv_row, 7, gl_balance, for_right)

                else:
                    worksheet.write(inv_row, 7, total, for_right)

        else:
            # ----------------HEADDER-------------------------------------
            worksheet = workbook.add_sheet('Coupon')
            worksheet.col(0).width = 4000
            worksheet.col(1).width = 10000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 4500
            worksheet.col(4).width = 6000
            worksheet.col(5).width = 6000
            worksheet.col(6).width = 4000
            worksheet.col(7).width = 4000
            worksheet.col(8).width = 4000
            worksheet.col(9).width = 4000
            worksheet.col(10).width = 4000
            # Search DATA
            # STATE >>>>>>  Available
            data_temp = []
            if self.project_id:
                params = (self.date, self.project_id.id, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                                   FROM wizard_coupon AS aml
                                                   JOIN project_project r ON aml.order_branch_id = r.id
                                                   JOIN operating_unit g ON r.operating_branch_id = g.id
                                                   JOIN pos_order p ON aml.order_id = p.id
                                                   JOIN res_company c ON p.company_id = c.id
                                                   WHERE aml.state = 'draft' and aml.purchase_date <= %s and r.id = %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                    GROUP BY aml.product_id
                                                    """
            else:
                params = (self.date, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                   FROM wizard_coupon AS aml
                                   JOIN pos_order p ON aml.order_id = p.id
                                   JOIN res_company c ON p.company_id = c.id
                                   WHERE aml.state = 'draft' and aml.purchase_date <= %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                    GROUP BY aml.product_id
                                    """
            self.env.cr.execute(query, params)
            res = self.env.cr.fetchall()
            data_temp.append(res)
            print('data_temp_1:', res)

            # # # STATE >>>>>>  REDEEMED
            if self.project_id:
                params_1 = (self.date, self.date, self.project_id.id, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                                          FROM wizard_coupon AS aml
                                                          JOIN project_project r ON aml.order_branch_id = r.id
                                                          JOIN operating_unit g ON r.operating_branch_id = g.id
                                                          JOIN pos_order p ON aml.order_id = p.id
                                                          JOIN res_company c ON p.company_id = c.id
                                                          WHERE aml.state = 'redeem' and aml.purchase_date <= %s and aml.redeem_date > %s and r.id = %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                          GROUP BY aml.product_id
                                                           """
            else:
                params_1 = (self.date, self.date, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                          FROM wizard_coupon AS aml
                                          JOIN pos_order p ON aml.order_id = p.id
                                          JOIN res_company c ON p.company_id = c.id
                                          WHERE aml.state = 'redeem' and aml.purchase_date <= %s and aml.redeem_date > %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                          GROUP BY aml.product_id
                                           """
            self.env.cr.execute(query, params_1)
            res = self.env.cr.fetchall()
            data_temp.append(res)
            print('data_temp_2:', res)

            # # STATE >>>>>>  Expried
            if self.project_id:
                params_2 = (self.date, self.date, self.project_id.id, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                                        FROM wizard_coupon AS aml
                                                        JOIN project_project r ON aml.order_branch_id = r.id
                                                        JOIN operating_unit g ON r.operating_branch_id = g.id
                                                        JOIN pos_order p ON aml.order_id = p.id
                                                        JOIN res_company c ON p.company_id = c.id
                                                        WHERE aml.state = 'expire' and aml.purchase_date <= %s and aml.expiry_date > %s and r.id = %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                        GROUP BY aml.product_id 
                                                         """
            else:
                params_2 = (self.date, self.date, self.env.user.company_id.id,)
                query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                        FROM wizard_coupon AS aml
                                        JOIN pos_order p ON aml.order_id = p.id
                                        JOIN res_company c ON p.company_id = c.id
                                        WHERE aml.state = 'expire' and aml.purchase_date <= %s and aml.expiry_date > %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                        GROUP BY aml.product_id 
                                         """
            self.env.cr.execute(query, params_2)
            res = self.env.cr.fetchall()
            data_temp.append(res)
            print('data_temp_3:', res)

            check_product = []
            data_total_temp = []
            account_product_ids = {}
            print('STEP-1')
            for data in data_temp:
                print('STEP-2')
                for data_line in data:
                    print('STEP-3')
                    if data_line[0] not in check_product:
                        print('STEP-4')
                        check_product.append(data_line[0])
                        vals = {
                            'product_id': data_line[0],
                            'qty': data_line[1],
                            'sum_total': data_line[2],
                        }
                        data_total_temp.append(vals)

                    else:
                        print('STEP-5')
                        for data_product in data_total_temp:
                            if data_product['product_id'] == data_line[0]:
                                data_product['qty'] += data_line[1]
                                if data_line[2]:
                                    data_product['sum_total'] += data_line[2]

                    # ----------------------------------------#

                    product_id = self.env['product.product'].browse(data_line[0])

                    if data_line[2] is not None:
                        value = data_line[2]
                    else:
                        value = 0

                    if product_id.property_account_income_id.id not in account_product_ids:
                        print('NEW')
                        account_product_ids[product_id.property_account_income_id.id] = {
                            'value': value
                        }
                    else:
                        print('DUP')
                        account_product_ids[product_id.property_account_income_id.id]['value'] += value

            print('STEP-6')
            date = strToDate(self.date).strftime("%d/%m/%Y")
            inv_row = 1
            worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่' + ' ' + date, GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'รหัสคูปอง', for_center_bold)
            worksheet.write(inv_row, 1, 'งานบริการ', for_center_bold)
            worksheet.write(inv_row, 2, 'จำนวน', for_center_bold)
            worksheet.write(inv_row, 3, 'ราคาเฉลี่ย', for_center_bold)
            worksheet.write(inv_row, 4, 'มูลค่า', for_center_bold)
            worksheet.write(inv_row, 5, 'Account CODE', for_center_bold)
            worksheet.write(inv_row, 6, 'Account Name', for_center_bold)
            worksheet.write(inv_row, 7, 'GL Balance', for_center_bold)
            print('STEP-7')
            for data in data_total_temp:
                print('STEP-8')
                inv_row += 1
                print('STEP-8-1')
                product_id = self.env['product.product'].browse(data['product_id'])
                worksheet.write(inv_row, 0, product_id.default_code, for_center)
                worksheet.write(inv_row, 1, product_id.name, for_left)
                worksheet.write(inv_row, 2, data['qty'], for_center)
                new_value = 0.00

                # ------------------ recompute new copon value-----------------------------#
                if product_id.property_account_income_id:
                    end_balance = self.gl_balance(self.date, product_id.property_account_income_id)
                else:
                    end_balance = 0.00

                if account_product_ids[product_id.property_account_income_id.id]['value'] and data['sum_total']:
                    new_value = (float(data['sum_total']) /
                                 account_product_ids[product_id.property_account_income_id.id]['value']) * end_balance

                if self.is_gl_balance:
                    worksheet.write(inv_row, 4, new_value, for_right)
                else:
                    worksheet.write(inv_row, 4, data['sum_total'], for_right)
                # ------------------ recompute new copon value-----------------------------#
                if self.is_gl_balance:
                    if new_value and data['qty']:
                        worksheet.write(inv_row, 3, new_value / float(data['qty']), for_right)
                    else:
                        worksheet.write(inv_row, 3, 0.00, for_right)
                else:
                    if data['sum_total'] and data['qty']:
                        worksheet.write(inv_row, 3, float(data['sum_total']) / float(data['qty']), for_right)
                    else:
                        worksheet.write(inv_row, 3, 0.00, for_right)

                worksheet.write(inv_row, 5, product_id.property_account_income_id.code, for_right)
                worksheet.write(inv_row, 6, product_id.property_account_income_id.name, for_right)

                if product_id.property_account_income_id:
                    end_balance = self.gl_balance(self.date, product_id.property_account_income_id)
                else:
                    end_balance = 0.00
                worksheet.write(inv_row, 7, end_balance, for_right)
                print('STEP-9')

        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['coupon.select.excel.export'].create(
            vals={'name': 'Coupon Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coupon.select.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

    # ('COUPON and GL')
    @api.multi
    def coupon_and_gl_movement(self):
        log_val = {}
        print ('COUPON and GL')
        fl = BytesIO()
        # output = io.BytesIO()
        workbook = xlsxwriter.Workbook(fl, {'in_memory': True})
        # workbook = xlwt.Workbook(encoding='utf-8')
        # workbook = xlsxwriter.Workbook('Coupon Report.xlsx')
        # Workbook(FileFormatType.CSV, CheckExcelRestriction='false')
        # font = xlwt.Font()
        # font.bold = True
        # font.bold = True
        # for_right = xlwt.easyxf(
        #     "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        # for_right.num_format_str = '#,##0.00'
        # for_center = xlwt.easyxf(
        #     "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        # for_left = xlwt.easyxf(
        #     "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        # for_center = xlwt.easyxf(
        #     "font: name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        #
        # for_center_bold = xlwt.easyxf(
        #     "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        # for_left_bold_no_border = xlwt.easyxf(
        #     "font: name  Times New Roman, color black, height 200;  align: horiz left,vertical center;")
        #
        # GREEN_TABLE_HEADER = xlwt.easyxf(
        #     'font: bold 1, name  Times New Roman, height 300,color black;'
        #     'align: vertical center, horizontal center, wrap on;'
        #     'borders: top thin, bottom thin, left thin, right thin;'
        #     'pattern:  pattern_fore_colour white, pattern_back_colour white'
        # )
        #
        # alignment = xlwt.Alignment()  # Create Alignment
        # alignment.horz = xlwt.Alignment.HORZ_RIGHT
        # style = xlwt.easyxf('align: wrap yes')
        # style.num_format_str = '#,###.00'

        GREEN_TABLE_HEADER = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'bg_color': '#FFF58C',
            'border': False
        })


        for_center_bold = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#FFFFFF',
            'border': True
        })

        for_center = workbook.add_format({
            'bold': False,
            'align': 'center',
            'bg_color': '#FFFFFF',
            'border': True
        })

        for_right = workbook.add_format({
            'bold': False,
            'align': 'right',
            'bg_color': '#FFFFFF',
            'border': True,
            'num_format': '#,##0.00'
        })

        format_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'bg_color': '#FFFFFF',
            'border': True
        })
        line_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFFF',
            'border': False
        })
        format_line = workbook.add_format({
            'bold': False,
            'bg_color': '#FFFFCC',
            'border': True
        })

        if self.date:
            # ----------------HEADDER-------------------------------------
            worksheet = workbook.add_worksheet('Coupon and GL Movement')
            # worksheet.set_column(0).width = 4000
            # worksheet.set_column(1).width = 10000
            # worksheet.set_column(2).width = 3000
            # worksheet.set_column(3).width = 4500
            # worksheet.set_column(4).width = 6000
            # worksheet.set_column(5).width = 6000
            # worksheet.set_column(6).width = 4000
            # worksheet.set_column(7).width = 4000
            # worksheet.set_column(8).width = 4000
            # worksheet.set_column(9).width = 4000
            # worksheet.set_column(10).width = 4000

            inv_row = 1
            # date_from = strToDate(self.date_from).strftime("%d/%m/%Y")
            at_date = strToDate(self.date).strftime("%d/%m/%Y")

            worksheet.merge_range(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่ ' + at_date,
                                  GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'วันที่', for_center_bold)
            worksheet.write(inv_row, 1, 'Session', for_center_bold)
            worksheet.write(inv_row, 2, 'Branch', for_center_bold)
            worksheet.write(inv_row, 3, 'Account Name', for_center_bold)
            worksheet.write(inv_row, 4, 'GL Total', for_center_bold)
            worksheet.write(inv_row, 5, 'Coupon Total', for_center_bold)
            worksheet.write(inv_row, 6, 'Use Coupon Value', for_center_bold)
            worksheet.write(inv_row, 7, 'Use Coupon GL', for_center_bold)
            worksheet.write(inv_row, 8, 'Coupon Balance', for_center_bold)
            worksheet.write(inv_row, 9, 'Coupon Detail', for_center_bold)
            worksheet.write(inv_row, 10, 'Reference', for_center_bold)
            worksheet.write(inv_row, 11, 'Available', for_center_bold)
            worksheet.write(inv_row, 12, 'Expire After', for_center_bold)
            worksheet.write(inv_row, 13, 'Redeem After', for_center_bold)
            # worksheet.write(inv_row, 9, 'Status', for_center_bold)
            #get all order with coupon
            aml_ids = []
            missing_gl = ""
            missing_gl_amount = 0.00
            balance_between_month = []



            log_val['start'] = str(datetime.now())
            start_time = datetime.now()
            if self.account_id:
                coupon_product_ids = self.env['product.product'].search([('property_account_income_id','=',self.account_id.id),('is_coupon','=',True)])
                # print ('COUPON PRODUCT',coupon_product_ids)
                # print (xxxx)
                # available_beginning_coupon_ids = self.env['wizard.coupon'].search([('state','=','draft'),('purchase_date','<',self.date_from),('product_id.property_account_income_id','=',self.account_id.id),('order_id.company_id','=',self.env.user.company_id.id)])

                ########### DRAFT OVER DATE ##############
                params_1 = (self.date_from, tuple(coupon_product_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                      FROM wizard_coupon AS aml
                                                      JOIN pos_order p ON aml.order_id = p.id
                                                      JOIN res_company c ON p.company_id = c.id
                                                      WHERE aml.state = 'draft' and aml.purchase_date < %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                      GROUP BY aml.product_id, aml.id
                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_ids = []
                for line in res:
                    coupon_ids.append(line[0])

                available_beginning_coupon_ids = self.env['wizard.coupon'].browse(coupon_ids)
                log_val['ava_time'] = str(datetime.now())
                ########### DRAFT OVER DATE ##############


                # redeem_over_date_beginning = self.env['wizard.coupon'].search([('state','=','redeem'),('purchase_date','<',self.date_from),('redeem_date','>=',self.date_from),('product_id.property_account_income_id','=',self.account_id.id),('order_id.company_id','=',self.env.user.company_id.id)])
                ########### REDEEM OVER DATE ##############
                params_1 = (self.date_from, self.date_from, tuple(coupon_product_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                      FROM wizard_coupon AS aml
                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                      JOIN res_company c ON p.company_id = c.id
                                                                      WHERE aml.state = 'redeem' and aml.purchase_date < %s and aml.redeem_date >= %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                      GROUP BY aml.product_id, aml.id
                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_ids = []
                for line in res:
                    coupon_ids.append(line[0])
                redeem_over_date_beginning = self.env['wizard.coupon'].browse(coupon_ids)
                log_val['redeem_time'] = str(datetime.now())
                ########### REDEEM OVER DATE ##############

                # expire_over_date_beginning = self.env['wizard.coupon'].search(
                #     [('state', '=', 'expire'), ('purchase_date', '<', self.date_from), ('expiry_date', '>=', self.date_from),('product_id.property_account_income_id','=',self.account_id.id),('order_id.company_id','=',self.env.user.company_id.id)])

                ########### Expire OVER DATE ##############
                params_1 = (self.date_from, self.date_from, tuple(coupon_product_ids.ids), self.env.user.company_id.id,)
                query = """SELECT aml.id
                                                                                      FROM wizard_coupon AS aml
                                                                                      JOIN pos_order p ON aml.order_id = p.id
                                                                                      JOIN res_company c ON p.company_id = c.id
                                                                                      WHERE aml.state = 'expire' and aml.purchase_date < %s and aml.expiry_date >= %s and aml.product_id in %s and aml.active = True and aml.order_id is not Null and c.id = %s
                                                                                      GROUP BY aml.product_id, aml.id
                                                                                       """
                self.env.cr.execute(query, params_1)
                res = self.env.cr.fetchall()
                coupon_ids = []
                for line in res:
                    coupon_ids.append(line[0])
                expire_over_date_beginning = self.env['wizard.coupon'].browse(coupon_ids)
                log_val['expire_time'] = str(datetime.now())
                ########### Expire OVER DATE ##############

            else:
                available_beginning_coupon_ids = self.env['wizard.coupon'].search(
                    [('state', '=', 'draft'), ('purchase_date', '<', self.date_from),
                     ('order_id.company_id', '=', self.env.user.company_id.id)])
                redeem_over_date_beginning = self.env['wizard.coupon'].search(
                    [('state', '=', 'redeem'), ('purchase_date', '<', self.date_from),
                     ('redeem_date', '>', self.date_from),
                     ('order_id.company_id', '=', self.env.user.company_id.id)])
                expire_over_date_beginning = self.env['wizard.coupon'].search(
                    [('state', '=', 'expire'), ('purchase_date', '<', self.date_from),
                     ('expiry_date', '>', self.date_from),
                     ('order_id.company_id', '=', self.env.user.company_id.id)])

            #coupon beginning balance all state
            beginning_coupon_ids = available_beginning_coupon_ids + redeem_over_date_beginning + expire_over_date_beginning

            ############# GL DETAIL############
            aml_line_ids = beginning_coupon_ids.mapped('order_id').filtered(lambda o: o.amount_total > 0).mapped('account_move').mapped('line_ids').filtered(
                lambda o: o.account_id == self.account_id)

            for aml in aml_line_ids:
                if aml.id not in aml_ids:
                    aml_ids.append(aml.id)
            ############# GL DETAIL############

            print ('BEGINNING',beginning_coupon_ids)
            beginning_use_coupon_ids = beginning_coupon_ids.filtered(
                lambda o: (o.state == 'redeem' and o.redeem_date <= self.date) or (
                        o.state == 'expire' and o.expiry_date <= self.date))
            all_use_coupon = beginning_use_coupon_ids
            coupon_ids = beginning_coupon_ids.filtered(
                lambda o: o.state == 'draft' or (o.state == 'redeem' and o.redeem_date > self.date) or (
                            o.state == 'expire' and o.expiry_date > self.date))
            coupon_available_amount = sum(coupon.amount for coupon in coupon_ids)
            ########### add coupon balance between month#######
            for balance_coupon_id in coupon_ids:
                balance_between_month.append(balance_coupon_id.id)
            ########### add coupon balance between month#######

            use_coupon_amount = sum(coupon.amount for coupon in beginning_use_coupon_ids)
            use_coupon_gl_amount = sum(coupon.move_id.amount for coupon in beginning_use_coupon_ids)
            log_val['use_time'] = str(datetime.now())

            ############# GL DETAIL############
            aml_line_ids = beginning_use_coupon_ids.mapped('move_id').mapped('line_ids').filtered(lambda o: o.account_id == self.account_id)
            for aml in aml_line_ids:
                print ('Add USE')
                if aml.id not in aml_ids:
                    aml_ids.append(aml.id)

            ############# GL DETAIL############


            note_for_missing = ''

            # for use_coupon in beginning_use_coupon_ids:
            #
            #     if not use_coupon.move_id and use_coupon.amount:
            #         note_for_missing += 'Coupon ' + use_coupon.name + ', NO GL' + '\r\n'
            #     elif use_coupon.move_id and use_coupon.move_id.amount != use_coupon.amount:
            #         if not use_coupon.move_id:
            #             note_for_missing += 'Coupon ' + use_coupon.name + ', Wrong Amount' + '\r\n'



            account_ids = beginning_coupon_ids.mapped('product_id').mapped('property_account_income_id')

            sum_coupon_session_balance = sum_coupon_gl_use = 0
            for account_id in account_ids:
                # print ('ACCOUNT CODE', account_id.code)
                # print ('ACCOUNT NAME', account_id.name)
                coupon_amount = sum(coupon_id.amount for coupon_id in beginning_coupon_ids)
                coupon_count = len(beginning_coupon_ids)
                # print ('Coupon Total', coupon_count)
                # print ('Total Coupon Amount', coupon_amount)
                coupon_available_amount_new = sum(coupon_id.amount for coupon_id in available_beginning_coupon_ids)
                coupon_expire_over_amount = sum(coupon_id.amount for coupon_id in expire_over_date_beginning)
                coupon_redeem_over_amount = sum(coupon_id.amount for coupon_id in redeem_over_date_beginning)

                # available_beginning_coupon_ids + redeem_over_date_beginning + expire_over_date_beginning


                params = (account_id.id, self.date_from,)
                aml_query = """SELECT sum(aml.credit) as sum_credit,sum(aml.debit) as sum_debit
                                                                   FROM account_move_line AS aml
                                                                   JOIN account_move m ON aml.move_id = m.id
                                                                   WHERE aml.account_id = %s and m.state = 'posted' and aml.date < %s
                                                                    GROUP BY aml.account_id
                                                                    """

                self.env.cr.execute(aml_query, params)
                res = self.env.cr.fetchall()
                # print ('RES',res)
                if res:
                    gl_balance = res[0][0] - res[0][1]
                else:
                    gl_balance = 0.00

                inv_row += 1
                # product_id = self.coupon_id
                # print (data['date'].strftime("%d/%m/%Y"))
                worksheet.write(inv_row, 0, strToDate(self.date_from) + relativedelta(days=-1), for_center)
                worksheet.write(inv_row, 1, 'ยกมา', for_right)
                worksheet.write(inv_row, 2, account_id.code, for_right)
                worksheet.write(inv_row, 3, account_id.name, for_right)
                if not self.is_gl_balance:
                    worksheet.write(inv_row, 4, gl_balance, for_right)
                    worksheet.write(inv_row, 5, coupon_amount, for_right)
                    worksheet.write(inv_row, 6, use_coupon_amount, for_right)
                    worksheet.write(inv_row, 7, use_coupon_gl_amount, for_right)
                    worksheet.write(inv_row, 8, coupon_available_amount, for_right)
                else:
                    worksheet.write(inv_row, 4, gl_balance, for_right)
                    worksheet.write(inv_row, 5, gl_balance, for_right)
                    worksheet.write(inv_row, 6, use_coupon_gl_amount, for_right)
                    worksheet.write(inv_row, 7, use_coupon_gl_amount, for_right)
                    coupon_available_amount = gl_balance - use_coupon_gl_amount
                    worksheet.write(inv_row, 8, coupon_available_amount, for_right)

                worksheet.write(inv_row, 9, note_for_missing, for_right)
                worksheet.write(inv_row, 11, coupon_available_amount_new, for_right)
                worksheet.write(inv_row, 12, coupon_expire_over_amount, for_right)
                worksheet.write(inv_row, 13, coupon_redeem_over_amount, for_right)

                sum_coupon_session_balance += coupon_available_amount
                sum_coupon_gl_use += use_coupon_gl_amount


            to_date = strToDate(self.date) + relativedelta(days=1)
            to_date = str(to_date)
            params = (self.date_from, to_date,self.env.user.company_id.id,)
            aml_query = """SELECT pos.id FROM pos_session AS pos 
                                     JOIN pos_config conf ON pos.config_id = conf.id
                                     WHERE pos.stop_at >= %s and pos.stop_at < %s and pos.state = 'closed' and conf.company_id = %s
                                     GROUP BY pos.id
                                     """

            self.env.cr.execute(aml_query, params)
            res = self.env.cr.fetchall()
            session_ids = []
            for session in res:
                session_ids.append(session[0])
            # print ('RES',res)
            # print ('session_ids',session_ids)
            session_with_coupon_ids = self.env['pos.session'].browse(session_ids)

            # print ('session_with_coupon_ids',session_with_coupon_ids)
            session_txt = ""
            if session_with_coupon_ids:
                for session_id in session_with_coupon_ids:
                    session_txt += str(session_id.name) + str(datetime.now()) + "\r\n"
                    reference = ""
                    if self.account_id:
                        account_ids = session_id.mapped('order_ids').mapped('account_move').mapped('line_ids').filtered(
                            lambda o: o.account_id == self.account_id).mapped('account_id')

                        #original
                        # account_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped(
                        #     'account_move').mapped('line_ids').filtered(
                        #     lambda o: o.account_id == self.account_id).mapped('account_id')

                        if not account_ids:
                            account_ids = session_id.mapped('order_ids').mapped('invoice_id').mapped('move_id').mapped('line_ids').filtered(lambda o: o.account_id == self.account_id).mapped('account_id')

                        if not account_ids:
                            account_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped('coupon_ids').mapped(
                                'product_id').mapped('property_account_income_id').filtered(
                                lambda o: o.id == self.account_id.id)

                        # account_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped(
                        #     'account_move').mapped('line_ids').filtered(
                        #     lambda o: o.account_id == self.account_id).mapped('account_id')

                    else:
                        account_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped('account_move').mapped('line_ids').mapped('account_id')

                        # account_ids = session_id.mapped('order_ids').mapped('coupon_ids').mapped('product_id').mapped(
                        #     'property_account_income_id')

                    # change from filter amount_total > 0 to all
                    account_move_ids = session_id.mapped('order_ids').filtered(lambda o: o.is_create_coupon).mapped('account_move')


                    # account_move_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped(
                    #     'account_move')

                    #change from filter amount_total > 0 to all
                    # account_invoice_ids_ids = session_id.mapped('order_ids').filtered(lambda o: o.amount_total > 0).mapped('invoice_id')
                    account_invoice_ids_ids = session_id.mapped('order_ids').mapped('invoice_id')

                    for account_id in account_ids:
                        # print ('ACCOUNT CODE', account_id.code)
                        # print ('ACCOUNT NAME', account_id.name)
                        coupon_account_ids = session_id.mapped('order_ids').mapped('coupon_ids').filtered(lambda o: o.product_id.property_account_income_id == account_id)
                        coupon_amount = sum(coupon_id.amount for coupon_id in coupon_account_ids)
                        coupon_count = len(coupon_account_ids)
                        # print ('Coupon Total', coupon_count)
                        # print ('Total Coupon Amount', coupon_amount)
                        coupon_ids = coupon_account_ids.filtered(lambda o: o.state == 'draft' or (o.state == 'redeem' and o.redeem_date > self.date) or (o.state == 'expire' and o.expiry_date > self.date))
                        ########### add coupon balance between month#######
                        for balance_coupon_id in coupon_ids:
                            balance_between_month.append(balance_coupon_id.id)
                        ########### add coupon balance between month#######
                        coupon_use_ids = coupon_account_ids.filtered(
                            lambda o: (o.state == 'redeem' and o.redeem_date <= self.date) or (
                                        o.state == 'expire' and o.expiry_date <= self.date))

                        all_use_coupon += coupon_use_ids
                        ############# GL DETAIL############
                        aml_line_ids = coupon_use_ids.mapped('move_id').mapped('line_ids').filtered(lambda o: o.account_id == self.account_id)
                        for aml in aml_line_ids:
                            # print('Add USE')
                            if aml.id not in aml_ids:
                                aml_ids.append(aml.id)
                        ############# GL DETAIL############

                        coupon_use_amount = sum(coupon.amount for coupon in coupon_use_ids)
                        coupon_use_gl_amount = sum(coupon.move_id.amount for coupon in coupon_use_ids)
                        note_for_missing = ''
                        for use_coupon in coupon_use_ids:
                            # if not use_coupon.move_id and use_coupon.amount:
                            #     note_for_missing += 'Coupon ' + use_coupon.name + ', NO GL' + '\r\n'
                            # elif use_coupon.move_id and use_coupon.move_id.amount != use_coupon.amount:
                            #     if not use_coupon.move_id:
                            #         note_for_missing += 'Coupon ' + use_coupon.name + ', Wrong Amount' + '\r\n'

                            if use_coupon.move_id and use_coupon.move_id and self.account_id:
                                aml_ids.append(aml.id for aml in use_coupon.move_id.line_ids.filtered(
                                    lambda o: o.account_id == self.account_id))



                        coupon_available_amount = sum(coupon.amount for coupon in coupon_ids)
                        detail = ''
                        for coupon_pending in coupon_ids:
                            detail += coupon_pending.name + ','


                        # print ('Coupon Ava Count Total', len(coupon_ids))
                        # print ('Total Ava Coupon Amount', coupon_available_amount)
                        total_amount = 0
                        if account_move_ids:
                            ############# GL DETAIL############
                            line_ids = account_move_ids[0].line_ids.filtered(lambda o: o.account_id == account_id)
                            for aml in line_ids:
                                if aml.id not in aml_ids:
                                    aml_ids.append(aml.id)
                            ############# GL DETAIL############

                            total_amount += sum(line_id.credit for line_id in line_ids)
                            total_amount -= sum(line_id.debit for line_id in line_ids)
                            reference = account_move_ids[0].name

                        if account_invoice_ids_ids:
                            for invoice in account_invoice_ids_ids.filtered(lambda o: o.state not in ('draft','cancel')):
                                ############# GL DETAIL############
                                line_ids = invoice.move_id.line_ids.filtered(lambda o: o.account_id == account_id)
                                for aml in line_ids:
                                    if aml.id not in aml_ids:
                                        aml_ids.append(aml.id)

                                ############# GL DETAIL############

                                total_amount += sum(line_id.credit for line_id in line_ids)
                                total_amount -= sum(line_id.debit for line_id in line_ids)
                                reference += invoice.number + ','


                        inv_row += 1

                        worksheet.write(inv_row, 0, strToDate(session_id.stop_at).strftime("%d/%m/%Y"), for_center)
                        worksheet.write(inv_row, 1, session_id.name, for_right)
                        worksheet.write(inv_row, 2, session_id.config_id.name, for_right)
                        worksheet.write(inv_row, 3, account_id.name, for_right)
                        worksheet.write(inv_row, 4, total_amount, for_right)
                        if not self.is_gl_balance:
                            worksheet.write(inv_row, 5, coupon_amount, for_right)
                            worksheet.write(inv_row, 6, coupon_use_amount, for_right)
                            worksheet.write(inv_row, 7, coupon_use_gl_amount, for_right)
                            worksheet.write(inv_row, 8, coupon_available_amount, for_right)
                        else:
                            worksheet.write(inv_row, 5, total_amount, for_right)
                            worksheet.write(inv_row, 6, coupon_use_amount, for_right)
                            worksheet.write(inv_row, 7, coupon_use_amount, for_right)
                            coupon_available_amount = total_amount - coupon_use_amount
                            worksheet.write(inv_row, 8, coupon_available_amount, for_right)

                        # worksheet.write(inv_row, 6, coupon_use_amount, for_right)
                        # worksheet.write(inv_row, 7, coupon_use_gl_amount, for_right)


                        worksheet.write(inv_row, 9, detail + '\r\n' + note_for_missing, for_right)
                        worksheet.write(inv_row, 10, reference, for_right)

                        sum_coupon_session_balance += coupon_available_amount
                        sum_coupon_gl_use += coupon_use_amount

                        if int(coupon_amount) != int(total_amount) and self.is_fix:
                            session_id.fix_session_coupon()



        else:
            raise UserError(_('เลือกคูปอง และ วันที่ ไม่ถูกต้อง'))

        log_val['session_time'] = session_txt

        # print ('AML IDS',aml_ids)
        if self.account_id:

            params = (account_id.id, self.date,)
            aml_query = """SELECT sum(aml.credit) as sum_credit,sum(aml.debit) as sum_debit
                                                                               FROM account_move_line AS aml
                                                                               JOIN account_move m ON aml.move_id = m.id
                                                                               WHERE aml.account_id = %s and m.state = 'posted' and aml.date <= %s
                                                                                GROUP BY aml.account_id
                                                                                """

            self.env.cr.execute(aml_query, params)
            res = self.env.cr.fetchall()
            # print ('RES',res)
            if res:
                end_balance = res[0][0] - res[0][1]
            else:
                end_balance = 0.00

            #######Old Query#############
            # to_date = strToDate(self.date) + relativedelta(days=1)
            # to_date = str(to_date)
            # params = (self.account_id.id, to_date,)
            # aml_query = """SELECT aml.id
            #                                                                    FROM account_move_line AS aml
            #                                                                    JOIN account_move m ON aml.move_id = m.id
            #                                                                    WHERE aml.account_id = %s and m.state = 'posted' and aml.date < %s
            #                                                                     GROUP BY aml.account_id, aml.id
            #                                                                     """
            #
            # self.env.cr.execute(aml_query, params)
            # res = self.env.cr.fetchall()
            # # print ('RES', res)
            # sum_debit = sum_credit = 0
            #
            # for line in res:
            #     # print ('line',line)
            #     aml = self.env['account.move.line'].browse(line[0])
            #     # if aml.move_id.journal_id.type != 'general' and aml.date >= self.date_from and abs(aml.balance) > 0:
            #     #     # if aml.ref:
            #     #     #     coupon_id = self.env['wizard.coupon'].search([('name','=',aml.ref)],limit=1)
            #     #     if line[0] not in aml_ids and aml.date >= '2021-01-01' and aml.ref and aml.ref[0:3] == 'CPN':
            #     #
            #     #         aml.move_id.sudo().button_cancel()
            #     #         aml.move_id.sudo().unlink()
            #     #         continue
            #     #         # missing_gl += aml.move_id.name + '=' + str(aml.credit - aml.debit) + '\r\n'
            #     #         # missing_gl_amount += aml.credit - aml.debit
            #
            #
            #     sum_debit += aml.debit
            #     sum_credit += aml.credit
            # #######Old Query#############


                # if
            # end_balance = sum_credit - sum_debit
            log_val['gl_time'] = str(datetime.now())




        else:
            end_balance = 0.00

        inv_row += 1
        worksheet.write(inv_row, 0, 'Sum', for_center)
        worksheet.write(inv_row, 1, "", for_right)
        worksheet.write(inv_row, 2, "", for_right)
        worksheet.write(inv_row, 3, "", for_right)
        worksheet.write(inv_row, 4, end_balance, for_right)
        worksheet.write(inv_row, 5, "", for_right)
        worksheet.write(inv_row, 6, "", for_right)
        worksheet.write(inv_row, 7, sum_coupon_gl_use, for_right)
        worksheet.write(inv_row, 8, sum_coupon_session_balance, for_right)
        worksheet.write(inv_row, 9, missing_gl, for_right)
        worksheet.write(inv_row, 10, missing_gl_amount, for_right)

        #########new work sheet#########
        if self.is_detail:
            worksheet = workbook.add_worksheet('Coupon Balance ยกมา')


            inv_row = 1
            # date_from = strToDate(self.date_from).strftime("%d/%m/%Y")
            at_date = strToDate(self.date_from) + relativedelta(days=-1)



            worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่ ' + str(at_date),
                                  GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'Coupon', for_center_bold)
            worksheet.write(inv_row, 1, 'Session', for_center_bold)
            worksheet.write(inv_row, 2, 'Order_id', for_center_bold)
            worksheet.write(inv_row, 3, 'Order Company', for_center_bold)
            worksheet.write(inv_row, 4, 'Purchase At', for_center_bold)
            worksheet.write(inv_row, 5, 'Purchase Date', for_center_bold)
            worksheet.write(inv_row, 6, 'Expiry Date', for_center_bold)
            worksheet.write(inv_row, 7, 'Redeem Date', for_center_bold)
            worksheet.write(inv_row, 8, 'Status', for_center_bold)
            worksheet.write(inv_row, 9, 'Amount', for_center_bold)
            total_coupon_amount = 0
            for balance_coupon_id in beginning_coupon_ids:
                inv_row += 1
                worksheet.write(inv_row, 0, balance_coupon_id.name, for_center_bold)
                worksheet.write(inv_row, 1, balance_coupon_id.sudo().session_id.name, for_center_bold)
                worksheet.write(inv_row, 2, balance_coupon_id.sudo().order_id.name, for_center_bold)
                worksheet.write(inv_row, 3, balance_coupon_id.sudo().order_id.company_id.name, for_center_bold)
                worksheet.write(inv_row, 4, balance_coupon_id.purchase_date, for_center_bold)
                worksheet.write(inv_row, 5, balance_coupon_id.sudo().order_branch_id.name, for_center_bold)
                worksheet.write(inv_row, 6, balance_coupon_id.expiry_date, for_center_bold)
                worksheet.write(inv_row, 7, balance_coupon_id.redeem_date, for_center_bold)
                worksheet.write(inv_row, 8, balance_coupon_id.state, for_center_bold)
                worksheet.write(inv_row, 9, balance_coupon_id.amount, for_center_bold)
                total_coupon_amount += balance_coupon_id.amount

            inv_row += 1
            worksheet.write(inv_row, 0, 'Total', for_center_bold)
            worksheet.write(inv_row, 9, total_coupon_amount, for_center_bold)


            ##################################################

            worksheet = workbook.add_worksheet('Coupon Balance ยกไป')
            # worksheet.col(0).width = 4000
            # worksheet.col(1).width = 10000
            # worksheet.col(2).width = 3000
            # worksheet.col(3).width = 4500
            # worksheet.col(4).width = 6000
            # worksheet.col(5).width = 6000
            # worksheet.col(6).width = 4000
            # worksheet.col(7).width = 4000
            # worksheet.col(8).width = 4000
            # worksheet.col(9).width = 4000
            # worksheet.col(10).width = 4000

            inv_row = 1
            # date_from = strToDate(self.date_from).strftime("%d/%m/%Y")
            at_date = strToDate(self.date).strftime("%d/%m/%Y")

            worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่ ' + at_date,
                                  GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'Coupon', for_center_bold)
            worksheet.write(inv_row, 1, 'Session', for_center_bold)
            worksheet.write(inv_row, 2, 'Order_id', for_center_bold)
            worksheet.write(inv_row, 3, 'Order Company', for_center_bold)
            worksheet.write(inv_row, 4, 'Purchase At', for_center_bold)
            worksheet.write(inv_row, 5, 'Purchase Date', for_center_bold)
            worksheet.write(inv_row, 6, 'Expiry Date', for_center_bold)
            worksheet.write(inv_row, 7, 'Redeem Date', for_center_bold)
            worksheet.write(inv_row, 8, 'Status', for_center_bold)
            worksheet.write(inv_row, 9, 'Amount', for_center_bold)
            total_coupon_amount = 0
            for balance_coupon_id in self.env['wizard.coupon'].browse(balance_between_month):
                inv_row +=1
                worksheet.write(inv_row, 0, balance_coupon_id.name, for_center_bold)
                worksheet.write(inv_row, 1, balance_coupon_id.sudo().session_id.name, for_center_bold)
                worksheet.write(inv_row, 2, balance_coupon_id.sudo().order_id.name, for_center_bold)
                worksheet.write(inv_row, 3, balance_coupon_id.sudo().order_id.company_id.name, for_center_bold)
                worksheet.write(inv_row, 4, balance_coupon_id.purchase_date, for_center_bold)
                worksheet.write(inv_row, 5, balance_coupon_id.sudo().order_branch_id.name, for_center_bold)
                worksheet.write(inv_row, 6, balance_coupon_id.expiry_date, for_center_bold)
                worksheet.write(inv_row, 7, balance_coupon_id.redeem_date, for_center_bold)
                worksheet.write(inv_row, 8, balance_coupon_id.state, for_center_bold)
                worksheet.write(inv_row, 9, balance_coupon_id.amount, for_center_bold)
                total_coupon_amount += balance_coupon_id.amount

            inv_row+=1
            worksheet.write(inv_row, 0, 'Total', for_center_bold)
            worksheet.write(inv_row, 9, total_coupon_amount, for_center_bold)

        #all coupon use##########################
        if self.is_use_detail:
            worksheet = workbook.add_worksheet('Coupon ใช้ไปทั้งหมด')
            inv_row = 1
            # date_from = strToDate(self.date_from).strftime("%d/%m/%Y")
            at_date = strToDate(self.date).strftime("%d/%m/%Y")

            worksheet.merge_range(0, 0, 0, 4, 'รายงานคูปอง ณ วันที่ ' + at_date,
                                  GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'Coupon', for_center_bold)
            worksheet.write(inv_row, 1, 'Session', for_center_bold)
            worksheet.write(inv_row, 2, 'Order_id', for_center_bold)
            worksheet.write(inv_row, 3, 'Order Company', for_center_bold)
            worksheet.write(inv_row, 4, 'Purchase At', for_center_bold)
            worksheet.write(inv_row, 5, 'Purchase Date', for_center_bold)
            worksheet.write(inv_row, 6, 'Expiry Date', for_center_bold)
            worksheet.write(inv_row, 7, 'Redeem Date', for_center_bold)
            worksheet.write(inv_row, 8, 'Status', for_center_bold)
            worksheet.write(inv_row, 9, 'Coupon Amount', for_center_bold)
            worksheet.write(inv_row, 10, 'GL Amount', for_center_bold)
            total_coupon_amount = total_gl_amount = 0
            for use_coupon_id in all_use_coupon:
                inv_row += 1
                worksheet.write(inv_row, 0, use_coupon_id.name, for_center_bold)
                worksheet.write(inv_row, 1, use_coupon_id.sudo().session_id.name, for_center_bold)
                worksheet.write(inv_row, 2, use_coupon_id.sudo().order_id.name, for_center_bold)
                worksheet.write(inv_row, 3, use_coupon_id.sudo().order_id.company_id.name, for_center_bold)
                worksheet.write(inv_row, 4, use_coupon_id.purchase_date, for_center_bold)
                worksheet.write(inv_row, 5, use_coupon_id.sudo().order_branch_id.name, for_center_bold)
                worksheet.write(inv_row, 6, use_coupon_id.expiry_date, for_center_bold)
                worksheet.write(inv_row, 7, use_coupon_id.redeem_date, for_center_bold)
                worksheet.write(inv_row, 8, use_coupon_id.state, for_center_bold)
                worksheet.write(inv_row, 9, use_coupon_id.amount, for_center_bold)
                worksheet.write(inv_row, 10, use_coupon_id.move_id.amount, for_center_bold)
                total_coupon_amount += use_coupon_id.amount
                total_gl_amount += use_coupon_id.move_id.amount

            inv_row += 1
            worksheet.write(inv_row, 0, 'Total', for_center_bold)
            worksheet.write(inv_row, 9, total_coupon_amount, for_center_bold)
            worksheet.write(inv_row, 10, total_gl_amount, for_center_bold)


        # log_val['total_time'] = str(datetime.now() - start_time)
        # self.env['wizard.log'].create(log_val)
        f_name = 'Coupon Report.xlsx'
        workbook.close()
        xlsx_data = fl.getvalue()
        wizard_id = self.env['coupon.select.excel.export'].create(
            {'report_file': base64.encodestring(xlsx_data), 'name': f_name})
        return {
            'view_mode': 'form',
            'res_id': wizard_id.id,
            'res_model': 'coupon.select.excel.export',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

        # # workbook.save(fl)
        # # fl.seek(0)
        # buf = base64.encodestring(fl.read())
        # cr, uid, context = self.env.args
        # ctx = dict(context)
        # ctx.update({'report_file': buf})
        # self.env.args = cr, uid, misc.frozendict(context)
        # ## To remove those previous saved report data from table. To avoid unwanted storage
        # self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        # wizard_id = self.env['coupon.select.excel.export'].create(
        #     vals={'name': 'Coupon Report.xlsx', 'report_file': ctx['report_file']})
        # # wizard_id = self.env['coupon.select.excel.export'].create(
        # #     vals={'name': 'Coupon Report.xls', 'report_file': ctx['report_file']})

        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'coupon.select.excel.export',
        #     'target': 'new',
        #     'context': ctx,
        #     'res_id': wizard_id.id,
        # }

    @api.multi
    def coupon_movement(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,##0.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")

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


        if self.coupon_id and self.date_from and self.date:
            # ----------------HEADDER-------------------------------------
            worksheet = workbook.add_sheet('Coupon Movement')
            worksheet.col(0).width = 4000
            worksheet.col(1).width = 10000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 4500
            worksheet.col(4).width = 6000
            worksheet.col(5).width = 6000
            worksheet.col(6).width = 4000
            worksheet.col(7).width = 4000
            worksheet.col(8).width = 4000
            worksheet.col(9).width = 4000
            worksheet.col(10).width = 4000
            # Search DATA
            # Purchase before >>>>>>
            data_temp = []

            params = (self.date_from,self.date_from,self.date_from, self.coupon_id.id,)
            initial_query = """SELECT aml.product_id,count(*),sum(aml.amount)
                                                   FROM wizard_coupon AS aml
                                                   JOIN project_project r ON aml.order_branch_id = r.id
                                                   JOIN operating_unit g ON r.operating_branch_id = g.id
                                                   WHERE aml.purchase_date < %s and (aml.state = 'draft' or (aml.state = 'redeem' and aml.redeem_date > %s) or (aml.state = 'expire' and aml.expiry_date > %s)) and aml.active = True and g.is_ou = True and aml.type = 'e-coupon' and aml.order_id is not Null and aml.product_id = %s
                                                    GROUP BY aml.product_id
                                                    """


            self.env.cr.execute(initial_query, params)
            res = self.env.cr.fetchall()
            if res:
                for line in res:
                    print (line)
                    val = {
                        'date': strToDate(self.date_from) + relativedelta(days=-1),
                        'in': line[1],
                        'out': 0,
                        'amount': line[2],
                        'balance':0,
                        'balance_amount': 0,
                        'code': '',
                    }
                    data_temp.append(val)
            print('data_temp:', data_temp)

            # # # purchase between
            params_1 = (self.date_from, self.date,self.coupon_id.id,)
            purchase_query = """SELECT aml.product_id,aml.purchase_date,aml.amount,aml.id,aml.name
                                                                           FROM wizard_coupon AS aml
                                                                           JOIN project_project r ON aml.order_branch_id = r.id
                                                                           JOIN operating_unit g ON r.operating_branch_id = g.id
                                                                           WHERE aml.purchase_date >= %s and aml.purchase_date <= %s and g.is_ou = True and aml.active = True and aml.type = 'e-coupon' and aml.order_id is not Null and aml.product_id = %s
                                                                            GROUP BY aml.product_id,aml.purchase_date,aml.amount,aml.id,aml.name
                                                                            """
            self.env.cr.execute(purchase_query, params_1)
            res = self.env.cr.fetchall()
            if res:
                for line in res:
                    print (line)
                    val = {
                        'date': strToDate(line[1]),
                        'in': 1,
                        'out': 0,
                        'amount': line[2],
                        'balance': 0,
                        'balance_amount': 0,
                        'code': line[4],
                        'id': line[3],
                    }
                    data_temp.append(val)
            print('data_temp:', data_temp)

            # # # redeem between
            params_2 = (self.date_from, self.date, self.coupon_id.id,)
            redeem_query = """SELECT aml.product_id,aml.redeem_date,aml.amount,aml.id,aml.name
                                                                           FROM wizard_coupon AS aml
                                                                           JOIN project_project r ON aml.order_branch_id = r.id
                                                                           JOIN operating_unit g ON r.operating_branch_id = g.id
                                                                           WHERE aml.redeem_date >= %s and aml.redeem_date <= %s and g.is_ou = True and aml.active = True and aml.type = 'e-coupon' and aml.order_id is not Null and aml.product_id = %s and aml.state = 'redeem'
                                                                            GROUP BY aml.product_id,aml.purchase_date,aml.amount,aml.id,aml.name
                                                                            """

            self.env.cr.execute(redeem_query, params_2)
            res = self.env.cr.fetchall()
            print ('reedeem---',res)
            if res:
                for line in res:
                    print (line)
                    val = {
                        'date': strToDate(line[1]),
                        'in': 0,
                        'out': 1,
                        'amount': line[2],
                        'balance': 0,
                        'balance_amount': 0,
                        'code': line[4],
                        'id': line[3],
                    }
                    data_temp.append(val)

            print('data_temp_3:', data_temp)

            # # # expire between
            params_3 = (self.date_from, self.date, self.coupon_id.id,)
            expire_query = """SELECT aml.product_id,aml.expiry_date,aml.amount,aml.id,aml.name
                                                                           FROM wizard_coupon AS aml
                                                                           JOIN project_project r ON aml.order_branch_id = r.id
                                                                           JOIN operating_unit g ON r.operating_branch_id = g.id
                                                                           WHERE aml.expiry_date >= %s and aml.expiry_date <= %s and g.is_ou = True and aml.active = True and aml.type = 'e-coupon' and aml.order_id is not Null and aml.product_id = %s and aml.state = 'expire'
                                                                            GROUP BY aml.product_id,aml.expiry_date,aml.amount,aml.id,aml.name
                                                                            """

            self.env.cr.execute(expire_query, params_3)
            res = self.env.cr.fetchall()
            if res:
                for line in res:
                    print (line)
                    val = {
                        'date': strToDate(line[1]),
                        'in': 0,
                        'out': 1,
                        'amount': line[2],
                        'balance': 0,
                        'balance_amount': 0,
                        'code':line[4],
                        'id': line[3],
                    }
                    data_temp.append(val)

            print('data_temp_4:', data_temp)

            check_product = []
            data_total_temp = []
            data_temp_new = sorted(data_temp, key=lambda aml: aml['date'])
            balance = 0
            balance_amount = 0.00
            for data_line in data_temp_new:
                print (data_line['in'])
                if int(data_line['in']) > 0:
                    balance = balance + int(data_line['in'])
                    balance_amount = balance_amount + float(data_line['amount'])
                else:
                    balance = balance - int(data_line['out'])
                    balance_amount = balance_amount - float(data_line['amount'])

                data_line['balance'] = balance
                data_line['balance_amount'] = round(balance_amount,2)

            print('data_temp_new', data_temp_new)
            date_from = strToDate(self.date_from).strftime("%d/%m/%Y")
            date = strToDate(self.date).strftime("%d/%m/%Y")
            inv_row = 1
            worksheet.write_merge(0, 0, 0, 4, 'รายงานคูปอง วันที่' + ' ' + date_from + 'ถึงวันที่ ' + date, GREEN_TABLE_HEADER)
            worksheet.write(inv_row, 0, 'วันที่', for_center_bold)
            worksheet.write(inv_row, 1, 'ซื้อ', for_center_bold)
            worksheet.write(inv_row, 2, 'ใช้/หมดอายุ', for_center_bold)
            worksheet.write(inv_row, 3, 'คงเหลือ', for_center_bold)
            worksheet.write(inv_row, 4, 'มูลค่า', for_center_bold)
            worksheet.write(inv_row, 5, 'CODE', for_center_bold)
            worksheet.write(inv_row, 6, 'Account CODE', for_center_bold)
            worksheet.write(inv_row, 7, 'Account Name', for_center_bold)
            worksheet.write(inv_row, 8, 'GL', for_center_bold)
            worksheet.write(inv_row, 9, 'Status', for_center_bold)

            for data in data_temp_new:
                inv_row += 1
                product_id = self.coupon_id
                print (data['date'].strftime("%d/%m/%Y"))
                worksheet.write(inv_row, 0, data['date'].strftime("%d/%m/%Y"), for_center)
                worksheet.write(inv_row, 1, data['in'], for_right)
                worksheet.write(inv_row, 2, data['out'], for_right)
                worksheet.write(inv_row, 3, data['balance'], for_right)
                worksheet.write(inv_row, 4, data['balance_amount'], for_right)
                worksheet.write(inv_row, 5, data['code'], for_left)
                worksheet.write(inv_row, 6, product_id.property_account_income_id.code, for_right)
                worksheet.write(inv_row, 7, product_id.property_account_income_id.name, for_right)


                if 'id' in data:
                    coupon_id = self.env['wizard.coupon'].browse(data['id'])

                    #### find purchase gl
                    if coupon_id and coupon_id.order_id.sudo() and coupon_id.order_id.sudo().account_move and data['in']:
                        gl = coupon_id.sudo().order_id.account_move.name
                    elif coupon_id and coupon_id.order_id.sudo() and coupon_id.order_id.sudo().invoice_id and data['in']:
                        gl = coupon_id.order_id.sudo().invoice_id.number
                    elif coupon_id and coupon_id.move_id.sudo() and data['out']:
                        gl = coupon_id.move_id.sudo().name
                    else:
                        gl = ""

                    worksheet.write(inv_row, 8, gl, for_right)
                    worksheet.write(inv_row, 9, coupon_id.state, for_right)
                else:

                    worksheet.write(inv_row, 8, "", for_right)
                    worksheet.write(inv_row, 9, "", for_right)





        else:
            raise UserError(_('เลือกคูปอง และ วันที่ ไม่ถูกต้อง'))

        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['coupon.select.excel.export'].create(
            vals={'name': 'Coupon Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coupon.select.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

class coupon_select_excel_export(models.TransientModel):
    _name = 'coupon.select.excel.export'

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
            'res_model': 'wizard.select.date',
            'target': 'new',
        }

coupon_select_excel_export()


class coupon_record_yearly(models.Model):
    _name = 'coupon.record.yearly'

    product_id = fields.Many2one('product.product',string='Coupon')
    qty = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Unit Price')
    value = fields.Float(string='Value')
    account_id = fields.Many2one('account.account',string='Account')
    date = fields.Date(string='Date')