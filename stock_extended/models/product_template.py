# -*- coding: utf-8 -*-

# for more product stock calculation and report

from bahttext import bahttext
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import locale
import time
from odoo import api,fields, models
from odoo.osv import osv
# from odoo.report import report_sxw
from odoo.tools import float_compare, float_is_zero

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class product_template(models.Model):
    _inherit = 'product.template'

    def get_land_cost_by_move_by_product(self, move_id=False,product_id=False):
        move_line_ids = {}
        move_line_s = {}
        picking_id = False
        if move_id:
            move_id = self.env['stock.move'].browse(move_id)
            if move_id:
                picking_id = move_id.picking_id.id

        if picking_id and move_id.picking_id.picking_type_id.code == 'incoming':
            #print 'ooo'
            land_cost_ids = self.env['stock.landed.cost'].search([('picking_ids','in',picking_id),('state','=','done')])
            if land_cost_ids:
                if move_id.picking_type_id:
                    if move_id.picking_type_id.code == 'incoming':
                        move_in = True
                        move_out = False
                        if move_id.picking_id.is_reverse:
                            type = 'return-customer'
                        else:
                            type = 'purchase'
                    elif move_id.picking_type_id.code == 'outgoing':
                        move_in = False
                        move_out = True
                        if move_id.picking_id.is_reverse:
                            type = 'return-supplier'
                        else:
                            type = 'sale'


                for land_cost in land_cost_ids:
                    if land_cost.valuation_adjustment_lines:
                        if int(land_cost.amount_total) > 0:
                            type = 'debit'
                        else:
                            type = 'credit'

                        i = 1000
                        for line in land_cost.valuation_adjustment_lines:
                            if line.product_id.id == product_id:
                                # print "Product to Land Cost"
                                if land_cost.invoice_reference:
                                    ref = land_cost.invoice_reference.number
                                    reference = land_cost.name
                                else:
                                    ref = land_cost.name
                                    reference = line.move_id.picking_id.name,

                                move_line_s[i] = {
                                    'product_id': product_id,
                                    'name': line.product_id.name,
                                    'uom': line.product_id.uom_id.name,
                                    # 'price': line.additional_landed_cost,
                                    'price': line.former_cost_per_unit,
                                    'reference': reference,
                                    'date': strToDate(land_cost.date).strftime("%d/%m/%Y"),
                                    # 'qty': locale.format("%.2f", qty, grouping=True),
                                    'qty': 0,
                                    'move_in': move_in,
                                    'type': type,
                                    'move_out': move_out,
                                    ######### balance is additional cost
                                    'balance': line.additional_landed_cost/line.quantity,
                                    'total_price': line.additional_landed_cost,
                                    'sum_total_price_add': 0,
                                    'sum_total_price_use': 0,
                                    'remark': land_cost.landcost_reference,
                                    'duration': 0,
                                    'sum_use': 0,
                                    'sum_add': 0,
                                    'no_ref': ref,
                                    'move_id': move_id.id,
                                }
                                i+=1
                                move_line_ids = [value for key, value in move_line_s.items()]
        #print "land cost"
        #print move_line_ids

        return move_line_ids

    @api.multi
    def get_stock_move_by_product_by_date(self, date_from, date_to, product_id):
        move_line_ids = {}
        if product_id:
            # locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            product = self.env['product.product'].browse(product_id)
            # print product.name
            move_line_s = {}
            move_in = False
            move_out = False
            ################ move type ########
            #1- purchase
            #2- sale
            #3- production-out (use matterial)
            #4- return-supplier(return to supplier)
            #5- return-customer(return from customer)
            #6- set (ยอดยกมาก)
            #7- production-in (transfer from production to stock)
            #8- inventory-lost(ของเสีย ของหาย)
            ############################
            type = ''
            balance = 0
            sum_use = 0
            sum_add = 0
            sum_total_price_add = 0
            sum_total_price_use = 0
            remark = ""
            i = 0
            # product_id = self.env['product.product'].search([('name', '=', product.name)], limit=1)
            move_ids = self.env['stock.move'].search(
                [('product_id', '=', product_id), ('date', '>=', date_from), ('date', '<=', date_to),('state', '=', 'done')],order='date_expected asc')

            # print move_ids
            if move_ids:
                for move in move_ids:
                    # print move.picking_id.name
                    # print move.date_expected

                    remark = ""
                    # define reference number
                    if move.picking_id:
                        reference = move.picking_id.name
                        if move.picking_id.note:
                            remark = move.picking_id.note
                    elif move.origin:
                        reference = move.origin
                    else:
                        reference = move.name

                    # define date
                    # if move.create_date:
                    #     date = strToDate(move.create_date).strftime("%d/%m/%Y")

                    if move.date_expected:
                        date = strToDate(move.date_expected).strftime("%d/%m/%Y")
                    else:
                        date = False

                    # define qty
                    if move.product_uom_qty:
                        if product.uom_id.id == move.product_uom.id:
                            qty = move.product_uom_qty
                        else:
                            if move.product_uom.uom_type == 'reference':
                                #print "CASE1"
                                if product.uom_id.uom_type == 'bigger':
                                    #print "CASE1-1"
                                    qty = move.product_uom_qty / product.uom_id.factor_inv
                                else:
                                    #print "CASE1-2"
                                    qty = move.product_uom_qty * product.uom_id.factor

                            elif move.product_uom.uom_type == 'bigger':
                                #print "CASE2"
                                if product.uom_id.uom_type == 'reference':
                                    #print "CASE2-1"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv
                                else:
                                    #print "CASE2-2"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv * product.uom_id.factor
                            else:
                                #print "CASE3"
                                if product.uom_id.uom_type == 'reference':
                                    #print "CASE3-1"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv
                                else:
                                    #print "CASE3-2"
                                    qty = move.product_uom_qty / move.product_uom.factor_inv / product.uom_id.factor

                    else:
                        qty = 0

                    # define move_in and move_out
                    if move.picking_type_id:
                        if move.picking_type_id.code == 'incoming':
                            move_in = True
                            move_out = False
                            if move.picking_id.is_reverse:
                                type = 'return-customer'
                            else:
                                type = 'purchase'
                        elif move.picking_type_id.code == 'outgoing':
                            move_in = False
                            move_out = True
                            if move.picking_id.is_reverse:
                                type = 'return-supplier'
                            else:
                                type = 'sale'
                        # it is internal move
                        else:
                            if move.location_id and move.location_dest_id:
                                if move.location_id.usage == 'internal':
                                    if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or \
                                            move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
                                        move_in = False
                                        move_out = True
                                        if move.location_dest_id.usage == 'production':
                                            type = 'production-out'
                                        elif move.location_dest_id.usage == 'supplier':
                                            type = 'return-supplier'
                                        elif move.location_dest_id.usage == 'customer':
                                            type = 'sale'
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'inventory':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                        type = 'set'
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'production':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                        type = 'production-in'
                                    # production to scrapt
                                    elif move.location_dest_id.usage == 'inventory':
                                        move_in = False
                                        move_out = True
                                        type = 'inventory-lost'
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'supplier':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                        type = 'purchase'
                                    else:
                                        move_in = False
                                        move_out = False

                                # case claim and return
                                elif move.location_id.usage == 'customer':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                        type = 'return-customer'
                                    else:
                                        move_in = False
                                        move_out = False
                                else:
                                    move_in = False
                                    move_out = False
                            else:
                                move_in = False
                                move_out = False

                    # if no picking type
                    else:
                        if move.location_id and move.location_dest_id:
                            if move.location_id.usage == 'internal':
                                if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
                                    move_in = False
                                    move_out = True
                                    if move.location_dest_id.usage == 'production':
                                        type = 'production-out'
                                    elif move.location_dest_id.usage == 'supplier':
                                        type = 'return-supplier'
                                    elif move.location_dest_id.usage == 'customer':
                                        type = 'sale'

                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'inventory':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                    type = 'set'
                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'production':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                    type = 'production-in'
                                # production to scrapt
                                elif move.location_dest_id.usage == 'inventory':
                                    move_in = False
                                    move_out = True
                                    type = 'inventory-lost'
                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'supplier':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                    type = 'purchase'
                                else:
                                    move_in = False
                                    move_out = False

                            # case claim and return
                            elif move.location_id.usage == 'customer':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                    type = 'return-customer'
                                else:
                                    move_in = False
                                    move_out = False
                            else:
                                move_in = False
                                move_out = False

                    # only move_in or move_out action will be considered
                    if move_in or move_out:
                        if move.picking_id and move.picking_id.is_reverse:
                            # print "MOVE-1"
                            ref = move.picking_id.invoice_reference.number
                            remark = move.picking_id.invoice_reference.name

                        elif move.picking_id and move.picking_id.sale_id and move.picking_id.sale_id.invoice_ids:
                            # print "MOVE-2"
                            for invoice in move.picking_id.sale_id.invoice_ids:
                                ref = invoice.number

                        elif move.picking_id and move.picking_id.purchase_id and move.picking_id.purchase_id.invoice_ids:
                            # print "MOVE-3"
                            for invoice in move.picking_id.purchase_id.invoice_ids:
                                ref = invoice.reference

                        else:
                            # print move.picking_id.name
                            # print move.picking_id.sale_id
                            # print move.picking_id.sale_id.invoice_ids
                            # print "MOVE-4"
                            ref = move.origin

                        i += 1
                        move_line_s[i] = {
                            'product_id': product_id,
                            'name': move.product_id.name,
                            'uom': move.product_id.uom_id.name,
                            # 'price_unit': locale.format("%.2f", move.price_unit, grouping=True),
                            # 'price': locale.format("%.2f", price, grouping=True),
                            'price':move.price_unit,
                            'reference': reference,
                            'date': date,
                            # 'qty': locale.format("%.2f", qty, grouping=True),
                            'qty': qty,
                            'move_in': move_in,
                            'type': type,
                            'move_out': move_out,
                            'balance': balance,
                            'total_price': move.price_unit * qty,
                            'sum_total_price_add': move_in and move.price_unit * qty,
                            'sum_total_price_use': move_out and move.price_unit * qty,
                            'remark': remark,
                            'duration': (strToDate(date_to) - strToDate(date_from)).days + 1,
                            'sum_use' : move_out and qty,
                            'sum_add': move_in and qty,
                            'no_ref' : ref,
                            'move_id': move.id,
                        }

                        # print move_line_s[i]
                        # print "----------------"

        move_line_ids = [value for key, value in move_line_s.items()]
        #print "Get_Stock_MOVE_by Prduct by Date"
        #print move_line_s
        # print "xxxxxxxxxxxxx"
        # print move_line_ids
        # for i in range(0,len(move_line_ids),1):
        #     print move[i]
        # print "-------------"
        return move_line_ids

    def get_stock_move_out_quant_split_lot(self,move_id=False):
        move_line_s = {}
        move_line_ids = {}
        ############ if move out can be split lot to out from fifo
        if move_id:
            move_id = self.env['stock.move'].browse(move_id)
        if move_id and move_id.move_line_ids:
            i = 0
            for quant in move_id.move_line_ids:
                name = move_id.product_id.name
                uom = move_id.product_id.uom_id.name
                if not float_is_zero(quant.qty, precision_digits=2):
                    price = quant.cost
                else:
                    price = move_id.price_unit
                qty = quant.qty


                i += 1

                ###########in some move out may have move in back, example is move out and customer return it back
                if not move_line_s:
                    move_line_s[i] = {
                        'product_id': move_id.product_id.id,
                        'name': name,
                        'uom': uom,
                        'price': price,
                        'date': date,
                        'qty': qty,
                        'move_in': False,
                        'move_out': True,
                        'total_price': quant.inventory_value,
                    }
                # elif not float_compare(float(price),float(move_line_s[i - 1]['price']),precision_digits=2):
                #     move_line_s[i - 1]['qty'] += qty
                else:
                    i -=1
                    # print move_line_s[i - 1]['qty']
                    if float_compare(float(price), float(move_line_s[i]['price']), precision_digits=2):
                        i +=1
                        move_line_s[i] = {
                            'product_id': move_id.product_id.id,
                            'name': name,
                            'uom': uom,
                            'price': price,
                            'date': date,
                            'qty': qty,
                            'move_in': False,
                            'move_out': True,
                            'total_price': quant.inventory_value,
                        }
                    else:
                        move_line_s[i]['qty'] += qty


        ########### if move in, will be one by one
        move_line_ids = [value for key, value in move_line_s.items()]
        return move_line_ids

    def get_inventory_before(self,date,product_id):
        stock_history_obj = self.env['stock.quantity.history']
        new_date = strToDate(date)
        before_date = new_date + relativedelta(days=-1)
        product = self.env['product.product'].browse(product_id)
        stock_history_ids = stock_history_obj.search([('product_id','=',product_id),('date','<',date)])
        product_history = {}
        i = 0
        for history in stock_history_ids:
            sign = 1
            #if more than 0 then will be 1
            #if equal 0 then will be 0
            #if less than 0 then will be -1
            # print float_compare(history.quantity, 0, precision_digits=2)
            if float_compare(history.quantity,0,precision_digits=2) != 1:
                sign = -1
            if history.move_id.quant_ids:
                for quant in history.move_id.quant_ids:
                    # print history.move_id.picking_id.name
                    if quant.cost not in product_history:
                        product_history[quant.cost] = {
                            'product_id': product_id,
                            'qty': quant.qty * sign,
                            'cost': quant.cost,
                            'date' : before_date,
                            'reference_name' : history.move_id.picking_id.name,
                        }
                        i +=1
                    else:
                        product_history[quant.cost]['qty'] += (quant.qty * sign)

        # print "before key"
        # print product_history
        product_history = [value for key, value in product_history.items()]
        # print "YYYYYYYYYYYYYYY"
        # print product_history
        # print "--------------"
        return product_history

    def gl_balance(self,date,product_id):
        account_id = product_id.categ_id.property_stock_valuation_account_id
        params = (account_id.id,date,product_id.id,)
        aml_query = """SELECT sum(aml.credit) as sum_credit,sum(aml.debit) as sum_debit,sum(aml.quantity)
                                                                                       FROM account_move_line AS aml
                                                                                       JOIN account_move m ON aml.move_id = m.id
                                                                                       WHERE aml.account_id = %s and m.state = 'posted' and aml.date <= %s and aml.product_id = %s
                                                                                        GROUP BY aml.account_id
                                                                                        """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES',res)
        if res:
            end_balance = res[0][0] - res[0][1]
        else:
            end_balance = 0.00

        return res[0][2],end_balance



    def get_stock_before(self, date, product_id, location_ids,location_id):
        product_id = self.env['product.product'].browse(product_id)
        last_date = strToDate(date) + relativedelta(days=-1)
        if location_id and len(location_ids) == 1:
            # qty = product_id.with_context(to_date=date, location=location_ids.id).qty_at_date
            value = product_id.with_context(to_date=date, location=location_ids.id).stock_value
            res = product_id._compute_quantities_dict_by_location(location_ids, None, False, False, False,
                                                                  str(last_date))
            qty = res[product_id.id]['qty_available']
        elif location_id:
            # qty = product_id.with_context(to_date=date).qty_at_date
            value = product_id.with_context(to_date=date).stock_value
            res = product_id._compute_quantities_dict(None, False, False, False, str(last_date))
            qty = res[product_id.id]['qty_available']

        else:
            qty,value = self.gl_balance(date,product_id)
            # qty = product_id.with_context(to_date=date).qty_at_date
            # value = product_id.with_context(to_date=date).stock_value

        # last_date = strToDate(date) + relativedelta(days=-1)
        # if len(location_ids) == 1:
        #     res = product_id._compute_quantities_dict_by_location(location_ids,None, False, False, False, str(last_date))
        # else:
        #     res = product_id._compute_quantities_dict(None, False, False, False, str(last_date))
        #
        # qty_available = res[product_id.id]['qty_available']


        qty, value = self.gl_balance(date, product_id)
        value = abs(value)

        result = {
            'qty': qty,
            'value': value,
            'product_id': product_id,
            'reference': "Balance",
            'date': (strToDate(date) + relativedelta(days=-1)).strftime("%d/%m/%Y"),
        }
        print('get_stock_before : ',result)
        return result

    def get_stock_after(self, date_form, date_to, product_id, location_ids):
        # print('get_stock_after : ', date_form, date_to, product_id, location_ids)
        company_id = self.env.user.company_id
        domain = [('product_id', '=', product_id),
                  ('product_id.type', '=', 'product'),
                  ('state', '=', 'done'),
                  ('date', '>=', date_form),
                  ('date', '<=', date_to),
                  ('move_id.company_id', '=', company_id.id)
                  ]
        if location_ids:
            domain += ['|', ('location_id', 'in', location_ids.ids),
                       ('location_dest_id', 'in', location_ids.ids)]

        # print('get_stock_after domain: ', domain)
        all_transaction = self.env['stock.move.line'].search(domain, order='date ASC')
        # print('all_transaction : ', all_transaction)
        result = []
        for move in all_transaction:
            if len(location_ids) == 1:
                move_in, move_out, type = move.get_type_reference(location_ids[0])
            else:
                move_in, move_out, type = move.get_type_reference(False)

            print('test : ',move_in or move_out)
            if move_in or move_out:
                note = move.lot_id.name if move.lot_id else ''
                ref = move.get_no_reference()
                val_move = {
                    'qty': move.qty_done,
                    'date': move.date,
                    'value': move.product_id.with_context(to_date=move.date).stock_value,
                    'product_id': product_id,
                    'reference': move.reference,
                    'no_ref': ref,
                    'type': type,
                    'move_in': move_in,
                    'move_out': move_out,
                    'note': note,
                    'move_line_id': move,
                }
                result.append(val_move)

        return result

    def get_stock_after_old(self,date_form,date_to,product_id):
        company_id = self.env.user.company_id
        all_transaction = self.env['stock.move.line'].search([('date','>',date_form),
                                                              ('date','<=',date_to),
                                                              ('state','=','done'),
                                                              ('product_id','=',product_id),], order='date ASC')

        result = {}
        move_line_s = {}
        i = 0
        for line in all_transaction:
            move_in = False
            move_out = False

            print('line.picking_id.picking_type_id : ',line.picking_id.picking_type_id)
            print('reference : ',line.reference)
            if line.picking_id.picking_type_id:
                if line.picking_id.picking_type_id.code == 'incoming':
                    move_in = True
                    move_out = False
                    if line.picking_id.is_reverse:
                        type = 'return-customer'
                    else:
                        type = 'purchase'
                elif line.picking_id.picking_type_id.code == 'outgoing':
                    move_in = False
                    move_out = True
                    if line.picking_id.is_reverse:
                        type = 'return-supplier'
                    else:
                        type = 'sale'
                # it is internal move
                else:
                    if line.location_id and line.location_dest_id:
                        if line.location_id.usage == 'internal':
                            if line.location_dest_id.usage == 'inventory' or line.location_dest_id.usage == 'production' or \
                                    line.location_dest_id.usage == 'supplier' or line.location_dest_id.usage == 'customer':
                                move_in = False
                                move_out = True
                                if line.location_dest_id.usage == 'production':
                                    type = 'production-out'
                                elif line.location_dest_id.usage == 'supplier':
                                    type = 'return-supplier'
                                elif line.location_dest_id.usage == 'customer':
                                    type = 'sale'
                            else:
                                move_in = False
                                move_out = False

                        elif line.location_id.usage == 'inventory':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'set'
                            else:
                                move_in = False
                                move_out = False

                        elif line.location_id.usage == 'production':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'production-in'
                            # production to scrapt
                            elif line.location_dest_id.usage == 'inventory':
                                move_in = False
                                move_out = True
                                type = 'inventory-lost'
                            else:
                                move_in = False
                                move_out = False

                        elif line.location_id.usage == 'supplier':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'purchase'
                            else:
                                move_in = False
                                move_out = False

                        # case claim and return
                        elif line.location_id.usage == 'customer':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'return-customer'
                            else:
                                move_in = False
                                move_out = False
                        else:
                            move_in = False
                            move_out = False
                    else:
                        move_in = False
                        move_out = False

            # if no picking type
            else:
                if line.location_id.sudo().company_id == company_id:
                    if line.location_id and line.location_dest_id:
                        if line.location_id.sudo().usage == 'internal':
                            if line.location_dest_id.usage == 'inventory' or line.location_dest_id.usage == 'production' or \
                                    line.location_dest_id.usage == 'supplier' or line.location_dest_id.usage == 'customer':
                                move_in = False
                                move_out = True
                                if line.location_dest_id.usage == 'production':
                                    type = 'production-out'
                                elif line.location_dest_id.usage == 'supplier':
                                    type = 'return-supplier'
                                elif line.location_dest_id.usage == 'customer':
                                    type = 'sale'
                            else:
                                move_in = False
                                move_out = False
                        elif line.location_id.usage == 'inventory':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'set'
                            else:
                                move_in = False
                                move_out = False
                        elif line.location_id.usage == 'production':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'production-in'
                            # production to scrapt
                            elif line.location_dest_id.usage == 'inventory':
                                move_in = False
                                move_out = True
                                type = 'inventory-lost'
                            else:
                                move_in = False
                                move_out = False
                        elif line.location_id.usage == 'supplier':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'purchase'
                            else:
                                move_in = False
                                move_out = False

                        # case claim and return
                        elif line.location_id.usage == 'customer':
                            if line.location_dest_id.usage == 'internal':
                                move_in = True
                                move_out = False
                                type = 'return-customer'
                            else:
                                move_in = False
                                move_out = False
                        else:
                            move_in = False
                            move_out = False
                else:
                    move_in = False
                    move_out = False

            if move_in or move_out:
                if line.lot_id:
                    note = line.lot_id.name
                else:
                    note = ""

                if line.picking_id and line.picking_id.is_reverse:
                    # print "MOVE-1"
                    ref = line.picking_id.invoice_reference.number
                    remark = line.picking_id.invoice_reference.name

                elif line.picking_id and line.picking_id.sale_id and line.picking_id.sale_id.invoice_ids:
                    # print "MOVE-2"
                    for invoice in line.picking_id.sale_id.invoice_ids:
                        ref = invoice.number

                elif line.picking_id and line.picking_id.purchase_id and line.picking_id.purchase_id.invoice_ids:
                    # print "MOVE-3"
                    for invoice in line.picking_id.purchase_id.invoice_ids:
                        ref = invoice.reference

                else:
                    # print move.picking_id.name
                    # print move.picking_id.sale_id
                    # print move.picking_id.sale_id.invoice_ids
                    # print "MOVE-4"
                    ref = line.sudo().move_id.origin

                i+=1
                move_line_s[i]= {
                    'qty': line.qty_done,
                    'date': line.date,
                    'value': line.product_id.with_context(to_date=line.date).stock_value,
                    'product_id': product_id,
                    'reference': line.reference,
                    'no_ref': ref,
                    'type': type,
                    'move_in': move_in,
                    'move_out': move_out,
                    'note': note,
                    'move_line_id':line,
                }
                # print('more tran -----')
                # print('stock move line : ', line)
                # print('stock move value : ', line.sudo().move_id)
                # print('stock move line value : ', line.sudo().move_id.value)
                # print('product_id : ', product_id)
                # print('value : ', line.product_id.with_context(to_date=line.date).stock_value)
                # print('reference : ', line.reference)

        result = [value for key, value in move_line_s.items()]

        print ("result : ",result)
        return result

    def get_inventory_after(self,before=False,transaction=False):
        # print "before start"
        # print before
        # print "before end"
        # print "trans start"
        # print transaction
        # print "trans end"
        new_transaction = {}
        existing_record = False
        # print "BEFORE & TRANS"
        # print before
        # print transaction
        if before:
            for line_before in before:
                #############if move_in or move_out with one lot then will do normal
                move_quant_ids = self.get_stock_move_out_quant_split_lot(transaction['move_id'])
                # print "xxxxxxxxxxxxxxxxxxxx"
                # print transaction['move_in']
                # print len(move_quant_ids)
                # print "xxxxxxxxxxxxxxxxxxxx"
                if transaction and (transaction['move_in'] or len(move_quant_ids) == 1):
                    # print "move in or 1 quant"
                    # check for transaction with the same price then adjust qty for more or less
                    # move out will alway in existing price
                    # move in may same or difference price
                    if not float_compare(float(transaction['price']),float(line_before['cost']),precision_digits=2):
                        if transaction['move_in'] and transaction['qty']:
                            line_before['qty'] = float(line_before['qty']) + float(transaction['qty'])
                        if transaction['move_out'] and transaction['qty']:
                            line_before['qty'] = float(line_before['qty']) - float(transaction['qty'])

                        #######This is original, under compare price
                        ###### this is land cost
                        # print "transaction['qty']"
                        # print transaction['qty']
                        if not transaction['qty']:
                            # print "Update Price Land Cost"
                            # print line_before['cost']
                            # print transaction['balance']
                            line_before['cost'] = line_before['cost'] + transaction['balance']

                        existing_record = True

                        ######change 30/03/2018, remove breack, will check if concern anything
                        break

                    ############This is new one, just check tran qty if not then it is land cost
                    # print "transaction['qty']"
                    # print transaction['qty']
                    # if not transaction['qty']:
                    #     print "Update Price Land Cost"
                    #     print line_before['cost']
                    #     print transaction['balance']
                    #     line_before['cost'] = line_before['cost'] + transaction['balance']


                ######## this is for move out only, even move in can have move quant more than 1 but will not consider this condition
                ######## due to it was select first if
                elif transaction and move_quant_ids > 1:
                    # print "more than 1 quant"
                    for move_quant in move_quant_ids:
                        if not float_compare(float(move_quant['price']),float(line_before['cost']),precision_digits=2):
                            line_before['qty'] = float(line_before['qty']) - float(move_quant['qty'])

                    existing_record = True

            # if move in with new price
            if not existing_record:
                new_transaction[int(transaction['price'])] = {
                    'product_id': transaction['product_id'],
                    'qty': transaction['qty'],
                    'cost': transaction['price'],
                    'date': transaction['date'],
                    'reference_name': transaction['reference'],
                }
                before += [value for key, value in new_transaction.items()]

        #if not existing stock
        else:
            before = {}
            if transaction:
                new_transaction[int(transaction['price'])]= {
                    'product_id': transaction['product_id'],
                    'qty': transaction['qty'],
                    'cost': transaction['price'],
                    'date': transaction['date'],
                    'reference_name': transaction['reference'],
                }
                before = [value for key, value in new_transaction.items()]
        # print "before ***"
        # print before
        # print "before end"
        return before


