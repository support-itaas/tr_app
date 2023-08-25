# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


class budget_report(models.TransientModel):
    _name = 'budget.report.detail'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    analytic_account = fields.Many2many('account.analytic.account', string='Analytic Account')


    def get_pos_budget(self):
        pos_all = []
        check_product = []
        line_temp = []
        if self.analytic_account:
            for analytic_id in self.analytic_account:
                pos_order_ids = self.env['pos.order'].sudo().search([('branch_id', '=', analytic_id.project_ids.id),
                                                                     ('date_order','>=',self.date_from),
                                                                     ('date_order','<=',self.date_to)])
                pos_all.append(pos_order_ids)

            for pos_all in pos_all:
                for pos in pos_all:
                    for pos_line in pos.lines:
                        if pos_line.product_id.property_account_income_id:
                            if pos_line.product_id.id not in check_product:
                                check_product.append(pos_line.product_id.id)
                                line_temp.append(pos_line)

        else:
            pos_order_ids = self.env['pos.order'].sudo().search([('date_order','>=',self.date_from),
                                                                 ('date_order','<=',self.date_to)])
            print('pos_order_ids////:',pos_order_ids)
            for pos_order_id in pos_order_ids:
                for pos_line in pos_order_id.lines:
                    if pos_line.product_id.property_account_income_id and pos_line.product_id.property_account_income_id.is_use == True :
                        if pos_line.product_id.property_account_income_id.id not in check_product:
                            check_product.append(pos_line.product_id.property_account_income_id.id)

        print('check_product:',check_product)
        return check_product

    def get_amount_expense_by_analytic(self,cost_by_account,analytic_id):
        cost_by_ana_all = []
        account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_expense', '=', True),
                                                                         ('date', '>=', self.date_from),
                                                                         ('date', '<=', self.date_to),
                                                                         ('analytic_account_id','=',analytic_id.id),
                                                                         ('account_id','=',cost_by_account.id)])

        balance = sum(aml.balance for aml in account_order_ids)

        return balance

    def get_amount_expense_by_name(self,analytic_id):
        cost_by_ana_all = []
        print('get_amount_expense_by_name')
        print('analytic_all:',analytic_id)
        account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_expense', '=', True),
                                                                         ('date', '>=', self.date_from),
                                                                         ('date', '<=', self.date_to),
                                                                         ('analytic_account_id','=',analytic_id.id)])
        print('account_order_isssssssds:',account_order_ids)
        account_order_ids = account_order_ids.mapped('account_id')
        print('account_order_ids_expense:',account_order_ids)
        return account_order_ids


    def get_amount_cost_by_analytic(self,cost_by_account,analytic_id):
        cost_by_ana_all = []
        print('get_amount_cost_by_analytic')
        print('analytic_all:',analytic_id)
        account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_cost', '=', True),
                                                                         ('date', '>=', self.date_from),
                                                                         ('date', '<=', self.date_to),
                                                                         ('analytic_account_id','=',analytic_id.id),
                                                                         ('account_id','=',cost_by_account.id)])

        print('account_order_idssssssssssssssssssssssss:',account_order_ids)
        balance = sum(aml.balance for aml in account_order_ids)

        return balance

    def get_amount_cost_by_name(self,analytic_id):
        cost_by_ana_all = []
        print('get_amount_cost_by_name')
        print('analytic_all:',analytic_id)
        account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_cost', '=', True),
                                                                         ('date', '>=', self.date_from),
                                                                         ('date', '<=', self.date_to),
                                                                         ('analytic_account_id','=',analytic_id.id)])

        account_order_ids = account_order_ids.mapped('account_id')
        print('account_order_ids:',account_order_ids)
        return account_order_ids



    def get_sum_account_cost(self,analytic_all):
        all_account_order=[]
        all_cost = []
        print('get_sum_account_cost:')
        print('========START============')
        for analytic in analytic_all:
            sum_cost = 0
            account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_cost', '=', True),
                                                                             ('date', '>=', self.date_from),
                                                                             ('date', '<=', self.date_to),
                                                                             ('analytic_account_id', '=',analytic.id)])
            for i in account_order_ids:
                sum_cost += i.balance
            all_cost.append(sum_cost)
        print('account_order_ids:',all_cost)
        print('balanceeeeeeeeeeeeeeeeeeeee:',all_cost)
        print('========END============')

        return all_cost

    def get_sum_account_expense(self,analytic_all):
        all_account_order=[]
        all_cost = []
        print('get_sum_account_cost:')
        print('========START============')
        for analytic in analytic_all:
            sum_cost = 0
            account_order_ids = self.env['account.move.line'].sudo().search([('account_id.is_expense', '=', True),
                                                                             ('date', '>=', self.date_from),
                                                                             ('date', '<=', self.date_to),
                                                                             ('analytic_account_id', '=',analytic.id)])
            for i in account_order_ids:
                sum_cost += i.balance
            all_cost.append(sum_cost)
        print('account_order_ids:',all_cost)
        print('balanceeeeeeeeeeeeeeeeeeeee:',all_cost)
        print('========END============')

        return all_cost

    def get_sum_pos(self, analytic):
        balance = 0
        pos_order_line = self.env['pos.order.line'].sudo().search(
            [('order_id.branch_id.analytic_account_id', '=', analytic.id),('order_id.state','in',('paid','done','invoiced')),
             ('order_id.date_order', '>=', self.date_from), ('order_id.date_order', '<=', self.date_to)])
        if pos_order_line:
            balance = sum(aml.price_subtotal_incl for aml in pos_order_line)
        return balance

    def get_amount_pos_by_order(self,account_id,analytic,pos_order):
        print('get_amount_pos------')
        # print('product_id:',account_id)
        # print('analytic,',analytic)
        balance = balance1 = balance2 = 0
        print ('account -id',account_id.id)
        print('account -id', account_id.code)
        print('account -id', account_id.name)

        account_company_id = self.env['account.account'].sudo().search([('code','=',account_id.code),('company_id','=',1)])

        pos_order_line = self.env['pos.order.line'].sudo().search([('order_id.id','=',pos_order.id),('order_id.state','in',('paid','done','invoiced')),('product_id.type', 'in', ('product','consu')),('product_id.property_account_income_id', '=', account_company_id.id),('order_id.branch_id.analytic_account_id', '=',analytic.id),('order_id.date_order','>=',self.date_from),('order_id.date_order','<=',self.date_to)])

        if pos_order_line:
            balance1 = sum(aml.price_subtotal_incl for aml in pos_order_line)
            print ('balance1',balance1)

        pos_order_line = self.env['pos.order.line'].sudo().search(
            [('order_id.id','=',pos_order.id),('product_id.type', '=', 'service'),('order_id.state','in',('paid','done','invoiced')),
             ('order_id.branch_id.analytic_account_id', '=', analytic.id),('order_id.date_order','>=',self.date_from),('order_id.date_order','<=',self.date_to)])

        print('pos_order_line SERVICE:', pos_order_line)
        if pos_order_line:
            # ('product_id.property_account_income_id', '!=', account_id.id)
            for line in pos_order_line:
                #this is pack
                if line.product_id.is_pack and line.product_id.product_pack_id:
                    print ('LINE------------IS PACK')
                    # print (line.product_id.name)
                    pack_total_price = sum(pack_line.product_id.lst_price * pack_line.product_quantity for pack_line in line.product_id.product_pack_id)
                    # print ('pack_total_price',pack_total_price)
                    # print ('line.price_subtotal_incl',line.price_subtotal_incl)
                    for pack_line in line.product_id.product_pack_id:
                        if pack_line.product_id.actual_income_account_id.id == account_company_id.id:
                            price = line.price_subtotal_incl * (pack_line.product_id.lst_price * pack_line.product_quantity / pack_total_price)
                            # print ('Price',price)
                            balance2 += price
                else:
                    print ('SERVICE NOT PACK')
                    price = 0
                    # print (line.product_id.default_code)
                    print ('line.product_id.property_account_income_id.id',line.product_id.property_account_income_id.id)
                    print('line.product_id.categ_id.property_account_income_categ_id.id',line.product_id.categ_id.property_account_income_categ_id.id)
                    print('account_id.id',account_id.id)
                    print('account_company_id.id', account_company_id.id)
                    if line.product_id.property_account_income_id.id == account_company_id.id:
                        price = line.price_subtotal_incl
                        balance2 += price
                    elif line.product_id.categ_id.property_account_income_categ_id.id == account_company_id.id:
                        price = line.price_subtotal_incl
                        balance2 += price

                    # print ('PRIE',price)



        print ('Balance 1 + 2')
        print ('balance1',balance1)
        print ('balance2', balance2)
        balance = balance1 + balance2
        return balance

    def get_amount_pos(self,account_id,analytic):
        print('get_amount_pos------')
        # print('product_id:',account_id)
        # print('analytic,',analytic)
        balance = balance1 = balance2 = 0
        print ('account -id',account_id.id)
        print('account -id', account_id.code)
        print('account -id', account_id.name)

        account_company_id = self.env['account.account'].sudo().search([('code','=',account_id.code),('company_id','=',1)])

        pos_order_line = self.env['pos.order.line'].sudo().search([('order_id.state','in',('paid','done','invoiced')),('product_id.type', 'in', ('product','consu')),('product_id.property_account_income_id', '=', account_company_id.id),('order_id.branch_id.analytic_account_id', '=',analytic.id),('order_id.date_order','>=',self.date_from),('order_id.date_order','<=',self.date_to)])
        # print('pos_order_line:',pos_order_line)
        # pos_order_line = self.env['pos.order.line'].sudo().search(
        #     [('order_id.state', 'in', ('paid', 'done', 'invoiced')), ('product_id.type', 'in', ('product', 'consu')),
        #      ('order_id.branch_id.analytic_account_id', '=', analytic.id),
        #      ('order_id.date_order', '>=', self.date_from), ('order_id.date_order', '<=', self.date_to)])
        # print('pos_order_line2222:', pos_order_line)
        # for order_line in pos_order_line:
        #     print(order_line.product_id.default_code)
        #     print(order_line.order_id.name)
        #     print (order_line.product_id.propertese ty_account_income_id.id)
        #     print(order_line.product_id.property_account_income_id.code)
        #     print(order_line.product_id.property_account_income_id.name)
        if pos_order_line:
            balance1 = sum(aml.price_subtotal_incl for aml in pos_order_line)
            print ('balance1',balance1)

        pos_order_line = self.env['pos.order.line'].sudo().search(
            [('product_id.type', '=', 'service'),('order_id.state','in',('paid','done','invoiced')),
             ('order_id.branch_id.analytic_account_id', '=', analytic.id),('order_id.date_order','>=',self.date_from),('order_id.date_order','<=',self.date_to)])

        print('pos_order_line SERVICE:', pos_order_line)
        if pos_order_line:
            # ('product_id.property_account_income_id', '!=', account_id.id)
            for line in pos_order_line:
                #this is pack
                if line.product_id.is_pack and line.product_id.product_pack_id:
                    print ('LINE------------IS PACK')
                    # print (line.product_id.name)
                    pack_total_price = sum(pack_line.product_id.lst_price * pack_line.product_quantity for pack_line in line.product_id.product_pack_id)
                    # print ('pack_total_price',pack_total_price)
                    # print ('line.price_subtotal_incl',line.price_subtotal_incl)
                    for pack_line in line.product_id.product_pack_id:
                        if pack_line.product_id.actual_income_account_id.id == account_company_id.id:
                            price = line.price_subtotal_incl * (pack_line.product_id.lst_price * pack_line.product_quantity / pack_total_price)
                            # print ('Price',price)
                            balance2 += price
                else:
                    print ('SERVICE NOT PACK')
                    price = 0
                    # print (line.product_id.default_code)
                    print ('line.product_id.property_account_income_id.id',line.product_id.property_account_income_id.id)
                    print('line.product_id.categ_id.property_account_income_categ_id.id',line.product_id.categ_id.property_account_income_categ_id.id)
                    print('account_id.id',account_id.id)
                    print('account_company_id.id', account_company_id.id)
                    if line.product_id.property_account_income_id.id == account_company_id.id:
                        price = line.price_subtotal_incl
                        balance2 += price
                    elif line.product_id.categ_id.property_account_income_categ_id.id == account_company_id.id:
                        price = line.price_subtotal_incl
                        balance2 += price

                    # print ('PRIE',price)



        print ('Balance 1 + 2')
        print ('balance1',balance1)
        print ('balance2', balance2)
        balance = balance1 + balance2
        return balance

    def get_product_special(self,analytic):
        print('get_product_special:')
        print('analytic:',analytic)
        project_id = analytic.project_ids[0]
        print('project_id:',project_id.name)
        pos_config = self.env['pos.config'].sudo().search([('branch_id', '=', project_id.id)])
        print('pos_config:',pos_config)
        print('pos_config:',pos_config.branch_id.name)
        print('pos_config.stock_location_id.id:',pos_config.stock_location_id.id)
        stock_move_ids = self.env['stock.move'].sudo().search([('product_id.is_special', '=', True),
                                                               ('date', '>=',self.date_from),
                                                               ('date', '<=',self.date_to),
                                                               ('state', '!=', 'cancel'),
                                                               ('location_id', '=',pos_config.stock_location_id.id),
                                                               ('location_dest_id.usage','=','customer')])

        # print('stock_move_ids:',stock_move_ids)
        # value = sum(aml.value for aml in stock_move_ids)
        value = 0
        for stock_move_id in stock_move_ids:
            # temporary change to this condition
            value += stock_move_id.product_uom_qty * stock_move_id.product_id.standard_price

        return value

    def get_product_special_sum(self, analytic_all):
        print('get_product_special_sum:')
        all_product_special = []
        for analytic in analytic_all:
            product_special = []
            sum_product = 0
            project_id = analytic.project_ids[0]
            pos_config = self.env['pos.config'].sudo().search([('branch_id', '=', project_id.id)])

            # temporary change to this condition for state != cancel
            stock_move_ids = self.env['stock.move'].sudo().search([('product_id.is_special', '=', True),
                                                                   ('date', '>=', self.date_from),
                                                                   ('date', '<=', self.date_to),
                                                                   ('state', '!=', 'cancel'),
                                                                   ('location_id', '=', pos_config.stock_location_id.id),
                                                                   ('location_dest_id.usage', '=', 'customer')])
            # print('analytic:',analytic)
            # print('stock_move_ids:',stock_move_ids)
            # if stock_move_ids:
            for stock_move_id in stock_move_ids:
                #temporary change to this condition
                sum_product += stock_move_id.product_uom_qty * stock_move_id.product_id.standard_price
                # sum_product += stock_move_id.value
            product_special.append(sum_product)
            # else:
            #     print('dddddddddd:', stock_move_ids)
            #     product_special.append(0.00)

            all_product_special.append(product_special)
        print('all_product_special:',all_product_special)
        return all_product_special



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
        for_left_head = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

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

        if self.analytic_account:
            analytic_all = self.analytic_account
        else:
            analytic_all = self.env['account.analytic.account'].sudo().search([('is_special', '=', True)])

        analytic = []
        for i in analytic_all:
            analytic.append(i.id)

        pos_order_ids = self.get_pos_budget()
        temp_pos_total = []
        temp_pos_total_sum = []

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Report งบศูนย์บริการ')
        worksheet.col(0).width = 3000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 10000
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
        worksheet.col(10).width = 4000

        worksheet.write(1, 1, 'งบกำไร(ขาดทุน)ศูนย์บริการ', for_center_bold)
        worksheet.write(2, 1, self.date_from + '-' + self.date_to, for_center_bold)


        inv_row = 4
        inv_amount = 4
        inv_colum_analytic = 2
        # ==========================
        # sum
        sum_amount_inv = 0
        sum_amount_colum = 0

        for analytic in analytic_all:
            worksheet.write(3, inv_colum_analytic, analytic.name, for_center_bold)
            inv_colum_analytic += 1

        # print('analytic_all:',analytic_all)
        # print('pos_order_idsvv:',pos_order_ids)

        ################Sum for each analytic for each account
        account_ids = self.env['account.account'].search([('is_use', '=', True)])
        print ('account_ids',account_ids)
        for account_id in account_ids:
            print ('account_id--name',account_id.name)
            print('account_id--code', account_id.code)
            inv_colum_analytic = 2
            inv_row += 1
            # account_ids = self.env['account.account'].sudo().search([('id', '=', pos_order_id)])
            worksheet.write(inv_row, 1, account_id.name, for_left)
            for analytic in analytic_all:
                amount_pos = self.get_amount_pos(account_id, analytic)
                print ('analytic',analytic.name)
                print ('amount_pos by analytic by account',amount_pos)
                worksheet.write(inv_row, inv_colum_analytic, amount_pos, for_right)
                inv_colum_analytic += 1
        ################Sum for each analytic for each account

        ################Sum for each analytic
        inv_row += 1
        inv_colum_analytic = 2
        amount_pos_ids = []
        for analytic in analytic_all:
            amount_pos = self.get_sum_pos(analytic)
            amount_pos_ids.append(amount_pos)
            worksheet.write(inv_row, inv_colum_analytic, amount_pos, for_right)
            inv_colum_analytic += 1

        # for amount in amount_pos:
        #     worksheet.write(inv_row, inv_colum_analytic, amount[0], for_right)
        #     inv_colum_analytic += 1
        ################Sum for each analytic

        inv_row += 1
        inv_colum_analytic = 1

        worksheet.write(inv_row, inv_colum_analytic, 'หัก-ต้นทุนน้ำยางานบริการ', for_left_head)

        inv_colum_analytic = 2
        for analytic in analytic_all:
            move_id = self.get_product_special(analytic)
            print ('get_product_special',move_id)

            worksheet.write(inv_row, inv_colum_analytic, move_id, for_right)
            inv_colum_analytic += 1

        inv_row += 1
        inv_colum_analytic = 1
        worksheet.write(inv_row, inv_colum_analytic, 'หัก-ต้นทุนสินค้า+บริการ', for_left_head)


        all_account_ids = self.env['account.account'].search([('is_cost','=',True)])
        print ('all_account_ids-is-cost',all_account_ids)
        for account_id in all_account_ids:
            print ('account-is-cost',account_id.name)
            print('account-is-cost', account_id.code)
            cost_by_analytic = self.get_amount_cost_by_name(analytic)
            print ('cost_by_analytic',cost_by_analytic)
            if cost_by_analytic:
                inv_row += 1
                inv_colum_analytic = 2
                worksheet.write(inv_row, 1, account_id.name, for_left)

                for analytic_id in analytic_all:
                    cost_by_analytic_amount = self.get_amount_cost_by_analytic(account_id, analytic_id)
                    print ('analytic_id',analytic_id.name)
                    print('cost_by_ana_id:', cost_by_analytic_amount)
                    worksheet.write(inv_row, inv_colum_analytic, cost_by_analytic_amount, for_right)
                    inv_colum_analytic += 1
        inv_row += 1
        worksheet.write(inv_row, 1, 'รวมต้นทุนบริการ', for_left_head)
        amount_account_cost = self.get_sum_account_cost(analytic_all)
        print ('get_sum_account_cost',amount_account_cost)

        inv_colum_analytic = 2
        for amount_cost in amount_account_cost:
            print ('amount_cost',amount_cost)
            worksheet.write(inv_row, inv_colum_analytic, amount_cost, for_right)
            inv_colum_analytic += 1

        inv_row += 1
        worksheet.write(inv_row, 1, 'กำไรขั้นต้น', for_left_head)
        inv_colum_analytic = 2

        move_id_sum = self.get_product_special_sum(analytic_all)
        print('move_id_sum:', move_id_sum)
        print('amount_pos:', amount_pos)
        print('amount_account_cost:', amount_account_cost)
        for i in range(len(amount_pos_ids)):
            worksheet.write(inv_row, inv_colum_analytic,
                            (amount_pos_ids[i] - amount_account_cost[i]) -
                            move_id_sum[i][0], for_right)
            inv_colum_analytic += 1

        inv_row += 1
        worksheet.write(inv_row, 1, 'หัก-ค่าใช้จ่ายในการขายและบริหาร', for_left_head)

        for analytic in analytic_all:
            cost_by_analytic_expense = self.get_amount_expense_by_name(analytic)
            for cost_by_account in cost_by_analytic_expense:
                inv_row += 1
                inv_colum_analytic = 2
                worksheet.write(inv_row, 1, cost_by_account.name, for_left)
                for analytic in analytic_all:
                    cost_by_analytic_expense = self.get_amount_expense_by_analytic(cost_by_account, analytic)
                    print('cost_by_ana_id:', cost_by_analytic)
                    worksheet.write(inv_row, inv_colum_analytic, cost_by_analytic_expense, for_right)
                    inv_colum_analytic += 1

        inv_row += 1
        worksheet.write(inv_row, 1, 'รวมค่าใช้จ่ายในการขายและบริหาร', for_left_head)

        amount_account_expense = self.get_sum_account_expense(analytic_all)
        inv_colum_analytic = 2
        for amount_cost in amount_account_expense:
            worksheet.write(inv_row, inv_colum_analytic, amount_cost, for_right)
            inv_colum_analytic += 1
        inv_row += 1
        worksheet.write(inv_row, 1, 'กำไร(ขาดทุน)', for_left_head)

        print('amount_account_expense:', amount_account_expense)

        inv_colum_analytic = 2
        for i in range(len(amount_pos_ids)):
            if amount_account_expense:
                worksheet.write(inv_row, inv_colum_analytic,
                                (amount_pos_ids[i] - amount_account_cost[i]) -
                                amount_account_expense[i], for_right)
            else:
                worksheet.write(inv_row, inv_colum_analytic,
                                (amount_pos_ids[i] - amount_account_cost[i]), for_right)

            inv_colum_analytic += 1

        ######################### End Work book##############

        ######################### Start Work Book รายได้ตรวจสอบ##############
        # ----------------HEADDER-------------------------------------
        # worksheet1 = workbook.add_sheet('Report งบศูนย์บริการ ตรวจสอบ')
        # worksheet1.col(0).width = 3000
        # worksheet1.col(1).width = 6000
        # worksheet1.col(2).width = 10000
        # worksheet1.col(3).width = 4500
        # worksheet1.col(4).width = 6000
        # worksheet1.col(5).width = 6000
        # worksheet1.col(6).width = 4000
        # worksheet1.col(7).width = 4000
        # worksheet1.col(8).width = 4000
        # worksheet1.col(9).width = 4000
        # worksheet1.col(10).width = 4000
        #
        # worksheet1.write(1, 1, 'งบกำไร(ขาดทุน)ศูนย์บริการ', for_center_bold)
        # worksheet1.write(2, 1, self.date_from + '-' + self.date_to, for_center_bold)
        # all_account_ids = self.env['account.account'].search([('is_use', '=', True)])
        #
        # col_account = 1
        # for account_id in all_account_ids:
        #     col_account +=1
        #     worksheet1.write(3, col_account, account_id.name, for_center_bold)
        #
        # inv_row = 3
        # if self.analytic_account:
        #     for analytic_id in self.analytic_account:
        #         pos_order_ids = self.env['pos.order'].sudo().search([('branch_id', '=', analytic_id.project_ids.id),
        #                                                              ('date_order','>=',self.date_from),
        #                                                              ('date_order','<=',self.date_to)])
        #         sum_pos_all = 0
        #         for pos_order in pos_order_ids:
        #             inv_row +=1
        #             inv_colum = 0
        #             worksheet1.write(inv_row, inv_colum, pos_order.name, for_right)
        #             inv_colum +=1
        #             worksheet1.write(inv_row, inv_colum, pos_order.amount_total, for_right)
        #
        #             sum_pos_all+= pos_order.amount_total
        #             sum_pos_each = 0
        #             for account_id in all_account_ids:
        #                 inv_colum += 1
        #                 amount_pos_order = self.get_amount_pos_by_order(account_id, analytic_id,pos_order)
        #                 sum_pos_each+= amount_pos_order
        #                 worksheet1.write(inv_row, inv_colum, amount_pos_order, for_right)
        #
        #             inv_colum+=1
        #             worksheet1.write(inv_row, inv_colum, sum_pos_each, for_right)
        #
        #         inv_row += 1
        #         inv_colum = 0
        #         worksheet1.write(inv_row, inv_colum, 'Sum', for_right)
        #         inv_colum += 1
        #         worksheet1.write(inv_row, inv_colum, sum_pos_all, for_right)

        ###################################### END Work Book-1#################

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())

        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['budget.excel.export'].create(
            vals={'name': 'งบศูนย์บริการ.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'budget.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


    #compare coupon and service use and stock request
    @api.multi
    def print_coupon_and_stock_report(self):
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
        for_left_head = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

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

        if self.analytic_account:
            analytic_all = self.analytic_account
        else:
            analytic_all = self.env['account.analytic.account'].sudo().search([('is_special', '=', True)])

        analytic = []
        for i in analytic_all:
            analytic.append(i.id)

        pos_order_ids = self.get_pos_budget()
        temp_pos_total = []
        temp_pos_total_sum = []

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Report คุปอง และ บริการ และ การเบิกน้ำยา')
        # worksheet.col(0).width = 3000
        # worksheet.col(1).width = 6000
        # worksheet.col(2).width = 10000
        # worksheet.col(3).width = 4500
        # worksheet.col(4).width = 6000
        # worksheet.col(5).width = 6000
        # worksheet.col(6).width = 4000
        # worksheet.col(7).width = 4000
        # worksheet.col(8).width = 4000
        # worksheet.col(9).width = 4000
        # worksheet.col(10).width = 4000

        worksheet.write(1, 1, 'Report คุปอง และ บริการ และ การเบิกน้ำยา', for_center_bold)
        worksheet.write(1, 2, self.analytic_account[0].name, for_center_bold)
        worksheet.write(2, 1, self.date_from + '-' + self.date_to, for_center_bold)

        pos_service_line_ids = self.env['pos.order.line'].search([('order_id.branch_id.analytic_account_id','=',self.analytic_account[0].id),('product_id.type','=','product'),('product_id.is_service','=',True),('order_id.date_order','>=',self.date_from),('order_id.date_order','<=',self.date_to)])
        print ('POS service line report',pos_service_line_ids)
        coupon_service_all_ids = self.env['wizard.coupon'].search([('branch_id.analytic_account_id','=',self.analytic_account[0].id),('redeem_date','>=',self.date_from),('redeem_date','<=',self.date_to),('state','=','redeem')])
        print('coupon_service_ids', coupon_service_all_ids)
        all_service = []
        order_service_ids = pos_service_line_ids.mapped('product_id')
        coupon_service_ids = coupon_service_all_ids.mapped('product_id').mapped('related_service_id')
        for order_service_id in order_service_ids:
            if order_service_id not in all_service:
                all_service.append(order_service_id)

        for coupon_service_id in coupon_service_ids:
            if coupon_service_id not in all_service:
                all_service.append(coupon_service_id)

        # print ('All service',all_service)
        # bom_ids =
        worksheet.write(3, 1, 'No', for_center_bold)
        worksheet.write(3, 2, 'Service Code', for_center_bold)
        worksheet.write(3, 3, 'Service Name', for_center_bold)
        worksheet.write(3, 4, 'Order QTY', for_center_bold)
        worksheet.write(3, 5, 'Coupon QTY', for_center_bold)
        worksheet.write(3, 6, 'Total QTY', for_center_bold)
        worksheet.write(3, 7, 'น้ำยา', for_center_bold)
        worksheet.write(3, 8, 'ปริมาณต่อบริการ', for_center_bold)
        worksheet.write(3, 9, 'น้ำยาที่เบิก/สั่ง', for_center_bold)
        worksheet.write(3, 10, 'น้ำยาที่ควรใช้', for_center_bold)
        worksheet.write(3, 11, 'น้ำยาที่ใช้มากกว่าที่สั่ง', for_center_bold)


        row = 3
        row_number = 0
        for service_id in all_service:
            row_number += 1
            row +=1
            product_use_id = False
            product_use_qty = 0
            if service_id.bom_ids and service_id.bom_ids[0].bom_line_ids:
                product_use_id = service_id.bom_ids[0].bom_line_ids[0].product_id
                product_use_qty = service_id.bom_ids[0].bom_line_ids[0].product_qty

            worksheet.write(row, 1, row_number, for_center_bold)
            worksheet.write(row, 2, service_id.default_code, for_center_bold)
            worksheet.write(row, 3, service_id.name, for_center_bold)
            order_service_qty = sum(pos_service_line_ids.filtered(lambda x: x.product_id == service_id).mapped('qty'))
            coupon_service_qty = len(coupon_service_all_ids.filtered(lambda x: x.product_id.related_service_id == service_id))
            total_service_qty = order_service_qty + coupon_service_qty
            worksheet.write(row, 4, order_service_qty, for_center_bold)
            worksheet.write(row, 5, coupon_service_qty, for_center_bold)
            worksheet.write(row, 6, total_service_qty, for_center_bold)
            if product_use_id:
                worksheet.write(row, 7, product_use_id.default_code, for_center_bold)
                worksheet.write(row, 8, product_use_qty, for_center_bold)
            else:
                worksheet.write(row, 7, "", for_center_bold)
                worksheet.write(row, 8, "", for_center_bold)

            request_stock_qty = 0.00
            worksheet.write(row, 9, request_stock_qty, for_center_bold)
            worksheet.write(row, 10, product_use_qty * total_service_qty, for_center_bold)
            worksheet.write(row, 11, product_use_qty * total_service_qty - request_stock_qty, for_center_bold)




        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())

        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['budget.excel.export'].create(
            vals={'name': 'Service Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'budget.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class budget_export(models.TransientModel):
    _name = 'budget.excel.export'

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
            'res_model': 'budget.report.detail',
            'target': 'new',
        }


