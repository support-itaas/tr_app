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

class product_product(models.Model):
    _inherit = 'product.product'

    def get_inventory_at_date(self,product_id,location_id,date):
        # product_id = self.product_id
        # location_id = self.location_id
        # date = self.date
        stock_history_obj = self.env['stock.history']
        if product_id and location_id and date:
            self.env.cr.execute('SELECT s.product_id, p.name, sum(s.quantity) as quantity, count(s.product_id) as product_id_count FROM stock_history s JOIN product_template p ON p.id=s.product_template_id where s.product_id = %s and s.date <= %s and s.location_id = %s group by s.product_id, p.name order by p.name',(product_id.id, date,location_id.id))
        res = self.env.cr.dictfetchall()

        group_lines = {}
        for line in res:
            domain = [('date', '<=', date), ('product_id', '=', product_id.id)]
            if location_id:
                domain.append(('location_id', '=', location_id.id))
            line['__domain'] = domain
            group_lines.setdefault(str(domain), stock_history_obj.search(domain))

        line_ids = set()
        for ids in group_lines.values():
            for product_find_id in ids:
                line_ids.add(product_find_id.id)
        lines_rec = {}
        if line_ids:
            move_ids = tuple(abs(line_id) for line_id in line_ids)
            self.env.cr.execute('SELECT id, product_id, price_unit_on_quant, company_id, quantity FROM stock_history WHERE move_id in %s', (move_ids,))
            res_new = self.env.cr.dictfetchall()
            lines_rec = tuple(rec for rec in res_new if rec['id'] in line_ids)
        lines_dict = dict((line['id'], line) for line in lines_rec)
        product_ids = list(set(line_rec['product_id'] for line_rec in lines_rec))
        products_rec = self.env['product.product'].browse(product_ids).read(['cost_method', 'id'])
        products_dict = dict((product['id'], product) for product in products_rec)
        cost_method_product_ids = list(set(product['id'] for product in products_rec if product['cost_method'] != 'real'))
        histories = []
        if cost_method_product_ids:
            self.env.cr.execute('SELECT DISTINCT ON (product_id, company_id) product_id, company_id, cost FROM product_price_history WHERE product_id in %s AND datetime <= %s ORDER BY product_id, company_id, datetime DESC', (tuple(cost_method_product_ids), date))
            histories = self.env.cr.dictfetchall()
        histories_dict = {}
        for history in histories:
            histories_dict[(history['product_id'], history['company_id'])] = history['cost']
        for line in res:
            inv_value = 0.0
            lines = group_lines.get(str(line.get('__domain', domain)))
            for line_id in lines:
                line_rec = lines_dict[line_id.id]
                product = products_dict[line_rec['product_id']]
                line['unit'] = self.env['product.product'].browse(line_rec['product_id']).uom_id.name
                if product['cost_method'] == 'real':
                    price = line_rec['price_unit_on_quant']
                else:
                    price = histories_dict.get((product['id'], line_rec['company_id']), 0.0)
                inv_value += price * line_rec['quantity']
            line['inventory_value'] = inv_value
        # print res['product_id']
        # print res['inventory_value']
        # print res['product_id']
        #print res
        return res

    @api.multi
    def get_last_balance(self, date_from, product_id, location_id):
        # print 'get_last_balance'
        print (product_id)
        # print self.id
        product_id = self.env['product.product'].browse(product_id)
        # date_from -= 1
        last_date = strToDate(date_from) + relativedelta(days=-1)


        if location_id:
            location_id = self.env['stock.location'].browse(location_id[0])
            res = product_id._compute_quantities_dict_by_location(location_id,None, False, False, False, str(last_date))
        else:
            res = product_id._compute_quantities_dict(None, False, False, False, str(last_date))

        # print "_compute_quantities"
        # print "RES-GET-LAST-Balance"
        # print res

        for product in self:
            # print "----111111-"
            qty_available = res[product_id.id]['qty_available']
            # product.incoming_qty = res[product.id]['incoming_qty']
            # product.outgoing_qty = res[product.id]['outgoing_qty']
            # product.virtual_available = res[product.id]['virtual_available']

        result = {
            'reference': 'ยอดยกมา',
            'no_ref': '',
            'date': (strToDate(date_from) + relativedelta(days=-1)).strftime("%d/%m/%Y"),
            'qty': qty_available,
            'remark': '',
        }
        print
        result
        return result

    @api.multi
    def get_stock_move_by_product_by_date(self, date_from, date_to, product_id,location_id=False):
        move_line_ids = {}
        if product_id:
            # locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            product = self.env['product.product'].browse(product_id)
            # print product.name
            move_line_s = {}
            move_in = False
            move_out = False
            ################ move type ########
            # 1- purchase
            # 2- sale
            # 3- production-out (use matterial)
            # 4- return-supplier(return to supplier)
            # 5- return-customer(return from customer)
            # 6- set (ยอดยกมาก)
            # 7- production-in (transfer from production to stock)
            # 8- inventory-lost(ของเสีย ของหาย)
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


            if location_id:
                # print "location_id" + str(location_id)
                move_ids = self.env['stock.move'].search(
                    ['|',('location_id', '=', location_id[0]),('location_dest_id', '=', location_id[0]),
                     ('product_id', '=', product_id), ('date', '>=', date_from), ('date', '<=', date_to),
                     ('state', '=', 'done'), ('company_id', '=', self.env.user.company_id.id)], order='date, id asc')
            else:
                # print "NO LO"
                move_ids = self.env['stock.move'].search(
                    [('product_id', '=', product_id), ('date', '>=', date_from), ('date', '<=', date_to),
                     ('state', '=', 'done'), ('company_id', '=', self.env.user.company_id.id)], order='date asc')



            # move_ids = self.env['stock.move'].search(
            #     [('product_id', '=', product_id), ('date', '>=', date_from), ('date', '<=', date_to),
            #      ('state', '=', 'done')], order='date asc')

            # print "----------------"
            # print move_ids
            # print "----------------"
            if move_ids:
                for move in move_ids:
                    # print "************"
                    # print move.name
                    # print move.date
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
                            'price': move.price_unit,
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
                            'sum_use': move_out and qty,
                            'sum_add': move_in and qty,
                            'no_ref': ref,
                            'move_id': move.id,
                        }

                        # print move_line_s[i]
                        # print "----------------"

        move_line_ids = [value for key, value in move_line_s.items()]
        #print "Get_Stock_MOVE_by Prduct by Date in Product-Product"
        #print move_line_s
        # print "xxxxxxxxxxxxx"
        # print move_line_ids
        # for i in range(0,len(move_line_ids),1):
        #     print move[i]
        # print "-------------"
        return move_line_ids