########################stock report with cost #####################3
class report_product_stock_report(models.AbstractModel):
    _name = 'report.stock_extended.product_stock_report_id'

    @api.multi
    def get_stock_move_product(self, date_from, date_to, location_ids, category_id, product_id, company_id):
        domain = [('date', '>', date_from),
                  ('date', '<=', date_to),
                  ('state', '=', 'done'),
                  ('product_id.type', '=', 'product'),
                  ('move_id.company_id', '=', company_id)
                  ]
        if product_id:
            domain += [('product_id', '=', product_id[0])]
        if location_ids:
            domain += ['|', ('location_dest_id', 'in', location_ids.ids),
                       ('location_id', 'in', location_ids.ids)]
        if category_id:
            domain += [('product_id.categ_id', '=', category_id[0])]

        # print('get_stock_move_product domain: ',domain)
        product_ids = self.env['stock.move.line'].search(domain, order='product_id').mapped('product_id')
        # print('*stock domain: ', len(self.env['stock.move.line'].search(domain).mapped('move_id')))
        # print('product_ids domain: ', product_ids)
        return product_ids

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        company_id = self.env['res.company'].browse(data['form']['company_id'][0])
        active_model = self.env['product.template']

        if not data['form']['location_id']:
            location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        else:
            location_ids = self.env['stock.location'].search([('id', '=', data['form']['location_id'][0])])

        docs = self.get_stock_move_product(data['form']['date_from'], data['form']['date_to'],
                                           location_ids, data['form']['category_id'],
                                           data['form']['product_id'], data['form']['company_id'][0])

        if not docs:
            raise UserError(_('Document empty'))

        return {
            'doc': self,
            'doc_model': active_model,
            'data': data['form'],
            'date_from': datetime.strptime(data['form']['date_from'], '%Y-%m-%d').strftime('%d/%m/%Y'),
            'date_to': datetime.strptime(data['form']['date_to'], '%Y-%m-%d').strftime('%d/%m/%Y'),
            'company_id': company_id,
            'docs': docs,
            'time': time,
            'location_ids': location_ids,
        }


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def get_type_reference(self, location_to):
        move_in = False
        move_out = False
        type = ''

        # Incoming
        # <filter string="Incoming" name="incoming"
        # domain="[('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))]"/>
        # domain="[('location_id.usage', 'in', ('internal', 'transit')), ('location_dest_id.usage', 'not in', ('internal', 'transit'))]"/>
        # <filter string="Receptions" name="incoming" domain="[('picking_id.picking_type_id.code','=','incoming')]"/>
        # <filter string="Deliveries" name="outgoing" domain="[('picking_id.picking_type_id.code','=','outgoing')]"/>
        # <filter string="Internal" name="internal" domain="[('picking_id.picking_type_id.code','=','internal')]"/>
        # <filter string="Manufacturing" name="manufacturing" domain="[('picking_id.picking_type_id.code','=','mrp_operation')]"/>

        if self.move_id.location_id.usage not in ('internal', 'transit', 'view') and self.move_id.location_dest_id.usage in ('internal', 'transit', 'view'):
            move_in = True
            move_out = False

            if self.location_id.usage == 'inventory':
                type = 'set'
            elif self.location_id.usage == 'production':
                type = 'production-in'
            elif self.picking_id.is_reverse:
                type = 'return-customer'
            elif not self.picking_id.is_reverse:
                type = 'purchase'

        # Outgoing
        elif self.move_id.location_id.usage in ('internal', 'transit', 'view') and self.move_id.location_dest_id.usage not in ('internal', 'transit', 'view'):
            move_in = False
            move_out = True

            if self.location_dest_id.usage == 'inventory':
                type = 'inventory-lost'
            elif self.location_dest_id.usage == 'production':
                type = 'production-out'
            elif self.picking_id.is_reverse:
                type = 'return-supplier'
            elif not self.picking_id.is_reverse:
                type = 'sale'

        else:
            if location_to:
                if self.location_id == location_to:
                        move_in = False
                        move_out = True
                else:
                    move_in = True
                    move_out = False
                type = ''

        print('self.move_id.reference : ',self.move_id.reference)
        print('move_in, move_out, type : ',move_in, move_out, type)

        return move_in, move_out, type

    def get_no_reference(self):
        ref = ""
        number = ""
        if self.move_id.sale_line_id:
            number = self.move_id.sale_line_id.invoice_lines.mapped('invoice_id').mapped('number')
        elif self.move_id.purchase_line_id:
            number = self.move_id.purchase_line_id.invoice_lines.mapped('invoice_id').mapped('number')
        elif self.move_id.picking_id and self.move_id.picking_id.is_reverse:
            ref = self.move_id.picking_id.invoice_reference.number
        # else:
        #     ref = self.move_id.origin

        if number:
            ref = ", ".join(number)

        return ref