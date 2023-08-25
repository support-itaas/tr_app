# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#========For Excel========
from io import BytesIO
import xlwt
from xlwt import easyxf
import base64
from datetime import datetime,timedelta,date
# =====================
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class inventory_wizard(models.TransientModel):
    _name = 'inventory.age.wizard'
    
    date_from = fields.Date('Date', required="1")
    company_id = fields.Many2one('res.company', string='Company', required="1", default=lambda self:self.env.user.company_id.id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse', required="1")
    location_ids = fields.Many2one('stock.location', string='Locations')
    period_length = fields.Integer('Period Length (Days)', default=30, required="1")
    filter_by = fields.Selection([('by_product','Product'),('by_category','Product Category'),('account','Account')], string='Filter By')
    product_ids = fields.Many2many('product.product', string='Product', domain=[('type','=','product')])
    category_id = fields.Many2one('product.category', string='Product Category')
    account_id = fields.Many2one('account.account',string='Stock Account')
    excel_file = fields.Binary('Excel File')
    

    def get_products(self):
        product_pool=self.env['product.product']
        if not self.filter_by:
            return product_pool.search([('type','=','product')])
        else:
            if self.filter_by == 'by_product':
                if self.product_ids:
                    return self.product_ids
            elif self.filter_by == 'account':
                product_ids = product_pool.search([('categ_id.property_stock_valuation_account_id','=',self.account_id.id),('type','=','product')])
                if product_ids:
                    return product_ids
                else:
                    raise ValidationError("Product not found in selected category !!!")
            else:
                product_ids = product_pool.search([('categ_id','child_of',self.category_id.id),('type','=','product')])
                if product_ids:
                    return product_ids
                else:
                    raise ValidationError("Product not found in selected category !!!")
                   
                    

    def get_style(self):
        main_header_style = easyxf('font:height 300;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")
                                   
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz center;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        left_header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        
        text_left = easyxf('font:height 200; align: horiz left;')
        
        text_right = easyxf('font:height 200; align: horiz right;', num_format_str='0.00')
        
        text_left_bold = easyxf('font:height 200; align: horiz right;font:bold True;')
        
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;', num_format_str='0.00') 
        text_center = easyxf('font:height 200; align: horiz center;'
                             "borders: top thin,left thin,right thin,bottom thin")  
        
        return [main_header_style, left_header_style,header_style, text_left, text_right, text_left_bold, text_right_bold, text_center]
        
        
    
    

    def create_excel_header(self,worksheet,main_header_style,left_header_style,text_left):
        worksheet.write_merge(0, 1, 2, 5, 'Stock Inventory Aging', main_header_style)
        row = 3
        col=1
        worksheet.write(row,col, 'Date', left_header_style)
        date = self.date_from
        worksheet.write_merge(row,row, col+1, col+2, date, text_left)
        worksheet.write(row,col+3, 'Period Length', left_header_style)
        worksheet.write_merge(row,row, col+4, col+5, self.period_length, text_left)
        
        row+=1
        worksheet.write(row,col, 'Company', left_header_style)
        worksheet.write_merge(row,row, col+1, col+2, self.company_id.name or '', text_left)
        if self.filter_by:
            worksheet.write(row,col+3, 'Filter', left_header_style)
            if self.filter_by == 'by_product':
                worksheet.write_merge(row,row, col+4, col+5, 'Products', text_left)
            elif self.filter_by == 'account':

                worksheet.write_merge(row, row, col + 4, col + 5, 'Account:' + str(self.account_id.code) + '|' + str(self.account_id.name),text_left)
            else:
                worksheet.write_merge(row,row, col+4, col+5, 'Product Category', text_left)
                
                
        row+=1
        worksheet.write(row,col, 'Warehouse', left_header_style)
        ware_name = ', '.join(map(lambda x: (x.name), self.warehouse_ids))
        worksheet.write_merge(row,row, col+1, col+2, ware_name or '', text_left)
        if self.filter_by and self.filter_by == 'by_category':
            worksheet.write(row,col+3, 'Product Category', left_header_style)
            worksheet.write_merge(row,row, col+4, col+5, self.category_id.name or '', text_left)
        
        if self.location_ids:
            row+=1
            worksheet.write(row,col, 'Location', left_header_style)
            location_name = ', '.join(map(lambda x: (x.name), self.location_ids))
            worksheet.write_merge(row,row, col+1, col+3, location_name or '', text_left)
            
        row+=1
        return worksheet, row
        
        

    def create_table_header(self,worksheet,header_style,row,res):
        worksheet.write_merge(row, row+1, 0, 0, 'Code', header_style)
        worksheet.write_merge(row,row+1, 1, 3, 'Product', header_style)
        worksheet.write_merge(row,row+1, 4, 4, 'Total Qty', header_style)
        worksheet.write_merge(row,row+1, 5, 5, 'Total Value', header_style)
        worksheet.write_merge(row, row + 1, 6, 6, 'Date', header_style)
        worksheet.write_merge(row, row + 1, 7, 7, 'Reference', header_style)
        worksheet.write_merge(row,row, 8, 9, res['6']['name'], header_style)
        worksheet.write(row+1, 8, 'Qunatity', header_style)
        worksheet.write(row+1, 9, 'Value', header_style)
        worksheet.write_merge(row,row, 10, 11, res['5']['name'], header_style)
        worksheet.write(row+1, 10, 'Qunatity', header_style)
        worksheet.write(row+1, 11, 'Value', header_style)
        worksheet.write_merge(row,row, 12, 13, res['4']['name'], header_style)
        worksheet.write(row+1, 12, 'Qunatity', header_style)
        worksheet.write(row+1, 13, 'Value', header_style)
        worksheet.write_merge(row,row, 14, 15, res['3']['name'], header_style)
        worksheet.write(row+1, 14, 'Qunatity', header_style)
        worksheet.write(row+1, 15, 'Value', header_style)
        worksheet.write_merge(row,row, 16, 17, res['2']['name'], header_style)
        worksheet.write(row+1, 16, 'Qunatity', header_style)
        worksheet.write(row+1, 17, 'Value', header_style)
        worksheet.write_merge(row,row, 18, 19, res['1']['name'], header_style)
        worksheet.write(row+1, 18, 'Qunatity', header_style)
        worksheet.write(row+1, 19, 'Value', header_style)
        worksheet.write_merge(row,row, 20, 21, res['0']['name'], header_style)
        worksheet.write(row+1, 20, 'Qunatity', header_style)
        worksheet.write(row+1, 21, 'Value', header_style)
        row+=1
        return worksheet, row
    

    def get_aging_quantity(self,product,from_date,to_date=False,qty=0,value=0):
        quant_obj = self.env.get('stock.quant')
        total_qty = 0
        start_date = from_date
        stop_date = to_date
        if start_date:
            start_date = strToDate(str(start_date))
        if stop_date:
            stop_date = strToDate(str(stop_date))

        # if self.location_ids:
        #     location_ids = self.location_ids.ids
        #     domain = [('location_id', 'in', location_ids)]
        # elif self.warehouse_ids:
        #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = product.with_context(warehouse=self.warehouse_ids[0].id)._get_domain_locations()
        #     domain = domain_quant_loc

            # print ('DOmain lo',domain_quant_loc)
            # location_ids = domain_quant_loc.ids


        if start_date and stop_date:
            sml_in_ids = self.env['account.move.line'].search(
                    [('company_id','=',self.env.user.company_id.id),('account_id', '=', product.categ_id.property_stock_valuation_account_id.id),('product_id', '=', product.id), ('move_id.state','=','posted'),('quantity', '>', 0),('date','>=',str('2021-01-01')),('date','>=',str(start_date)),('date','<=',str(stop_date))],order='date desc')
        else:
            sml_in_ids = self.env['account.move.line'].search(
                [('company_id', '=', self.env.user.company_id.id), ('account_id', '=', product.categ_id.property_stock_valuation_account_id.id),('product_id', '=', product.id),
                 ('move_id.state', '=', 'posted'), ('quantity', '>', 0),
                 ('date','>=',str('2021-01-01')),('date', '<=', str(stop_date))],order='date desc')

        product_aging_ids = []
        pending_qty = qty
        pending_value = value
        if qty > 0:
            price_unit = value/qty
        else:
            price_unit = 0

        count = 0
        if sml_in_ids:
            for sml_in_id in sml_in_ids:
                count +=1

                if sml_in_id.ref and sml_in_id.ref[0:2] not in ['RR','RS','Cu','LL','RL','SR','Eป','PO','TK','JB'] and count != len(sml_in_ids):
                    if sml_in_id.ref == '' and sml_in_id.name[0:2] not in ['IN','MO']:
                        continue
                    elif sml_in_id.ref != '' and sml_in_id.date >= '2021-01-01':
                        continue

                if pending_qty <= 0 and pending_value <= 0:
                    break
                elif pending_qty <=0 and pending_value > 0:
                    if sml_in_id.move_id and sml_in_id.move_id.stock_move_id:
                        ref = sml_in_id.move_id.stock_move_id.reference
                    else:
                        ref = sml_in_id.move_id.ref

                    if ref[0:3] == 'INV':
                        continue
                    val = {
                        'date': strToDate(sml_in_id.date).strftime('%d/%m/%Y'),
                        'ref': ref,
                        'qty': 0.00,
                        'value': round(pending_value, 2)
                    }
                    product_aging_ids.append(val)
                    pending_value = 0.00

                else:
                    if count == len(sml_in_ids) and not start_date:
                        if sml_in_id.move_id and sml_in_id.move_id.stock_move_id:
                            ref = sml_in_id.move_id.stock_move_id.reference
                        else:
                            ref = sml_in_id.move_id.ref
                        if ref[0:3] == 'INV':
                            continue
                        val = {
                            'date': strToDate(sml_in_id.date).strftime('%d/%m/%Y'),
                            'ref': ref,
                            'qty': round(abs(pending_qty),2),
                            'value': round(abs(pending_value),2),
                        }
                    else:
                        if sml_in_id.move_id and sml_in_id.move_id.stock_move_id:
                            ref = sml_in_id.move_id.stock_move_id.reference
                        else:
                            ref = sml_in_id.move_id.ref

                        if ref[0:3] == 'INV':
                            continue
                        if pending_qty > sml_in_id.quantity:
                            temp_qty = round(abs(sml_in_id.quantity),2)
                            pending_qty -= round(abs(sml_in_id.quantity),2)
                        else:
                            temp_qty = pending_qty
                            pending_qty = 0.00

                        if sml_in_id.debit:
                            if pending_value > abs(sml_in_id.debit) and pending_qty > 0:
                                temp_value = abs(sml_in_id.debit)
                                pending_value -= round(abs(sml_in_id.debit),2)
                            else:
                                temp_value = abs(pending_value)
                                pending_value = 0.00
                        else:
                            if pending_value > abs(sml_in_id.credit):
                                temp_value = abs(sml_in_id.credit)
                                pending_value -= round(abs(sml_in_id.credit),2)
                            else:
                                temp_value = abs(pending_value)
                                pending_value = 0.00

                            # temp_value = abs(sml_in_id.credit)
                            # pending_value -= round(abs(sml_in_id.credit), 2)
                            #

                        val = {
                            'date': strToDate(sml_in_id.date).strftime('%d/%m/%Y'),
                            'ref': ref,
                            'qty': round(abs(temp_qty),2),
                            'value': round(abs(temp_value),2),
                        }

                    product_aging_ids.append(val)

        elif pending_qty > 0 and start_date and stop_date and str(stop_date) < '2021-01-01':
            old_sml_in_id = self.env['stock.move.line'].search(
                [('move_id.company_id','=',self.env.user.company_id.id),
                 ('location_id.usage', '!=', 'internal'), ('location_dest_id.usage', '=', 'internal'),
                 ('product_id', '=', product.id),
                 ('state', '=', 'done'), ('qty_done', '>', 0),('is_aging', '=', True),
                 ('date', '<', str(start_date))], limit=5, order='date asc')

            if not old_sml_in_id:
                sml_in_id = self.env['stock.move.line'].search(
                    [('move_id.company_id','=',self.env.user.company_id.id),
                     ('location_id.usage', '!=', 'internal'), ('location_dest_id.usage', '=', 'internal'),
                     ('product_id', '=', product.id),
                     ('state', '=', 'done'), ('qty_done', '>', 0),
                     ('date', '>', str(start_date)),('date', '<=', str(stop_date))], limit=1, order='date asc')

                if sml_in_id and sml_in_id.lot_id:
                    if sml_in_id.lot_id.name[0:2] not in ['RR','RS','Cu','LL','RL','SR','Eป','PO','JR','TK','JB']:
                        ref = sml_in_id.reference
                    else:
                        ref = sml_in_id.lot_id.name
                    move_date = strToDate(sml_in_id.date).strftime('%d/%m/%Y')

                    if ref[0:3] != 'INV':
                        val = {
                            'date': move_date,
                            'ref': ref,
                            'qty': round(pending_qty, 2),
                            'value': round(pending_value, 2)
                        }
                        product_aging_ids.append(val)

        elif pending_qty > 0 and not start_date:
            # sml_in_id = self.env['stock.move.line'].search(
            #     [('move_id.company_id','=',self.env.user.company_id.id),
            #      ('location_id.usage', '!=', 'internal'),('location_dest_id.usage', '=', 'internal'),
            #      ('product_id', '=', product.id),
            #      ('state', '=', 'done'), ('qty_done', '>', 0),
            #      ('date', '<=', str(stop_date))], limit=1, order='date asc')
            #
            # if sml_in_id and sml_in_id.lot_id:
            #     ref = sml_in_id.lot_id.name
            #     move_date = strToDate(sml_in_id.date).strftime('%d/%m/%Y')
            # else:
            #     ref = ""
            #     move_date = stop_date.strftime('%d/%m/%Y')

            ref = ""
            move_date = stop_date.strftime('%d/%m/%Y')

            val = {
                'date': move_date,
                'ref': ref,
                'qty': round(pending_qty,2),
                'value': round(pending_value,2)
            }
            product_aging_ids.append(val)

        return product_aging_ids

        # product_dict[str(data)] = total_qty

        # if to_date:
        #     product = product.with_context(to_date=to_date)
        # if self.warehouse_ids:
        #     product = product.with_context(warehouse=self.warehouse_ids.ids)
        # if self.location_ids:
        #     product = product.with_context(location=self.location_ids.ids)


        # return product.qty_available
    

    def create_table_values(self,worksheet,text_left,text_right,row,res,product_ids,text_right_bold):
        lst=[0,0,0,0,0,0,0]
        lst_val=[0,0,0,0,0,0,0]
        row = row+1
        total_qty = total_val=0
        # product_ids = product_ids.with_context(to_date=self.date_from).filtered(lambda p: p.qty_available > 0)

        self.env['account.move.line'].check_access_rights('read')
        # print ('product',product_ids.ids)
        fifo_automated_values = {}
        if self.account_id:
            account_id = self.account_id
        else:
            account_id = product_ids[0].categ_id.property_stock_valuation_account_id

        if account_id:
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                                     FROM account_move_line AS aml
                                    WHERE aml.product_id IS not null AND aml.account_id = %s AND aml.company_id=%s and aml.date <= %s
                                 GROUP BY aml.product_id, aml.account_id"""
            params = (account_id.id, self.env.user.company_id.id,self.date_from,)
        else:
            raise ValidationError("Please select account to process !!!")

        self.env.cr.execute(query, params=params)

        result = self.env.cr.fetchall()
        print ('RESULT--->',result)
        for row_result in result:
            # print(row)
            fifo_automated_values[(row_result[0], row_result[1])] = (row_result[2], row_result[3], list(row_result[4]))

        print ('fifo_automated_values',fifo_automated_values)
        for product in product_ids.filtered(lambda x: x.product_tmpl_id.valuation == 'real_time'):

            print ('Product---ID',product.id)
            stock_value, stock_qty, aml_ids = fifo_automated_values.get((product.id, product.categ_id.property_stock_valuation_account_id.id)) or (
                0, 0, [])
            # print ('Product',product.default_code)
            # print('Stock qty', stock_qty)
            # print('Stock Value', stock_value)

            # stock_qty = self.get_aging_quantity(product,False,self.date_from)
            if not stock_qty:
                continue

            worksheet.write_merge(row, row, 0, 0, product.default_code, text_left)
            worksheet.write_merge(row, row, 1, 3, product.name, text_left)

            total_qty += stock_qty
            ##value, that wrong
            total_val += stock_value

            worksheet.write(row, 4, stock_qty, text_right)
            worksheet.write(row, 5,stock_value, text_right)
            col=6
            found = False
            pending_qty = stock_qty
            pending_value = stock_value



            for i in range(7)[::-1]:
                from_qty = to_qty = qty = 0

                # print ('RES',res)
                # print (res[str(i)]['start'])
                # print(res[str(i)]['stop'])
                # if not found:

                if pending_qty > 0:
                    # print ('I RANGE',i)
                    product_aging_ids = self.get_aging_quantity(product,res[str(i)]['start'],res[str(i)]['stop'],pending_qty,pending_value)
                    if product_aging_ids:

                        for aging_id in product_aging_ids:
                            col = 6
                            pending_qty -= aging_id['qty']
                            pending_value -= aging_id['value']
                            lst[i] += aging_id['qty']
                            lst_val[i] += aging_id['value']
                            worksheet.write(row, col, aging_id['date'] or '', text_right)
                            col += 1
                            worksheet.write(row, col, aging_id['ref'] or '', text_right)
                            col += 1
                            #write range before
                            for y in range(6-i)[::1]:
                            # if i < 6:
                                worksheet.write(row, col, 0, text_right)
                                col += 1
                                worksheet.write(row, col, 0, text_right)
                                col += 1

                            worksheet.write(row, col, round(aging_id['qty'],2) or 0, text_right)
                            col += 1
                            worksheet.write(row, col, round(aging_id['value'],2) or 0, text_right)
                            col += 1

                            #write range after
                            for x in range(i)[::-1]:
                                worksheet.write(row, col, 0, text_right)
                                col += 1
                                worksheet.write(row, col, 0, text_right)
                                col += 1

                            row +=1

                    pending_qty = round(pending_qty,2)


                else:
                    break

                    # qty = 0.00
                    # worksheet.write(row, col, qty or 0, text_right)
                    # col += 1
                    # worksheet.write(row, col, qty or 0, text_right)
                    # col += 1

            # row+=1
#        
        worksheet.write_merge(row,row, 0, 2, 'TOTAL', text_right_bold)
        worksheet.write(row,4, total_qty or 0, text_right_bold)
        worksheet.write(row,5, total_val or 0, text_right_bold)
        col=8
        for i in range(7)[::-1]:
            worksheet.write(row,col, lst[i] or 0, text_right_bold)
            col+=1
            worksheet.write(row,col, lst_val[i] or 0, text_right_bold)
            col+=1
         
        return worksheet, row
        
        

    def get_aging_detail(self):
        res = {}
        period_length = self.period_length
        start = strToDate(self.date_from)
        print ('get_aging_detail------')
        for i in range(7)[::-1]:
            stop = start - relativedelta(days=period_length)
            res[str(i)] = {
                'name'  : (i != 0 and (str((7 - (i + 1)) * period_length) + '-' + str((7 - i) * period_length)) or ('+' + str(6 * period_length))),
                'value':'Values',
                'stop'  : start.strftime('%Y-%m-%d'),
                'start' : (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return res
    

    def print_excel(self):
        product_ids = self.get_products()
        #====================================
        # Style of Excel Sheet 
        excel_style = self.get_style()
        main_header_style = excel_style[0]
        left_header_style = excel_style[1]
        header_style = excel_style[2]
        text_left = excel_style[3]
        text_right = excel_style[4]
        text_left_bold = excel_style[5]
        text_right_bold = excel_style[6]
        text_center = excel_style[7]
        # ====================================
        
        
        
        # Define Wookbook and add sheet 
        workbook = xlwt.Workbook()
        filename = 'Stock Inventory Aging.xls'
        worksheet = workbook.add_sheet('Stock Inventory Aging')
        for i in range(0,120):
            if i > 5:
                worksheet.col(i).width = 110 * 30
            else:
                worksheet.col(i).width = 130 * 30

        # Print Excel Header
        worksheet,row = self.create_excel_header(worksheet,main_header_style,left_header_style,text_left)
        res = self.get_aging_detail()
        worksheet, row = self.create_table_header(worksheet,header_style,row+2,res)
        # print ('www',worksheet)
        # print('www', row)
        worksheet, row = self.create_table_values(worksheet,text_left,text_right,row,res,product_ids,text_right_bold)
        
        
        
        
        
        #download Excel File
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=inventory.age.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, filename),
                'target': 'new',
            }
    
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