# class product_template(models.Model):
#     _inherit = 'product.template'
#
#     ########### function to simple stock move report #############
#     @api.multi
#     def get_stock_move(self):
#
#         locale.setlocale(locale.LC_ALL, 'en_US.utf8')
#         for product in self:
#             move_line_s = {}
#             move_in = False
#             move_out = False
#             balance = 0
#             remark = ""
#             i = 0
#             product_id = self.env['product.product'].search([('name', '=', product.name)], limit=1)
#             move_ids = self.env['stock.move'].search([('product_id', '=', product_id.id)])
#
#             #print move_ids
#             if move_ids:
#                 for move in move_ids:
#
#                     remark = ""
#                     # define reference number
#                     if move.picking_id:
#                         reference = move.picking_id.name
#                         if move.picking_id.note:
#                             remark = move.picking_id.note
#                     elif move.origin:
#                         reference = move.origin
#                     else:
#                         reference = move.name
#
#                     # define date
#                     if move.create_date:
#                         date = strToDate(move.create_date).strftime("%d/%m/%Y")
#                     else:
#                         date = False
#
#                     # define qty
#                     if move.product_uom_qty:
#                         if product.uom_id.id == move.product_uom.id:
#                             qty = move.product_uom_qty
#                         else:
#                             if move.product_uom.uom_type == 'reference':
#                                 if product.uom_id.uom_type == 'bigger':
#                                     qty = move.product_uom_qty / product.uom_id.factor
#                                 else:
#                                     qty = move.product_uom_qty * product.uom_id.factor
#
#                             elif move.product_uom.uom_type == 'bigger':
#                                 if product.uom_id.uom_type == 'reference':
#                                     qty = move.product_uom_qty * move.product_uom.factor
#                                 else:
#                                     qty = move.product_uom_qty * move.product_uom.factor * product.uom_id.factor
#                             else:
#                                 if product.uom_id.uom_type == 'reference':
#                                     qty = move.product_uom_qty * move.product_uom.factor
#                                 else:
#                                     qty = move.product_uom_qty / move.product_uom.factor / product.uom_id.factor
#
#                     else:
#                         qty = 0
#
#                     # define move_in and move_out
#                     if move.picking_type_id:
#                         if move.picking_type_id.code == 'incoming':
#                             move_in = True
#                             move_out = False
#                         elif move.picking_type_id.code == 'outgoing':
#                             move_in = False
#                             move_out = True
#                         # it is internal move
#                         else:
#                             if move.location_id and move.location_dest_id:
#                                 if move.location_id.usage == 'internal':
#                                     if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
#                                         move_in = False
#                                         move_out = True
#                                     else:
#                                         move_in = False
#                                         move_out = False
#                                 elif move.location_id.usage == 'inventory':
#                                     if move.location_dest_id.usage == 'internal':
#                                         move_in = True
#                                         move_out = False
#                                     else:
#                                         move_in = False
#                                         move_out = False
#                                 elif move.location_id.usage == 'production':
#                                     if move.location_dest_id.usage == 'internal':
#                                         move_in = True
#                                         move_out = False
#                                     # production to scrapt
#                                     elif move.location_dest_id.usage == 'inventory':
#                                         move_in = False
#                                         move_out = True
#                                     else:
#                                         move_in = False
#                                         move_out = False
#                                 elif move.location_id.usage == 'supplier':
#                                     if move.location_dest_id.usage == 'internal':
#                                         move_in = True
#                                         move_out = False
#                                     else:
#                                         move_in = False
#                                         move_out = False
#
#                                 # case claim and return
#                                 elif move.location_id.usage == 'customer':
#                                     if move.location_dest_id.usage == 'internal':
#                                         move_in = True
#                                         move_out = False
#                                     else:
#                                         move_in = False
#                                         move_out = False
#                                 else:
#                                     move_in = False
#                                     move_out = False
#                             else:
#                                 move_in = False
#                                 move_out = False
#
#                     # if no picking type
#                     else:
#                         if move.location_id and move.location_dest_id:
#                             if move.location_id.usage == 'internal':
#                                 if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
#                                     move_in = False
#                                     move_out = True
#                                 else:
#                                     move_in = False
#                                     move_out = False
#                             elif move.location_id.usage == 'inventory':
#                                 if move.location_dest_id.usage == 'internal':
#                                     move_in = True
#                                     move_out = False
#                                 else:
#                                     move_in = False
#                                     move_out = False
#                             elif move.location_id.usage == 'production':
#                                 if move.location_dest_id.usage == 'internal':
#                                     move_in = True
#                                     move_out = False
#                                 # production to scrapt
#                                 elif move.location_dest_id.usage == 'inventory':
#                                     move_in = False
#                                     move_out = True
#                                 else:
#                                     move_in = False
#                                     move_out = False
#                             elif move.location_id.usage == 'supplier':
#                                 if move.location_dest_id.usage == 'internal':
#                                     move_in = True
#                                     move_out = False
#                                 else:
#                                     move_in = False
#                                     move_out = False
#
#                             # case claim and return
#                             elif move.location_id.usage == 'customer':
#                                 if move.location_dest_id.usage == 'internal':
#                                     move_in = True
#                                     move_out = False
#                                 else:
#                                     move_in = False
#                                     move_out = False
#                             else:
#                                 move_in = False
#                                 move_out = False
#
#                     # only move_in or move_out action will be considered
#                     if move_in or move_out:
#
#                         if move_in:
#                             balance += qty
#                         else:
#                             balance -= qty
#                         i += 1
#
#                         move_line_s[i] = {
#                             'reference': reference,
#                             'date': date,
#                             'qty': locale.format("%.2f", qty, grouping=True),
#                             'move_in': move_in,
#                             'move_out': move_out,
#                             'balance': locale.format("%.2f", balance, grouping=True),
#                             'remark': remark
#                         }
#             move_line_s = [value for key, value in move_line_s.items()]
#
#             #print "Get_Stock_MOVE_SIMPLE"
#             #print move_line_s
#             return move_line_s


########## stock report without cost################333
class report_product_stock_simple_report(models.AbstractModel):
    _name = 'report.stock_extended.product_report_id'

    @api.multi
    def get_stock_move_product(self, date_from, date_to, location_ids, category_id, product_id, company_id):
        domain = [('date', '>=', date_from),
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
