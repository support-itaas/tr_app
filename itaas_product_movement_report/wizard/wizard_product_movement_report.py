# -*- coding: utf-8 -*-
# Copyright (C) 2021-today ITAAS (Dev K.IT)

import base64
import xlwt
from io import BytesIO
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import misc
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz
from datetime import datetime, timedelta, date, time

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class WizardProductMovementReport(models.TransientModel):
    _name = 'wizard.product.movement.report'
    _description = 'Wizard Product Movement Report'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id = fields.Many2one('stock.location', string='Location')
    category_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    is_cost = fields.Boolean('Show Cost')
    is_purchase = fields.Boolean('Purchase')
    is_show_lot_initial = fields.Boolean(string='Show LOT Initial')
    customer_id = fields.Many2one('res.partner', string='Customer')
    account_id = fields.Many2one('account.account','Account')
    code_from = fields.Char(string='Product Code From')
    code_to = fields.Char(string='Product Code To')

    # @api.model
    # def default_get(self, fields):
    #     res = super(WizardProductMovementReport, self).default_get(fields)
    #     curr_date = datetime.now()
    #     from_date = datetime(curr_date.year, 1, 1).date() or False
    #     to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
    #     res.update({'date_from': str(from_date), 'date_to': str(to_date)})
    #
    #     return res

    def get_stock_move(self):
        domain = [('state', '=', 'done'), ('state', '=', 'done')]
        if self.product_id:
            product_ids = self.product_id.ids
        else:
            domain_product = [('type', '=', 'product')]
            if self.category_id:
                domain_product += [('categ_id', '=', self.category_id.id)]
            if self.customer_id:
                domain_product += [('customer_id', '=', self.customer_id.id)]
            if self.account_id:
                domain_product += [('categ_id.property_stock_valuation_account_id', '=', self.account_id.id)]
            product_ids = self.env['product.product'].search(domain_product).ids
        domain += [('product_id', 'in', product_ids)]

        if self.location_id and self.location_id.usage == 'internal':
            domain += ['|', ('location_id', 'child_of', self.location_id.id),
                       ('location_dest_id', 'child_of', self.location_id.id)]
        print ('domain : ', domain)

        stock_move = self.env['stock.move'].search(domain)
        print('stock_move:',len(stock_move))
        return stock_move

    def get_inventory_before(self, date, product_id):
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        move_in = self.env['stock.move.line'].search([('move_id.state', '=', 'done'),
                                                      ('product_id', '=', product_id.id),
                                                      ('location_dest_id', 'in', locations.ids),
                                                      ('date', '<', date)
                                                      ])
        print('before move_in: ', move_in)
        move_out = self.env['stock.move.line'].search([('move_id.state', '=', 'done'),
                                                       ('product_id', '=', product_id.id),
                                                       ('location_id', 'in', locations.ids),
                                                       ('date', '<', date)
                                                       ])
        print('before move_out: ', move_out)
        move_in_qty = sum(move_in.mapped('qty_done'))
        move_out_qty = sum(move_out.mapped('qty_done'))
        print('move_in_qty: ', move_in_qty)
        print('move_out_qty: ', move_out_qty)

        return move_in_qty - move_out_qty

    def get_move_inventory_after(self, date_from, date_to, product_id, location_id):
        locations = self.env['stock.location'].search([('id', 'child_of', [location_id.id])])
        print('get_inventory_after ',date_from, date_to, product_id, locations)
        move_ids = self.env['stock.move.line'].search([('move_id.state', '=', 'done'),
                                                       ('product_id', '=', product_id.id),
                                                       '|',('location_dest_id', 'in', locations.ids),('location_id', 'in', locations.ids),
                                                       ('date', '>=', date_from),('date', '<=', date_to)], order='date')
        print('move_ids ',move_ids)

        return move_ids

    def get_inventory_after(self, date_from, date_to, product_id, location_id):
        print('get_inventory_afterL')
        print('date_from',date_from)
        print('date_to',date_to)
        print('product_id',product_id)
        print('location_id',location_id)
        move_ids = self.get_move_inventory_after(date_from, date_to, product_id, location_id)
        move_val = []
        for move in move_ids:
            remark = move.picking_id.note or ''
            type = ''
            if location_id.id == move.location_dest_id.id:
                move_in = True
                move_out = False
                if move.location_id.usage == 'production':
                    type = 'production-in'
                elif move.location_id.usage == 'supplier':
                    type = 'return-supplier'
                elif move.location_id.usage == 'customer':
                    type = 'return-sale'
                elif move.location_id.usage == 'inventory':
                    type = 'inventory-lost'
                elif move.location_id.usage == 'internal':
                    type = 'set'
            else:
                move_in = False
                move_out = True
                if move.location_dest_id.usage == 'production':
                    type = 'production-out'
                elif move.location_dest_id.usage == 'supplier':
                    type = 'purchase'
                elif move.location_dest_id.usage == 'customer':
                    type = 'sale'
                elif move.location_id.usage == 'inventory':
                    type = 'inventory-lost'
                elif move.location_id.usage == 'internal':
                    type = 'set'

            ref = ''
            ref = move.move_id.origin
            # if move.picking_id and move.picking_id.is_reverse:
            #     ref = move.picking_id.invoice_reference.number
            #     remark = move.picking_id.invoice_reference.name
            # elif move.picking_id and move.picking_id.sale_id and move.picking_id.sale_id.invoice_ids:
            #     for invoice in move.picking_id.sale_id.invoice_ids:
            #         ref = invoice.number
            # elif move.picking_id and move.picking_id.purchase_id and move.picking_id.purchase_id.invoice_ids:
            #     for invoice in move.picking_id.purchase_id.invoice_ids:
            #         ref = invoice.reference
            # else:
            #     ref = move.origin

            str2dt = fields.Datetime.from_string
            date = str2dt(move.date).strftime("%d/%m/%Y")
            lot = ''
            # if move.lot_ids:
            #     lot = ', '.join(move.lot_ids.mapped('name'))

            print('date ',date)
            print('move ',move)
            val = {
                'move_in': move_in,
                'move_out': move_out,
                'type': type,
                'reference': move.picking_id.name or move.reference,
                'picking_number': move.picking_id.picking_number,
                'invoice_number': move.picking_id.invoice_number,
                'remark': remark,
                'qty': move.qty_done,
                'uom': move.product_id.uom_id.name,
                'no_ref': ref,
                'price_unit': move.move_id.price_unit,
                'price_total': move.move_id.price_unit * move.qty_done,
                'lot': move.lot_id,
                'date': date,
            }
            move_val.append(val)

        return move_val

    def convert_utc_to_usertz(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = tz.localize(date_time).astimezone(user_tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

    def print_report_pdf(self, data):
        print('print_pdf_report : ')
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'location_id', 'category_id', 'product_id','company_id','is_cost', 'customer_id'])[0]
        envref = self.env.ref('itaas_product_movement_report.product_movement_report')
        print('envref : ',envref)
        return envref.report_action(self, data=data,config=False)

    def print_purchase_excel(self):
        [data] = self.read()
        datas = {'form': data}
        str2d = fields.Date.from_string
        date_from = str2d(self.date_from)
        date_to = str2d(self.date_to)
        # date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        # date_to_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        report_file = "รายงานซื้อสินค้า" + str(date_from.strftime("%d/%m/%Y")) + "-" + str(
            date_to.strftime("%d/%m/%Y"))
        self.env.ref('itaas_product_movement_report.purchase_report_xls').report_file = report_file
        return self.env.ref('itaas_product_movement_report.purchase_report_xls').report_action(self, data=datas, config=False)


    def print_report_excel(self):
        [data] = self.read()
        datas = {'form': data}

        str2d = fields.Date.from_string
        date_from = str2d(self.date_from)
        date_to = str2d(self.date_to)
        # date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        # date_to_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        report_file = "รายงานเคลื่อนไหวสินค้า" + str(date_from.strftime("%d/%m/%Y")) + "-" + str(date_to.strftime("%d/%m/%Y"))
        self.env.ref('itaas_product_movement_report.pm_report_xls').report_file = report_file
        return self.env.ref('itaas_product_movement_report.pm_report_xls').report_action(self, data=datas, config=False)

    def fix_fifo(self):
        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(self.date_from)
        date_to = str2d(self.date_to)
        # date_time_from = self.convert_usertz_to_utc(datetime.combine(str2dt(self.date_from), time.min))
        # date_time_to = self.convert_usertz_to_utc(datetime.combine(str2dt(self.date_to), time.max))
        location_ids = self._get_location()
        product_ids = self._get_stock_move_product(location_ids)
        # print('product_ids for Excel:', product_ids)
        # print (xxx)
        for product in product_ids:

            last_move_in_ids = self.last_5_get_stock_account_move_line_by_product(product, date_from)
            last_balance_qty = self._get_stock_move_initial_qty_by_product(product.id, date_from)
            last_balance_cost = self._get_stock_move_initial_qty_by_product_cost(product.id, date_from)
            move_after = self.get_stock_account_move_line_by_product(product, date_from, date_to)
            stock_in_ids = []

            #get 5 last in



            print ('last_move_in_ids',last_move_in_ids)
            if last_balance_qty:
                pending_balance = last_balance_qty
                count = 0
                for move_in in last_move_in_ids:
                    count += 1
                    if pending_balance < move_in['qty']:
                        print ('Pending < move-qty')
                        if count == 1:
                            print ('Count =1')
                            intial_price = last_balance_cost / last_balance_qty
                            val_in = {
                                'id': count,
                                'qty': last_balance_qty,
                                'unit_cost': round(intial_price, 2),
                                'last_balance_cost': last_balance_cost,
                            }
                            stock_in_ids.append(val_in)
                            print('stock_in_ids', stock_in_ids)

                        else:
                            print('Count > 1')
                            intial_price = move_in['price_total'] / move_in['qty']
                            cost = intial_price * pending_balance
                            # intial_price = last_balance_cost / pending_balance
                            val_in = {
                                'id':count,
                                'qty': pending_balance,
                                'unit_cost': round(intial_price, 2),
                                'last_balance_cost': cost,
                            }
                            stock_in_ids.append(val_in)
                            print('stock_in_ids', stock_in_ids)
                        break
                    else:
                        #update
                        print('Pending > move-qty')
                        pending_balance -= abs(move_in['qty'])
                        unit_price = move_in['price_total'] / move_in['qty']
                        cost = move_in['price_total']
                        val_in = {
                            'id': count,
                            'qty':move_in['qty'],
                            'unit_cost': round(unit_price, 2),
                            'last_balance_cost': cost,
                        }
                        stock_in_ids.append(val_in)
                        print ('stock_in_ids',stock_in_ids)

            # print('before sort', stock_in_ids)
            # stock_in_ids.sort(reverse=True)
            stock_in_ids = sorted(stock_in_ids, key=lambda d: d['id'],reverse=True)
            # print ('after sort',stock_in_ids)
            for move in move_after:

                #in
                if move['move_in'] and not move['move_out']:
                    print('1---> THIS IS STOCK IN')
                    if move['qty']:
                        price_unit = move['price_total'] / float(move['qty'])

                        val_in = {
                            'qty': float(move['qty']),
                            'unit_cost': round(price_unit, 2),
                            'last_balance_cost': move['price_total'],
                            'date':move['date'],
                        }
                        stock_in_ids.append(val_in)
                        print('stock_in_ids',stock_in_ids)
                    else:
                        if stock_in_ids:
                            # print ('IN with NO QTy')
                            # print ('stock_in_ids',stock_in_ids)
                            #no qty but has some debit, credit, mean to landed cost
                            #??? if already move then how landed cost cal effect to this
                            # print ('len(stock_in_ids)-1',len(stock_in_ids)-1)
                            # print ('xxx',stock_in_ids[len(stock_in_ids)-1]['unit_cost'])
                            stock_in_ids[len(stock_in_ids)-1]['last_balance_cost'] += move['price_total']
                            stock_in_ids[len(stock_in_ids)-1]['unit_cost'] = round(stock_in_ids[len(stock_in_ids)-1]['last_balance_cost'] / stock_in_ids[len(stock_in_ids)-1]['qty'],2)

                #out
                elif not move['move_in'] and move['move_out']:
                    print('2---> THIS IS STOCK OUT',move['qty'])
                    pending_qty = abs(move['qty'])
                    stock_in_remove_ids = []
                    max_stock_in = len(stock_in_ids)
                    count_stock_in = 0
                    move_id = move['aml_id'].move_id
                    if move_id.date == '2022-02-21':
                        break
                    # print ('MOVE Name',move_id.name)
                    # print ('stock_in_ids',stock_in_ids)
                    final_debit_credit_amount = 0

                    for stock_in_id in stock_in_ids:
                        count_stock_in +=1
                        # print ('stock_in_id',stock_in_id)
                        # print ('move qty',move['qty'])
                        # print (float_is_zero(abs(move['qty']), precision_rounding=2))
                        #if out and not qty, mean landed cost work it self
                        if float_compare(move['qty'], 0, precision_digits=2) == 0:
                        # if float_is_zero(abs(move['qty']), precision_rounding=2):
                            print ('STEP-01')
                            stock_in_id['last_balance_cost'] -= abs(move['price_total'])
                            if stock_in_id['qty']:
                                stock_in_id['unit_cost'] = round(stock_in_id['last_balance_cost'] / stock_in_id['qty'], 2)
                            else:
                                stock_in_id['last_balance_cost'] = 0.00
                                stock_in_id['unit_cost'] = 0.00
                            #break due to landed cost nothing to do other code exept reduce value
                            break

                        if float_compare(pending_qty, 0, precision_digits=2) == 0:
                            print('STEP-02')
                            #break due to pending is zero
                            # stock_in_id['last_balance_cost'] -= abs(move['price_total'])
                            # stock_in_id['unit_cost'] = round(stock_in_id['last_balance_cost'] / stock_in_id['qty'], 2)
                            break

                        if stock_in_id['qty'] > pending_qty:
                            print ('stock_in_id[qty] more than pending_qty:',pending_qty)
                            stock_in_id['qty'] -= pending_qty
                            debit_credit_amount = pending_qty * stock_in_id['unit_cost']
                            stock_in_id['last_balance_cost'] -= abs(debit_credit_amount)
                            final_debit_credit_amount += debit_credit_amount

                            if float_compare(abs(final_debit_credit_amount), abs(move['price_total']), precision_digits=2) != 0:
                                print ('DIFF GL Value then update')


                                # print ('JE Name',move_id.name)
                                move_id.button_cancel()
                                debit_line_id = move_id.line_ids.filtered(lambda x: x.debit)
                                if not debit_line_id:
                                    debit_line_id = move_id.line_ids.filtered(lambda x: x.account_id != self.account_id)

                                credit_line_id = move_id.line_ids.filtered(lambda x: x.credit)
                                if not credit_line_id:
                                    credit_line_id = move_id.line_ids.filtered(lambda x: x.account_id == self.account_id)
                                # print('OLD Value', debit_line_id.debit)
                                # print('new Value', debit_credit_amount)
                                # print ('debit_line_id',debit_line_id)
                                # print('credit_line_id', credit_line_id)


                                if len(debit_line_id) == 1 and len(credit_line_id) == 1 and final_debit_credit_amount > 0:
                                    debit_line_id.sudo().with_context(check_move_validity=False).update({'debit':final_debit_credit_amount})
                                    credit_line_id.sudo().with_context(check_move_validity=False).update({'credit':final_debit_credit_amount})
                                else:
                                    print ('MULTIPLE LINE OF STOCK IGNORE---First')

                                move_id.post()
                                move_id.sudo().stock_move_id.update({'value':final_debit_credit_amount * (-1)})
                                move_id.sudo().stock_move_id.update({'price_unit': (final_debit_credit_amount/abs(move_id.sudo().stock_move_id.quantity_done)) * (-1)})

                            stock_in_id['unit_cost'] = round(stock_in_id['last_balance_cost'] / stock_in_id['qty'], 2)
                            pending_qty = 0.00

                            print('new stock in', stock_in_id)

                        #current-in stock qty < move_qty
                        else:
                            print('stock_in_id[qty] less than or equal pending_qty:', pending_qty)
                            pending_qty -= stock_in_id['qty']
                            stock_in_id['qty'] = 0
                            debit_credit_amount = stock_in_id['last_balance_cost']
                            stock_in_id['last_balance_cost'] = 0
                            stock_in_id['unit_cost'] = 0
                            final_debit_credit_amount += debit_credit_amount

                            # stock_in_id['last_balance_cost'] -= abs(debit_credit_amount)

                            if float_compare(abs(final_debit_credit_amount), abs(move['price_total']),precision_digits=2) != 0 and float_is_zero(pending_qty,precision_digits=2):
                                print('DIFF GL Value then update')

                                move_id.button_cancel()
                                debit_line_id = move_id.line_ids.filtered(lambda x: x.debit)
                                if not debit_line_id:
                                    debit_line_id = move_id.line_ids.filtered(lambda x: x.account_id != self.account_id)

                                credit_line_id = move_id.line_ids.filtered(lambda x: x.credit)
                                if not credit_line_id:
                                    credit_line_id = move_id.line_ids.filtered(
                                        lambda x: x.account_id == self.account_id)
                                # print('OLD Value', debit_line_id.debit)
                                # print('new Value', debit_credit_amount)

                                if len(debit_line_id) == 1 and len(credit_line_id) == 1 and final_debit_credit_amount > 0:
                                    debit_line_id.sudo().with_context(check_move_validity=False).update(
                                        {'debit': final_debit_credit_amount})
                                    credit_line_id.sudo().with_context(check_move_validity=False).update(
                                        {'credit': final_debit_credit_amount})
                                else:
                                    print('MULTIPLE LINE OF STOCK IGNORE---First')

                                move_id.post()
                                move_id.sudo().stock_move_id.update({'value': final_debit_credit_amount * (-1)})
                                move_id.sudo().stock_move_id.update({'price_unit': (final_debit_credit_amount / abs(
                                    move_id.sudo().stock_move_id.quantity_done)) * (-1)})


                            print('new stock in', stock_in_id)

                            # stock_in_remove_ids.append(stock_in_id)


                        # print ('count_stock_in',count_stock_in)
                        # print('max_stock_in', max_stock_in)
                        # print ('pending_qty',pending_qty)
                        if count_stock_in == max_stock_in and pending_qty != 0:
                            print ('Update record')
                            val = {
                                'product_id':product.id,
                                'lot': move_id.name,
                            }
                            self.env['stock.record.yearly'].create(val)

                            # print('STOCK OUT OVER STOCK IN')


                    #final loop and remove zero one
                    for stock_in_id in stock_in_ids:
                        if float_compare(stock_in_id['qty'], 0, precision_digits=2) == 0:
                        # if float_is_zero(stock_in_id['qty'],precision_digits=2):
                            stock_in_ids.remove(stock_in_id)
                    # stock_in_ids.remove({'qty': 0, 'unit_cost': 0, 'last_balance_cost': 0})
                    print ('new stock in ids',stock_in_ids)
                    # print ('2')

                #movein and mout out
                else:
                    print ('NO IDEA')




        # if self.location_id:
        #     warehouse = False
        # else:
        #     warehouse = self.warehouse_id



    def _get_product(self):
        if self.product_id:
            product_ids = self.product_id
        else:
            domain_product = [('type', '=', 'product')]
            if self.category_id:
                domain_product += [('categ_id', '=', self.category_id.id)]
            if self.customer_id:
                domain_product += [('customer_id', '=', self.customer_id.id)]
            if self.account_id:
                domain_product += [('categ_id.property_stock_valuation_account_id', '=', self.account_id.id)]
            if self.code_from and self.code_to:
                domain_product += [('default_code', '>=', self.code_from),('default_code', '<=', self.code_to)]
            product_ids = self.env['product.product'].search(domain_product)
            # print ('Product1111',product_ids)

        return product_ids

    def _get_location(self):
        if self.location_id and self.location_id.usage == 'internal':
            location_ids = self.env['stock.location'].search([('id', '=', self.location_id.id)])
        elif self.location_id and self.location_id.usage != 'internal':
            location_ids = self.env['stock.location'].search([('location_id', '=', self.location_id.id)])
        elif self.warehouse_id:
            location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        else:
            location_view = self.env['stock.location'].sudo().search([('name', '=', self.warehouse_id.code)])
            # print ('Loc',location_view)
            location_ids = self.env['stock.location'].sudo().search([('location_id', '=', location_view.id)])
            # print ('location_ids',location_ids)

        return location_ids

    def _get_stock_move_product(self, locations):
        product_ids = self._get_product()
        # print ('LOcations',locations)
        self._cr.execute(
            """
            SELECT move.product_id
            FROM stock_move move
            WHERE(move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done'
                and move.company_id = %s
                and move.product_id in %s
                and CAST(move.date AS date) <= %s
            GROUP BY move.product_id
        """,
            (
                tuple(locations.ids),
                tuple(locations.ids),
                self.company_id.id,
                tuple(product_ids.ids),
                self.date_to,
            ),
        )
        stock_card_results = [x[0] for x in self.env.cr.fetchall()]
        # print('stock_card_results : ', stock_card_results)
        # return self.env['product.product'].sudo().browse(31238).filtered(lambda x: x.type in ['product'])
        return self.env['product.product'].sudo().browse(stock_card_results).filtered(lambda x: x.type in ['product'])

    def _get_stock_move_results(self, date_from, date_to, warehouse, locations, product_ids):
        # print('_get_stock_move_results ', date_from, date_to, warehouse, locations, product_ids)
        if warehouse:
            print ('WArehouse')
            self._cr.execute("""
                        SELECT move.date, move.product_id, move_line.qty_done,
                            move.product_uom, move.reference, move_line.lot_id,
                            move_line.location_id, move_line.location_dest_id, move.price_unit,
                            move.value, move.id as move_id, move.name as picking_name,
                            move.origin,
                            case when move_line.location_dest_id in %s
                                then move_line.qty_done end as product_in,
                            case when move_line.location_id in %s
                                then move_line.qty_done end as product_out,
                            case when move.date < %s 
                                then True else False end as is_initial
                        FROM stock_move_line move_line
                        JOIN stock_move move ON move.id = move_line.move_id
                        
                        JOIN stock_location location ON location.id = move_line.location_id
                        JOIN stock_location location_dest ON location_dest.id = move_line.location_dest_id
                        WHERE (move_line.location_id in %s or move_line.location_dest_id in %s)
                            and move.state = 'done' and move.product_id in %s
                            and CAST(move.date AS date) <= %s
                        ORDER BY move.date, move.reference
                    """, (
                tuple(locations.ids), tuple(locations.ids), date_from,
                tuple(locations.ids), tuple(locations.ids),
                tuple(product_ids.ids), date_to))
        else:
            print('ELSE')
            print('locations:',locations)
            self._cr.execute("""
                SELECT move.date, move.product_id, move_line.qty_done,
                    move.product_uom, move.reference, move_line.lot_id,
                    move_line.location_id, move_line.location_dest_id, move.price_unit,
                    move.value, move.id as move_id,
                    move.origin,
                    case when move_line.location_dest_id in %s
                        then move_line.qty_done end as product_in,
                    case when move_line.location_id in %s
                        then move_line.qty_done end as product_out,
                    case when move.date < %s 
                        then True else False end as is_initial
                FROM stock_move_line move_line
                JOIN stock_move move ON move.id = move_line.move_id
                WHERE (move_line.location_id in %s or move_line.location_dest_id in %s)
                    and move.state = 'done' and move.product_id in %s
                    and CAST(move.date AS date) <= %s
                ORDER BY move.date, move.reference
                                """, (
                tuple(locations.ids), tuple(locations.ids), date_from,
                tuple(locations.ids), tuple(locations.ids),
                tuple(product_ids.ids), date_to))
        print('date_from:',date_from)
        print('date_to:',date_to)
        stock_card_results = self._cr.dictfetchall()
        # print('stock_card_results_ssss--1:', stock_card_results)
        # print('stock_card_results_ssss:',len(stock_card_results))
        for move in stock_card_results:
            # print('** move ', move)
            # print('** move_id', move['move_id'])
            # print('** product_in ', move['product_in'])
            # print('** product_out ', move['product_out'])
            # print('** reference ', move['reference'])
            # print('** location_id ', move['location_id'])
            # print('** location_dest_id ', move['location_dest_id'])
            stock_move_id = self.env['stock.move'].browse(move['move_id'])
            if not stock_move_id.sudo().account_move_ids:
                move['move_in'] = False
                move['move_out'] = False
                move['product_in'] = False
                move['product_out'] = False
            elif move['product_in'] and move['product_out']:
                move['move_in'] = True
                move['move_out'] = True
            elif move['product_in']:
                move['move_in'] = True
                move['move_out'] = False
            else:
                move['move_in'] = False
                move['move_out'] = True

        return stock_card_results

    def _get_stock_move_results_by_product(self, product, stock_move_results):
        stock_move_results_by_product = list(filter(lambda x: x['product_id'] == product.id, stock_move_results))
        print('len stock_move_results_by_product', len(stock_move_results_by_product))
        return stock_move_results_by_product

    def _get_stock_move_initial_qty_by_product_by_location(self, product_id,to_date, location_id):

        product_product_id = self.env['product.product'].browse(product_id)

        stock_quant_ids = self.env['stock.quant'].search(
            [('product_id', '=', product_id), ('location_id', '=', location_id)])
        stock_qty = sum(stock_quant_id.quantity for stock_quant_id in stock_quant_ids)
        # print ('ORIGINAL VALUE by LOCATION',stock_qty)

        domain_move_in_loc = [('location_dest_id', '=', location_id)]
        domain_move_out_loc = [('location_id', '=', location_id)]
        domain_move_in = [('product_id', 'in', product_product_id.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', product_product_id.ids)] + domain_move_out_loc
        domain_move_in_done = [('state', '=', 'done'), ('date', '>', str(to_date))] + domain_move_in
        domain_move_out_done = [('state', '=', 'done'), ('date', '>', str(to_date))] + domain_move_out

        move_in_qty = abs(sum(move.quantity_done for move in self.env['stock.move'].search(domain_move_in_done)))
        move_out_qty = abs(sum(move.quantity_done for move in self.env['stock.move'].search(domain_move_out_done)))
        stock_qty = stock_qty + move_out_qty - move_in_qty

        # rec = self.env['stock.record.yearly'].search([('product_id','=',product_id),('location','=',location_id)],limit=1,order='date desc')
        #
        # if rec:
        #     return rec.qty,rec.value
        print ('stock_qty',stock_qty)
        return stock_qty

        # account_id = product_product_id.categ_id.property_stock_valuation_account_id.id
        # if not account_id:
        #     return 0.00
        # params = (product_id, account_id, to_date,)
        # aml_query = """SELECT sum(aml.quantity) as quantity,sum(aml.balance) as value
        #                                                                                                FROM account_move_line AS aml
        #                                                                                                WHERE aml.product_id = %s and aml.account_id = %s and aml.date < %s
        #                                                                                                 GROUP BY aml.product_id
        #                                                                                                 """
        #
        # self.env.cr.execute(aml_query, params)
        # res = self.env.cr.fetchall()
        #
        # if res:
        #     return res[0][0]
        # else:
        #     return 0.00


    def _get_stock_move_initial_qty_by_product_cost(self, product_id, to_date):
        product_product_id = self.env['product.product'].browse(product_id)
        account_id = product_product_id.categ_id.property_stock_valuation_account_id.id
        params = (product_id, account_id, to_date,)

        #sum(aml.debit) - sum(aml.credit)
        aml_query = """SELECT sum(aml.quantity) as quantity,sum(aml.debit) - sum(aml.credit) as value
                                                                                               FROM account_move_line AS aml
                                                                                               WHERE aml.product_id = %s and aml.account_id = %s and aml.date < %s
                                                                                                GROUP BY aml.product_id
                                                                                                """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES',res)
        if res:
            return res[0][1]
        else:
            return 0.00


        # stock_move_initial_results_by_product = list(filter(lambda x: x['is_initial'] == True, stock_move_results))
        # # print('stock_move_initial_results_by_product:',stock_move_initial_results_by_product)
        # # print('stock_move_initial_results_by_product:',len(stock_move_initial_results_by_product))
        # sum_cost_in = 0
        # sum_cost_out = 0
        # move_done_ids = []
        # # check_ref = []
        # # for move in stock_move_initial_results_by_product:
        # #     amount = 0
        # #     location_id = self.env['stock.location'].browse(move['location_dest_id'])
        # #
        # #     if location_id.usage  in ('supplier','customer','production','inventory'):
        # #         if move['reference'] not in check_ref:
        # #             check_ref.append(move['reference'])
        # #         else:
        # #             continue
        # #         print('location_id:', location_id)
        # #         print('value_out:',move['value'])
        # #         if move['value']:
        # #             #บางครั้งมีการ dif กันของทศนิยม เลยต้องปัดก่อน T22059149 #เคส 1 12/05
        # #             amount = round(move['value'], 2)
        # #         print('amount_OUT:', amount)
        # #         sum_cost_out += amount or 0.00
        # #     else:
        # #         print('location_id:',location_id)
        # #         print('value_in:',move['value'])
        # #         if move['value']:
        # #             #บางครั้งมีการ dif กันของทศนิยม เลยต้องปัดก่อน T22059149 #เคส 1 12/05
        # #             amount = round(move['value'],2)
        # #         print('amount_IN:',amount)
        # #         sum_cost_in += amount or 0.00
        # # print('sum_cost_in:',sum_cost_in)
        # # print('sum_cost_out:',sum_cost_out)
        # sum_in = 0
        # sum_out = 0
        # for move in stock_move_initial_results_by_product:
        #     if move['move_id'] not in move_done_ids:
        #         if move['product_in'] and not move['product_out']:
        #             if move['value']:
        #                 print('value_In',move['value'])
        #                 print('reference_In',move['reference'])
        #                 sum_cost_in += round(move['value'],2) or 0.00
        #         if move['product_out'] and not move['product_in']:
        #             if move['value']:
        #                 print('value_out',move['value'])
        #                 print('reference_out',move['reference'])
        #                 sum_cost_out += round(move['value'],2) or 0.00
        #
        #         move_done_ids.append(move['move_id'])
        #
        #     #
        #     #
        #     #
        #     # sum_cost_in += move['product_in'] or 0.00
        #     # sum_cost_out += move['product_out'] or 0.00
        #
        # print('sum_move_in:', sum_cost_in)
        # print('sum_move_in:', sum_cost_out)
        #
        # return sum_cost_in - abs(sum_cost_out)

    def _get_stock_move_initial_qty_by_product(self, product_id,to_date):
        product_product_id = self.env['product.product'].browse(product_id)
        account_id = product_product_id.categ_id.property_stock_valuation_account_id.id
        if not account_id:
            return 0.00
        params = (product_id, account_id, to_date,)
        aml_query = """SELECT sum(aml.quantity) as quantity,sum(aml.balance) as value
                                                                                                       FROM account_move_line AS aml
                                                                                                       WHERE aml.product_id = %s and aml.account_id = %s and aml.date < %s
                                                                                                        GROUP BY aml.product_id
                                                                                                        """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print('RES', res)
        if res:
            # print ('resss',res[0][0])
            return res[0][0]
        else:
            return 0.00

        # stock_move_initial_results_by_product = list(filter(lambda x: x['is_initial'] == True, stock_move_results))
        # sum_in = 0
        # sum_out = 0
        # for move in stock_move_initial_results_by_product:
        #     move_id = self.env['stock.move'].browse(move['move_id'])
        #     if move['product_in']:
        #         move_in = move_id.product_uom._compute_quantity(move['product_in'], move_id.product_id.uom_id)
        #     else:
        #         move_in = 0.00
        #
        #     if move['product_out']:
        #         move_out = move_id.product_uom._compute_quantity(move['product_out'], move_id.product_id.uom_id)
        #     else:
        #         move_out = 0.00
        #
        #
        #     sum_in += move_in or 0.00
        #     sum_out += move_out or 0.00
        # return sum_in - sum_out

    def get_stock_account_move_line_by_product_by_location(self, product_id, from_date, to_date,location_id):
        # print ('get_stock_account_move_line_by_product')
        move_val = []
        # product_product_id = self.env['product.product'].browse(product_id)
        account_id = product_id.categ_id.property_stock_valuation_account_id.id
        if not account_id:
            return move_val
        # params = (product_id.id, account_id, from_date, to_date,)
        # aml_query = """SELECT aml.quantity, aml.id, aml.debit, aml.credit,aml.date
        #                     FROM account_move_line AS aml
        #                     LEFT JOIN account_move am ON (aml.move_id=am.id)
        #                     LEFT JOIN stock_move sm ON (am.stock_move_id=sm.id)
        #                     WHERE aml.product_id = %s and aml.account_id = %s and aml.date >= %s and aml.date <= %s
        #                     GROUP BY aml.product_id,aml.quantity,aml.debit,aml.credit,aml.id,aml.date
        #                     ORDER BY aml.date
        #                 """
        #
        # self.env.cr.execute(aml_query, params)
        # res = self.env.cr.fetchall()

        params = (product_id.id, location_id, location_id, from_date, to_date,)
        aml_query = """SELECT sm.product_uom_qty, sm.id, sm.date,sm.location_id,sm.location_dest_id,sm.value
                            FROM stock_move AS sm
                            WHERE sm.product_id = %s and (sm.location_id = %s  or sm.location_dest_id = %s) and sm.state = 'done' and sm.date >= %s and sm.date <= %s
                            GROUP BY sm.product_id,sm.product_uom_qty,sm.location_id,sm.location_dest_id,sm.id,sm.value,sm.date
                            ORDER BY sm.date
                        """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        #0-qty
        #1-id
        #2-date
        #3-location
        #4-location_dest_id
        #5-value

        # print ('RES--AML',res)
        # landed_cost_ids =
        if res:
            for aml in res:
                # print ('AML---',aml[0])
                qty = 0.00
                lot = ''
                move_in = False
                move_out = False
                ref = ''
                picking_number = ''
                invoice_txt = ''

                if aml[3] == location_id:
                    move_in = False
                    move_out = True

                else:
                    move_in = True
                    move_out = False

                # if aml[0] and aml[0] > 0:
                #     move_in = True
                #     move_out = False
                #     if aml[2]:
                #         value = abs(aml[2])
                #     else:
                #         lot = 'SP'
                #         value = abs(aml[3])
                # elif aml[0] and aml[0] < 0:
                #     move_in = False
                #     move_out = True
                #     if aml[3]:
                #         value = abs(aml[3])
                #     else:
                #         lot = 'SP'
                #         value = abs(aml[2])
                # else:
                #     if aml[2]:
                #         move_in = True
                #         move_out = False
                #         value = abs(aml[2])
                #     else:
                #         move_in = False
                #         move_out = True
                #         value = abs(aml[3])
                if aml[5]:
                    value = abs(aml[5])
                else:
                    value = 0.00

                aml_id = self.env['stock.move'].sudo().browse(aml[1])

                if (aml_id._is_in() or aml_id._is_out()) and not aml_id.account_move_ids:
                    continue

                date = str(aml[2])
                print ('XXXXX')
                print(aml_id.reference)
                print(aml_id._is_in())
                print(aml_id._is_out())
                print(qty)
                print(value)

                qty = str(aml[0])

                if qty and value > 0:

                    price_unit = value / float(qty)


                elif qty and (not aml_id._is_in() and not aml_id._is_out()):
                    price_used = product_id.get_history_price(
                        self.env.user.company_id.id,
                        date=date,
                    )
                    # print ('price_used',price_used)
                    price_unit = price_used
                    if not price_used:
                        vendor_location = self.env['stock.location'].search([('usage','=','supplier')])
                        if vendor_location:
                            move_id = self.env['stock.move'].search([('location_id','in',vendor_location.ids),('date','<=',date)],limit=1,order='date desc')
                            if move_id:
                                price_unit = move_id.price_unit
                            else:
                                price_unit = 0.00


                    value = price_unit * float(qty)


                else:
                    price_unit = 0.00






                ref = aml_id.reference or aml_id.origin
                picking_number = aml_id.reference
                invoice_txt = ""

                val = {
                    'move_in': move_in,
                    'move_out': move_out,
                    'reference': ref,
                    'picking_number': picking_number,
                    'invoice_number': invoice_txt,
                    'remark': '',
                    'qty': qty,
                    'uom': product_id.uom_id.name,
                    'no_ref': "",
                    'price_unit': price_unit or 0.0,
                    'price_total': value or 0.0,
                    'lot': lot,
                    'date': date,
                }
                move_val.append(val)

        return move_val

    def last_5_get_stock_account_move_line_by_product(self,product_id,from_date):
        # print ('get_stock_account_move_line_by_product')
        move_val = []
        # product_product_id = self.env['product.product'].browse(product_id)
        account_id = product_id.categ_id.property_stock_valuation_account_id.id
        if not account_id:
            return move_val
        params = (product_id.id, account_id, from_date,)
        aml_query = """SELECT aml.quantity, aml.id, aml.debit, aml.credit,aml.date
                        FROM account_move_line AS aml
                        WHERE aml.quantity != 0 and aml.product_id = %s and aml.account_id = %s and aml.date < %s and aml.debit > 0
                        GROUP BY aml.product_id,aml.quantity,aml.debit,aml.credit,aml.id,aml.date
                        ORDER BY aml.date desc,aml.id
                    """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES--AML',res)
        # landed_cost_ids =
        count_old = 0
        if res:
            for aml in res:
                count_old +=1
                if count_old == 5:
                    break
                # print ('AML---',aml[0])
                qty = 0.00
                lot = ''
                move_in = False
                move_out = False
                ref = ''
                picking_number = ''
                invoice_txt = ''

                if aml[0]:
                    qty = abs(aml[0])
                else:
                    qty = 0.00


                if aml[0] and aml[0] > 0:
                    move_in = True
                    move_out = False
                    if aml[2]:
                        value = abs(aml[2])
                    else:
                        lot = 'SP'
                        value = abs(aml[3])
                elif aml[0] and aml[0] < 0:
                    move_in = False
                    move_out = True
                    if aml[3]:
                        value = abs(aml[3])
                    else:
                        lot = 'SP'
                        value = abs(aml[2])
                else:
                    if aml[2]:
                        move_in = True
                        move_out = False
                        value = abs(aml[2])
                    else:
                        move_in = False
                        move_out = True
                        value = abs(aml[3])


                if qty:
                    price_unit = value /qty
                else:
                    price_unit = 0.00

                date = str(aml[4])
                aml_id = self.env['account.move.line'].sudo().browse(aml[1])
                if aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().picking_id:
                    ref = aml_id.move_id.stock_move_id.sudo().picking_id.name
                    picking_number = aml_id.move_id.stock_move_id.sudo().picking_id.name
                    if aml_id.move_id.stock_move_id.sudo().picking_id.sale_id and aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids:
                        invoice_txt = aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids[0].number
                    else:
                        invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().inventory_id:
                    ref = aml_id.move_id.stock_move_id.sudo().inventory_id.name
                    picking_number = ""
                    invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo():
                    ref = aml_id.move_id.stock_move_id.sudo().origin
                    picking_number = ""
                    invoice_txt = ""
                else:
                    ref = aml_id.ref or aml_id.name
                    picking_number = ""
                    invoice_txt = ""

                val = {
                    'move_in': move_in,
                    'move_out': move_out,
                    'reference': ref,
                    'picking_number': picking_number,
                    'invoice_number': invoice_txt,
                    'remark': '',
                    'qty': qty,
                    'uom': product_id.uom_id.name,
                    'no_ref': "",
                    'price_unit': price_unit or 0.0,
                    'price_total': value or 0.0,
                    'lot': lot,
                    'date': date,
                    'aml_id':aml_id,
                }
                move_val.append(val)

        return move_val

    def get_stock_account_move_line_by_product(self,product_id,from_date,to_date):
        # print ('get_stock_account_move_line_by_product')
        move_val = []
        # product_product_id = self.env['product.product'].browse(product_id)
        account_id = product_id.categ_id.property_stock_valuation_account_id.id
        if not account_id:
            return move_val
        params = (product_id.id, account_id, from_date, to_date,)
        aml_query = """SELECT aml.quantity, aml.id, aml.debit, aml.credit,aml.date
                        FROM account_move_line AS aml
                        WHERE aml.product_id = %s and aml.account_id = %s and aml.date >= %s and aml.date <= %s
                        GROUP BY aml.product_id,aml.quantity,aml.debit,aml.credit,aml.id,aml.date
                        ORDER BY aml.date,aml.id
                    """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES--AML',res)
        # landed_cost_ids =
        if res:
            for aml in res:
                # print ('AML---',aml[0])
                qty = 0.00
                lot = ''
                move_in = False
                move_out = False
                ref = ''
                picking_number = ''
                invoice_txt = ''

                if aml[0]:
                    qty = abs(aml[0])
                else:
                    qty = 0.00


                if aml[0] and aml[0] > 0:
                    move_in = True
                    move_out = False
                    if aml[2]:
                        value = abs(aml[2])
                    else:
                        lot = 'SP'
                        value = abs(aml[3])
                elif aml[0] and aml[0] < 0:
                    move_in = False
                    move_out = True
                    if aml[3]:
                        value = abs(aml[3])
                    else:
                        lot = 'SP'
                        value = abs(aml[2])
                else:
                    if aml[2]:
                        move_in = True
                        move_out = False
                        value = abs(aml[2])
                    else:
                        move_in = False
                        move_out = True
                        value = abs(aml[3])


                if qty:
                    price_unit = value /qty
                else:
                    price_unit = 0.00

                date = str(aml[4])
                aml_id = self.env['account.move.line'].sudo().browse(aml[1])
                if aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().picking_id:
                    ref = aml_id.move_id.stock_move_id.sudo().picking_id.name
                    picking_number = aml_id.move_id.stock_move_id.sudo().picking_id.name
                    if aml_id.move_id.stock_move_id.sudo().picking_id.sale_id and aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids:
                        invoice_txt = aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids[0].number
                    else:
                        invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().inventory_id:
                    ref = aml_id.move_id.stock_move_id.sudo().inventory_id.name
                    picking_number = ""
                    invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo():
                    ref = aml_id.move_id.stock_move_id.sudo().origin
                    picking_number = ""
                    invoice_txt = ""
                else:
                    ref = aml_id.ref or aml_id.name
                    picking_number = ""
                    invoice_txt = ""

                val = {
                    'move_in': move_in,
                    'move_out': move_out,
                    'reference': ref,
                    'picking_number': picking_number,
                    'invoice_number': invoice_txt,
                    'remark': '',
                    'qty': qty,
                    'uom': product_id.uom_id.name,
                    'no_ref': "",
                    'price_unit': price_unit or 0.0,
                    'price_total': value or 0.0,
                    'lot': lot,
                    'date': date,
                    'aml_id':aml_id,
                }
                move_val.append(val)

        return move_val

    #for purchase account
    def get_stock_account_move_line_by_account(self,account_id,from_date,to_date):
        # print ('get_stock_account_move_line_by_product')
        move_val = []
        # product_product_id = self.env['product.product'].browse(product_id)
        # account_id = product_id.categ_id.property_stock_valuation_account_id.id
        if not account_id:
            return move_val
        params = (account_id, from_date, to_date,)
        aml_query = """SELECT aml.quantity, aml.id, aml.debit, aml.credit,aml.date
                        FROM account_move_line AS aml
                        LEFT JOIN account_move am ON (aml.move_id=am.id)
                        WHERE am.stock_move_id is not Null and aml.product_id is not Null and aml.account_id = %s and aml.date >= %s and aml.date <= %s
                        GROUP BY aml.quantity,aml.debit,aml.credit,aml.id,aml.date
                        ORDER BY aml.date
                    """

        self.env.cr.execute(aml_query, params)
        res = self.env.cr.fetchall()
        # print ('RES--AML',res)
        # landed_cost_ids =
        if res:
            for aml in res:
                # print ('AML---',aml[0])
                qty = 0.00
                lot = ''
                move_in = False
                move_out = False
                ref = ''
                picking_number = ''
                invoice_txt = ''

                if aml[0]:
                    qty = abs(aml[0])
                else:
                    qty = 0.00


                if aml[0] and aml[0] > 0:
                    move_in = True
                    move_out = False
                    if aml[2]:
                        value = abs(aml[2])
                    else:
                        lot = 'SP'
                        value = abs(aml[3])
                elif aml[0] and aml[0] < 0:
                    move_in = False
                    move_out = True
                    if aml[3]:
                        value = abs(aml[3])
                    else:
                        lot = 'SP'
                        value = abs(aml[2])
                else:
                    if aml[2]:
                        move_in = True
                        move_out = False
                        value = abs(aml[2])
                    else:
                        move_in = False
                        move_out = True
                        value = abs(aml[3])


                if qty:
                    price_unit = value /qty
                else:
                    price_unit = 0.00

                date = str(aml[4])
                aml_id = self.env['account.move.line'].sudo().browse(aml[1])
                if aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().picking_id:
                    ref = aml_id.move_id.name
                    picking_number = aml_id.move_id.stock_move_id.sudo().picking_id.name
                    if aml_id.move_id.stock_move_id.sudo().picking_id.sale_id and aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids:
                        invoice_txt = aml_id.move_id.stock_move_id.sudo().picking_id.sale_id.invoice_ids[0].number
                    else:
                        invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo() and aml_id.move_id.stock_move_id.sudo().inventory_id:
                    ref = aml_id.move_id.stock_move_id.sudo().inventory_id.name
                    picking_number = ""
                    invoice_txt = ""
                elif aml_id.move_id.sudo().stock_move_id.sudo():
                    ref = aml_id.move_id.stock_move_id.sudo().origin
                    picking_number = ""
                    invoice_txt = ""
                else:
                    ref = aml_id.ref or aml_id.name
                    picking_number = ""
                    invoice_txt = ""

                val = {
                    'move_in': move_in,
                    'move_out': move_out,
                    'reference': ref,
                    'picking_number': picking_number,
                    'invoice_number': invoice_txt,
                    'product_code': aml_id.product_id.default_code,
                    'product_name': aml_id.product_id.name,
                    'remark': '',
                    'qty': qty,
                    'uom': aml_id.product_id.uom_id.name,
                    'no_ref': "",
                    'price_unit': price_unit or 0.0,
                    'price_total': value or 0.0,
                    'lot': lot,
                    'date': date,
                    'aml_id':aml_id,
                }
                move_val.append(val)

        return move_val


    def _get_stock_move_after_by_product(self, stock_move_results):
        stock_move_after_results_by_product = list(filter(lambda x: x['is_initial'] == False, stock_move_results))

        move_val = []
        for move in stock_move_after_results_by_product:
            move_id = self.env['stock.move'].browse(move['move_id'])
            # print('move ',move)
            # print('move_id',move_id)
            # print('product_in ',move['product_in'])
            # print('product_out ',move['product_out'])
            # print('reference ',move['reference'])
            if move['product_in'] and move['product_out']:
                move_in = True
                move_out = True
            elif move['product_in']:
                move_in = True
                move_out = False
            elif move['product_out']:
                move_in = False
                move_out = True
            else:
                continue
            # print('move_id.picking_id:',move_id.picking_id)
            # print('move_id.picking_id:',move_id.picking_id.name)
            sale_order_id = self.env['sale.order'].search([('name', '=',move['origin'])])
            invoice_text = ""
            for sale_order in sale_order_id:
                for invoice in sale_order.invoice_ids.filtered(lambda x: x.state not in ('cancel','draft')):
                    # print('sale_orderrrrrrr:',sale_order)
                    invoice_text += invoice.number + " "
            if move_id.picking_id.name and not move_id.inventory_id:
                ref = move_id.picking_id.name
            elif move_id.inventory_id:
                ref = move_id.inventory_id.name
            else:
                ref = move['reference']

            if move_id.product_id.uom_id != move_id.product_uom:
                qty = move_id.product_uom._compute_quantity(move['qty_done'], move_id.product_id.uom_id)
            else:
                qty = move['qty_done']

            if move_id.picking_id.sale_id and move_id.picking_id.sale_id.invoice_ids:
                invoice_txt = move_id.picking_id.sale_id.invoice_ids[0].name
            else:
                invoice_txt = ""

            if len(move_id.sudo().account_move_ids.line_ids) > 2:
                value_debit = move_id.sudo().account_move_ids.line_ids.filtered(lambda x: x.product_id == move_id.product_id and x.account_id == move_id.product_id.property_stock_valuation_account_id).debit
                value_credit = move_id.sudo().account_move_ids.line_ids.filtered(lambda x: x.product_id == move_id.product_id and x.account_id == move_id.product_id.property_stock_valuation_account_id).credit
                value = value_debit - value_credit

            else:
                value = move_id.sudo().account_move_ids.amount

            if qty:
                price_unit = value / qty
            else:
                price_unit = 0.00

            val = {
                'move_in': move_in,
                'move_out': move_out,
                'reference': ref,
                'picking_number': move_id.picking_id.name,
                'invoice_number': invoice_txt,
                'remark': move_id.picking_id.note or '',
                'qty': qty,
                'uom': move_id.product_id.uom_id.name,
                'no_ref': move['origin'],
                'price_unit': price_unit or 0.0,
                'price_total': value or 0.0,
                'lot': self.env['stock.production.lot'].browse(move['lot_id']).name,
                'date': move['date'],
            }
            move_val.append(val)
            # print('move_val____aa:',move_val)
        return move_val


class WizardProductMovementReportXls(models.AbstractModel):
    _name = 'report.itaas_product_movement_report.pm_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        if lines.location_id:
            print('test generate_xlsx_report by location')
            for_left = workbook.add_format({'align': 'left'})
            for_left_border = workbook.add_format({'align': 'left', 'border': True})
            for_left_bold = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True})
            for_left_bold_border = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True, 'border': True})

            for_right = workbook.add_format({'align': 'right'})
            for_right_border = workbook.add_format({'align': 'right', 'border': True})
            for_right_bold_border = workbook.add_format({'align': 'right', 'border': True, 'bold': True})
            for_right_border_num_format = workbook.add_format(
                {'align': 'right', 'border': True, 'num_format': '#,##0.00'})
            for_right_bold_border_num_format = workbook.add_format(
                {'align': 'right', 'border': True, 'bold': True, 'num_format': '#,##0.00'})

            for_center = workbook.add_format({'align': 'center'})
            for_center_bold = workbook.add_format({'align': 'center', 'bold': True})
            for_center_border = workbook.add_format({'align': 'center', 'border': True})
            for_center_bold_border = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': True})
            for_center_border_num_format = workbook.add_format(
                {'align': 'center', 'border': True, 'num_format': '#,##0.00'})

            for_center_date = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy'})
            for_center_datetime = workbook.add_format(
                {'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy HH:MM'})

            # def convert_utc_to_usertz(date_time):
            #     if not date_time:
            #         return ''
            #     user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            #     tz = pytz.timezone('UTC')
            #     date_time = tz.localize(fields.Datetime.from_string(date_time)).astimezone(user_tz)
            #     date_time = date_time.strftime('%d/%m/%Y %H:%M')
            #
            #     return date_time

            worksheet = workbook.add_worksheet('รายงานเคลื่อนไหวสินค้า')
            worksheet2 = workbook.add_worksheet('รายงานสินค้าคงเหลือ')
            #
            ending_row = 0
            worksheet2.write(0, 0, 'สินค้า', for_center_bold_border)
            worksheet2.write(0, 1, 'ยกมา-QTY', for_center_bold_border)
            worksheet2.write(0, 2, 'ต่อหน่วย', for_center_bold_border)
            worksheet2.write(0, 3, 'คงเหลือ', for_center_bold_border)
            worksheet2.write(0, 4, 'ยกไป-QTY', for_center_bold_border)
            worksheet2.write(0, 5, 'ต่อหน่วย', for_center_bold_border)
            worksheet2.write(0, 6, 'คงเหลือ', for_center_bold_border)
            #

            i_row = 1
            worksheet.merge_range(i_row, 0, i_row, 13, 'รายงานเคลื่อนไหวสินค้า', for_center_bold_border)
            i_row += 1
            worksheet.merge_range(i_row, 0, i_row, 13,
                                  'ข้อมูลวันที่ ' + strToDate(str(lines.date_from)).strftime(
                                      "%d/%m/%Y") + " - " + strToDate(
                                      str(lines.date_to)).strftime("%d/%m/%Y"), for_center_bold_border)
            i_row += 2
            if lines.location_id:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.location_id.display_name, for_center_bold_border)
            else:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.warehouse_id.display_name, for_center_bold_border)

            i_row += 3
            i_col = 0
            worksheet.merge_range(i_row, 0, i_row, 4, ' ', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 5, i_row, 7, 'ยอดเข้า', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 8, i_row, 10, 'ยอดออก', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 11, i_row, 13, 'คงเหลือ', for_center_bold_border)

            i_row += 1
            i_col = 0
            worksheet.write(i_row, i_col, 'วันที่', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'เลขที่เอกสาร', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'Picking Number', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'เลขที่อ้างอิง', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ใบกำกับภาษี', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)



            str2d = fields.Date.from_string
            str2dt = fields.Datetime.from_string
            date_from = str2d(lines.date_from)
            date_to = str2d(lines.date_to)
            date_time_from = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_from), time.min))
            date_time_to = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_to), time.max))
            location_ids = lines._get_location()
            product_ids = lines._get_stock_move_product(location_ids)
            print('product_ids for Excel:', product_ids)
            if lines.location_id:
                warehouse = False
            else:
                warehouse = lines.warehouse_id

            # stock_move_results = lines._get_stock_move_results(date_from, date_to, warehouse, location_ids, product_ids)

            move_in = 0.0
            move_in_total_amount = 0.0
            move_out = 0.0
            move_out_total_amount = 0.0
            ending_balance = 0.00

            for product in product_ids:


                move_balance = 0.0
                move_balance_amount = 0.0
                last_balance_qty = last_balance_cost = 0.00

                # print('display_name', product.display_name)
                # stock_move_results_by_product = lines._get_stock_move_results_by_product(product, stock_move_results)
                last_warehouse_balance_qty = lines._get_stock_move_initial_qty_by_product(product.id, date_from)
                last_warehouse_balance_cost = lines._get_stock_move_initial_qty_by_product_cost(product.id, date_from)
                if last_warehouse_balance_qty:
                    unit_price = last_warehouse_balance_cost / last_warehouse_balance_qty
                else:
                    unit_price = 0.00

                last_balance_qty = lines._get_stock_move_initial_qty_by_product_by_location(product.id, date_from,lines.location_id.id)
                last_balance_cost = last_balance_qty * unit_price

                # last_balance_cost = 0.00
                # move_after = lines._get_stock_move_after_by_product(stock_move_results_by_product)
                move_after = lines.get_stock_account_move_line_by_product_by_location(product, date_from, date_to,lines.location_id.id)

                # print('product_id,', product.id)
                # print('last_balance_qty:', last_balance_qty)
                # print('move_after:', move_after)
                if not last_balance_qty and not move_after:
                    continue

                ending_row += 1
                i_row += 1
                i_col = 0
                worksheet.merge_range(i_row, i_col, i_row, 13, 'สินค้า :' + str(product.display_name), for_left_border)
                i_row += 1
                i_col = 0
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, 'ยอดยกมา', for_left_border)
                # qty in
                if last_balance_qty:
                    intial_price = last_balance_cost / last_balance_qty


                else:
                    intial_price = 0.00

                i_col += 1
                worksheet.write(i_row, i_col, last_balance_qty or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, intial_price or 0.00 or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_left_border)
                move_in_total_amount += last_balance_cost
                # qty in
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                # qty out end

                # end------
                i_col += 1
                worksheet.write(i_row, i_col, last_balance_qty or ' ', for_right_border_num_format)
                i_col += 1
                date_intial = (strToDate(lines.date_from) - relativedelta(days=1))
                print('date_intial:', date_intial)
                # intial_price = product.get_history_price(self.env.user.company_id.id,str(date_intial))
                # print('intial_price:',intial_price)
                # last_balance_cost = intial_price * last_balance_qty

                if last_balance_qty:
                    worksheet.write(i_row, i_col, intial_price or 0.00 or ' ', for_right_border_num_format)

                    i_col += 1
                    worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_right_border_num_format)
                else:
                    worksheet.write(i_row, i_col, 0.00 or ' ', for_right_border_num_format)

                    i_col += 1
                    worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_right_border_num_format)

                move_balance += last_balance_qty
                move_balance_amount += last_balance_cost
                move_in = 0
                move_in_amount = 0
                move_out = 0
                move_out_amount = 0
                count_move = len(move_after)
                count_start = 0

                worksheet2.write(ending_row, 0, product.default_code, for_center_bold_border)
                worksheet2.write(ending_row, 1, last_balance_qty, for_center_bold_border)
                worksheet2.write(ending_row, 2, last_balance_cost / last_balance_qty if last_balance_qty else 0.00,
                                 for_center_bold_border)
                worksheet2.write(ending_row, 3, last_balance_cost, for_center_bold_border)

                # 'list' object has no attribute 'filtered'
                # .filtered(lambda o: o.account_move_ids)
                # print ('move_after',move_after)
                if move_after:
                    for move in move_after:
                        count_start += 1
                        # print('** moveeeeeeeeeeeeeeeeeeeeeee:', move)

                        i_row += 1
                        i_col = 0
                        worksheet.write(i_row, i_col, move['date'] or ' ', for_center_date)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['reference'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['picking_number'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['no_ref'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['invoice_number'] or ' ', for_left_border)

                        if move['move_in'] and not move['move_out']:
                            # incomming
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['qty']:
                                price_unit = move['price_total'] / float(move['qty'])
                            else:
                                price_unit = 0.00

                            worksheet.write(i_row, i_col, price_unit or ' ', for_right_border_num_format)
                            i_col += 1
                            price_total = move['price_total']
                            worksheet.write(i_row, i_col, move['price_total'] or ' ', for_right_border_num_format)
                            # --
                            move_in = move_in + float(move['qty'])
                            move_balance = move_balance + float(move['qty'])
                            last_balance_cost += abs(price_total)
                            move_in_amount += price_total
                            move_in_total_amount += price_total

                            # move out
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)

                            # move balance
                            # date_after = move['date'] + relativedelta(days=1)
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id,date_after)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # move_balance_amount += price_total
                            # worksheet.write(i_row, i_col, price_unit_out or ' ', for_right_border_num_format)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, price_unit_out * move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1

                            if move['lot'] == 'SP':
                                move_balance_amount -= abs(price_total)
                            else:
                                move_balance_amount += abs(price_total)

                            # print('reff:',move['reference'])
                            # print('move_balance_amount:',move_balance_amount)
                            # print('last_balance_cost:',last_balance_cost)
                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if round(move_balance, 2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount

                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ',
                                                    for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)
                                # end product row
                                worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                # end product row
                                # worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                #                 for_right_border_num_format)

                                # worksheet.write(i_row, i_col, last_price_unit * move_balance or ' ', for_right_border_num_format)

                            else:
                                if round(move_balance, 2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                    for_right_border_num_format)

                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)

                        elif move['move_in'] and move['move_out']:
                            # internal
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_unit'], for_right_border_num_format)
                            i_col += 1
                            price_total = move['qty'] * move['price_unit']
                            worksheet.write(i_row, i_col, price_total, for_right_border_num_format)
                            # --
                            move_in = move_in + move['qty']
                            move_in_amount += move['price_total']

                            # move out
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_unit'], for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_total'], for_right_border_num_format)
                            # --
                            move_out = move_out + move['qty']
                            move_out_amount -= move['price_total']

                            # move balance
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id, move['date'])
                            # i_col += 1
                            # worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # move_balance_amount += price_total
                            # worksheet.write(i_row, i_col, price_unit_out or ' ', for_right_border_num_format)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, price_unit_out * move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # date_after = move['date'] + relativedelta(days=1)
                            #
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1

                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if move_balance:
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount
                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)

                                worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                for_right_border_num_format)

                                # end product row
                                worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                # end product row

                            else:
                                if move_balance:
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                else:
                                    worksheet.write(i_row, i_col, last_balance_cost or ' ', for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, i_col, move_balance_amount, for_right_border_num_format)



                        elif not move['move_in'] and move['move_out']:
                            # outgoing
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            # move out
                            i_col += 1

                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['price_total'] and move['qty']:
                                price_unit_out = move['price_total'] / float(move['qty'])



                            else:
                                price_unit_out = 0.00
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id, move['date'])
                            worksheet.write(i_row, i_col, abs(price_unit_out) or ' ', for_right_border_num_format)
                            i_col += 1
                            price_total = abs(move['price_total'])
                            worksheet.write(i_row, i_col, price_total or ' ', for_right_border_num_format)
                            # --
                            # print('price_total_111:', price_total)
                            # print('last_balance_cost:', last_balance_cost)
                            move_out = move_out + float(move['qty'])
                            move_balance = move_balance - float(move['qty'])

                            # last_balance_cost += abs(price_total)

                            move_out_amount -= price_total
                            move_out_total_amount += abs(price_total)

                            # move balance
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['lot'] == 'SP':
                                move_balance_amount += abs(price_total)
                            else:
                                move_balance_amount -= abs(price_total)

                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if round(move_balance, 2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount,
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount

                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ',
                                                    for_right_border_num_format)

                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)


                                # end product row
                                worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                # end product row

                            else:

                                if round(move_balance, 2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance,
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                    for_right_border_num_format)


                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)

                            # if move_balance:
                            #     worksheet.write(i_row, i_col,last_balance_cost / move_balance or ' ',for_right_border_num_format)
                            #     i_col += 1
                            #
                            #     worksheet.write(i_row, i_col, last_balance_cost or ' ', for_right_border_num_format)
                            #
                            # else:
                            #     worksheet.write(i_row, i_col, ' ',for_right_border_num_format)
                            #     i_col += 1
                            #
                            #     worksheet.write(i_row, i_col,   ' ', for_right_border_num_format)
                else:
                    ending_balance += last_balance_cost

                    worksheet2.write(ending_row, 4, last_balance_qty, for_center_bold_border)
                    worksheet2.write(ending_row, 5, last_balance_cost / last_balance_qty if last_balance_qty else 0.00,
                                     for_center_bold_border)
                    worksheet2.write(ending_row, 6, last_balance_cost, for_center_bold_border)

                i_row += 1
                i_col = 0
                worksheet.merge_range(i_row, i_col, i_row, 4, ' ', for_right_border_num_format)
                i_col = 5
                worksheet.write(i_row, i_col, move_in or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, move_in_amount or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, move_out or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, abs(move_out_amount) or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)

            i_row += 1
            i_col = 0
            worksheet.merge_range(i_row, i_col, i_row, 4, ' ', for_right_border_num_format)
            i_col = 5
            worksheet.write(i_row, i_col, ' Total ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, move_in_total_amount, for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, move_out_total_amount, for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ending_balance, for_right_border_num_format)
            # end product row
            ending_row += 1
            # worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
            # worksheet2.write(ending_row, 5,
            #                  move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
            #                  for_center_bold_border)
            worksheet2.write(ending_row, 6, ending_balance if round(ending_balance, 2) else 0.00,
                             for_center_bold_border)
            # end product row

            workbook.close()
        else:
            print('test generate_xlsx_report by warehouse')
            for_left = workbook.add_format({'align': 'left'})
            for_left_border = workbook.add_format({'align': 'left', 'border': True})
            for_left_bold = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True})
            for_left_bold_border = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True, 'border': True})

            for_right = workbook.add_format({'align': 'right'})
            for_right_border = workbook.add_format({'align': 'right', 'border': True})
            for_right_bold_border = workbook.add_format({'align': 'right', 'border': True, 'bold': True})
            for_right_border_num_format = workbook.add_format({'align': 'right', 'border': True, 'num_format': '#,##0.00'})
            for_right_bold_border_num_format = workbook.add_format(
                {'align': 'right', 'border': True, 'bold': True, 'num_format': '#,##0.00'})

            for_center = workbook.add_format({'align': 'center'})
            for_center_bold = workbook.add_format({'align': 'center', 'bold': True})
            for_center_border = workbook.add_format({'align': 'center', 'border': True})
            for_center_bold_border = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': True})
            for_center_border_num_format = workbook.add_format(
                {'align': 'center', 'border': True, 'num_format': '#,##0.00'})

            for_center_date = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy'})
            for_center_datetime = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy HH:MM'})

            # def convert_utc_to_usertz(date_time):
            #     if not date_time:
            #         return ''
            #     user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            #     tz = pytz.timezone('UTC')
            #     date_time = tz.localize(fields.Datetime.from_string(date_time)).astimezone(user_tz)
            #     date_time = date_time.strftime('%d/%m/%Y %H:%M')
            #
            #     return date_time

            worksheet = workbook.add_worksheet('รายงานเคลื่อนไหวสินค้า')
            worksheet2 = workbook.add_worksheet('รายงานสินค้าคงเหลือ')
            worksheet3 = workbook.add_worksheet('รายงานสินค้ามีปัญหามูลค่า')
            #
            ending_row = 0
            worksheet2.write(0, 0, 'สินค้า', for_center_bold_border)
            worksheet2.write(0, 1, 'ยกมา-QTY', for_center_bold_border)
            worksheet2.write(0, 2, 'ต่อหน่วย', for_center_bold_border)
            worksheet2.write(0, 3, 'คงเหลือ', for_center_bold_border)
            worksheet2.write(0, 4, 'ยกไป-QTY', for_center_bold_border)
            worksheet2.write(0, 5, 'ต่อหน่วย', for_center_bold_border)
            worksheet2.write(0, 6, 'คงเหลือ', for_center_bold_border)
            #
            worksheet3.write(0, 0, 'สินค้า', for_center_bold_border)
            worksheet3.write(0, 1, 'จำนวน', for_center_bold_border)
            worksheet3.write(0, 2, 'มูลค่า', for_center_bold_border)


            i_row = 1
            worksheet.merge_range(i_row, 0, i_row, 13, 'รายงานเคลื่อนไหวสินค้า', for_center_bold_border)
            i_row += 1
            worksheet.merge_range(i_row, 0, i_row, 13,
                                  'ข้อมูลวันที่ ' + strToDate(str(lines.date_from)).strftime(
                                      "%d/%m/%Y") + " - " + strToDate(
                                      str(lines.date_to)).strftime("%d/%m/%Y"), for_center_bold_border)
            i_row += 2
            if lines.location_id:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.location_id.display_name, for_center_bold_border)
            else:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.warehouse_id.display_name, for_center_bold_border)

            i_row += 3
            i_col = 0
            worksheet.merge_range(i_row, 0, i_row, 4, ' ', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 5, i_row, 7, 'ยอดเข้า', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 8, i_row, 10, 'ยอดออก', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 11, i_row, 13, 'คงเหลือ', for_center_bold_border)

            i_row += 1
            i_col = 0
            worksheet.write(i_row, i_col, 'วันที่', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'เลขที่เอกสาร', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'Picking Number', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'เลขที่อ้างอิง', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ใบกำกับภาษี', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)

            str2d = fields.Date.from_string
            str2dt = fields.Datetime.from_string
            date_from = str2d(lines.date_from)
            date_to = str2d(lines.date_to)
            date_time_from = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_from), time.min))
            date_time_to = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_to), time.max))
            location_ids = lines._get_location()
            product_ids = lines._get_stock_move_product(location_ids)
            # print('product_ids:', product_ids)
            if lines.location_id:
                warehouse = False
            else:
                warehouse = lines.warehouse_id


            # stock_move_results = lines._get_stock_move_results(date_from, date_to, warehouse, location_ids, product_ids)

            initial = 0.0
            initial_total_amount = 0.0
            move_in = 0.0
            move_in_total_amount = 0.0
            move_out = 0.0
            move_out_total_amount = 0.0
            ending_balance = 0.00
            missing_row = 0
            print ('All Product:',len(product_ids))
            count_product = 0
            start = False
            for product in product_ids:
                count_product +=1
                end = fields.datetime.now()
                if start:
                   print ('Time:',end-start)
                print ('Count Product:',count_product)
                print ('Product:',product.default_code)
                start = fields.datetime.now()


                move_balance = 0.0
                move_balance_amount = 0.0

                # print('display_name', product.display_name)
                # stock_move_results_by_product = lines._get_stock_move_results_by_product(product, stock_move_results)
                last_balance_qty = lines._get_stock_move_initial_qty_by_product(product.id, date_from)
                last_balance_cost = lines._get_stock_move_initial_qty_by_product_cost(product.id, date_from)
                # move_after = lines._get_stock_move_after_by_product(stock_move_results_by_product)
                move_after = lines.get_stock_account_move_line_by_product(product, date_from, date_to)

                # print('product_id,', product.id)
                # print('last_balance_qty:', last_balance_qty)
                # print('move_after:', move_after)
                if not last_balance_qty and not move_after:
                    if not last_balance_qty and last_balance_cost:
                        missing_row += 1
                        worksheet3.write(missing_row, 0, product.default_code, for_center_bold_border)
                        worksheet3.write(missing_row, 1, last_balance_qty, for_center_bold_border)
                        worksheet3.write(missing_row, 2, last_balance_cost, for_center_bold_border)

                    continue

                ending_row += 1
                i_row += 1
                i_col = 0
                worksheet.write(i_row, i_col,'สินค้า :' + str(product.display_name), for_left_border)
                i_row += 1
                i_col = 0
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, 'ยอดยกมา', for_left_border)
                #qty in
                if last_balance_qty:
                    intial_price = last_balance_cost / last_balance_qty
                    initial_total_amount += last_balance_cost
                else:
                    intial_price = 0.00

                i_col += 1
                worksheet.write(i_row, i_col, last_balance_qty or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, round(intial_price,2) or 0.00 or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_left_border)

                # qty in
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_left_border)
                # qty out end

                #end------
                i_col += 1
                worksheet.write(i_row, i_col, last_balance_qty or ' ', for_right_border_num_format)
                i_col += 1
                date_intial = (strToDate(lines.date_from) - relativedelta(days=1))
                # print('date_intial:', date_intial)
                # intial_price = product.get_history_price(self.env.user.company_id.id,str(date_intial))
                # print('intial_price:',intial_price)
                # last_balance_cost = intial_price * last_balance_qty


                if last_balance_qty:
                    worksheet.write(i_row, i_col, intial_price or 0.00 or ' ', for_right_border_num_format)

                    i_col += 1
                    worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_right_border_num_format)
                else:
                    worksheet.write(i_row, i_col, 0.00 or ' ', for_right_border_num_format)

                    i_col += 1
                    worksheet.write(i_row, i_col, last_balance_cost or '0.00', for_right_border_num_format)

                move_balance += last_balance_qty
                move_balance_amount += last_balance_cost
                move_in = 0
                move_in_amount = 0
                move_out = 0
                move_out_amount = 0
                count_move = len(move_after)
                count_start = 0

                worksheet2.write(ending_row, 0, product.default_code, for_center_bold_border)
                worksheet2.write(ending_row, 1, last_balance_qty, for_center_bold_border)
                worksheet2.write(ending_row, 2, last_balance_cost / last_balance_qty if last_balance_qty else 0.00,
                                 for_center_bold_border)
                worksheet2.write(ending_row, 3, last_balance_cost, for_center_bold_border)

                # 'list' object has no attribute 'filtered'
                # .filtered(lambda o: o.account_move_ids)
                # print ('move_after',move_after)
                if move_after:
                    for move in move_after:
                        count_start += 1
                        # print('** moveeeeeeeeeeeeeeeeeeeeeee:', move)

                        i_row += 1
                        i_col = 0
                        worksheet.write(i_row, i_col, move['date'] or ' ', for_center_date)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['reference'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['picking_number'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['no_ref'] or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, move['invoice_number'] or ' ', for_left_border)

                        if move['move_in'] and not move['move_out']:
                            # incomming
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['qty']:
                                price_unit = move['price_total'] / move['qty']
                            else:
                                price_unit = 0.00

                            worksheet.write(i_row, i_col, price_unit or ' ', for_right_border_num_format)
                            i_col += 1
                            price_total = move['price_total']
                            worksheet.write(i_row, i_col, move['price_total'] or ' ', for_right_border_num_format)
                            # --
                            move_in = move_in + move['qty']
                            move_balance = move_balance + move['qty']
                            last_balance_cost += abs(price_total)
                            move_in_amount += price_total
                            move_in_total_amount += price_total

                            # move out
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)

                            # move balance
                            # date_after = move['date'] + relativedelta(days=1)
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id,date_after)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # move_balance_amount += price_total
                            # worksheet.write(i_row, i_col, price_unit_out or ' ', for_right_border_num_format)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, price_unit_out * move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1

                            if move['lot'] == 'SP':
                                move_balance_amount -= abs(price_total)
                            else:
                                move_balance_amount += abs(price_total)


                            # print('reff:',move['reference'])
                            # print('move_balance_amount:',move_balance_amount)
                            # print('last_balance_cost:',last_balance_cost)
                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if round(move_balance,2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount

                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ',
                                                    for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)
                                #end product row
                                worksheet2.write(ending_row, 4, round(move_balance,2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance,2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance,2) else 0.00, for_center_bold_border)

                                if not move_balance and move_balance_amount:
                                    missing_row += 1
                                    worksheet3.write(missing_row, 0, product.default_code, for_center_bold_border)
                                    worksheet3.write(missing_row, 1, move_balance, for_center_bold_border)
                                    worksheet3.write(missing_row, 2, move_balance_amount, for_center_bold_border)

                                # end product row
                                # worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                #                 for_right_border_num_format)

                                # worksheet.write(i_row, i_col, last_price_unit * move_balance or ' ', for_right_border_num_format)

                            else:
                                if round(move_balance,2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ', for_right_border_num_format)

                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)

                        elif move['move_in'] and move['move_out']:
                            # internal
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_unit'], for_right_border_num_format)
                            i_col += 1
                            price_total = move['qty'] * move['price_unit']
                            worksheet.write(i_row, i_col, price_total, for_right_border_num_format)
                            # --
                            move_in = move_in + move['qty']
                            move_in_amount += move['price_total']

                            # move out
                            i_col += 1
                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_unit'], for_right_border_num_format)
                            i_col += 1
                            worksheet.write(i_row, i_col, move['price_total'], for_right_border_num_format)
                            # --
                            move_out = move_out + move['qty']
                            move_out_amount -= move['price_total']

                            # move balance
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id, move['date'])
                            # i_col += 1
                            # worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # move_balance_amount += price_total
                            # worksheet.write(i_row, i_col, price_unit_out or ' ', for_right_border_num_format)
                            # i_col += 1
                            # worksheet.write(i_row, i_col, price_unit_out * move_balance or ' ', for_right_border_num_format)
                            # i_col += 1
                            # date_after = move['date'] + relativedelta(days=1)
                            #
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1

                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if move_balance:
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount
                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)

                                worksheet.write(i_row, i_col, move_balance_amount or ' ',
                                                for_right_border_num_format)

                                # end product row
                                worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                # end product row
                                if not move_balance and move_balance_amount:
                                    missing_row += 1
                                    worksheet3.write(missing_row, 0, product.default_code, for_center_bold_border)
                                    worksheet3.write(missing_row, 1, move_balance, for_center_bold_border)
                                    worksheet3.write(missing_row, 2, move_balance_amount, for_center_bold_border)

                            else:
                                if move_balance:
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                else:
                                    worksheet.write(i_row, i_col, last_balance_cost or ' ', for_right_border_num_format)
                                i_col += 1
                                worksheet.write(i_row, i_col, move_balance_amount, for_right_border_num_format)



                        elif not move['move_in'] and move['move_out']:
                            # outgoing
                            # move in
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            i_col += 1
                            worksheet.write(i_row, i_col, ' ', for_left_border)
                            # move out
                            i_col += 1

                            worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['qty']:
                                price_unit_out = move['price_total'] / move['qty']
                            else:
                                price_unit_out = 0.00
                            # price_unit_out = product.get_history_price(self.env.user.company_id.id, move['date'])
                            worksheet.write(i_row, i_col, abs(price_unit_out) or ' ', for_right_border_num_format)
                            i_col += 1
                            price_total = abs(move['price_total'])
                            worksheet.write(i_row, i_col, price_total or ' ', for_right_border_num_format)
                            # --
                            # print('price_total_111:', price_total)
                            # print('last_balance_cost:', last_balance_cost)
                            move_out = move_out + move['qty']
                            move_balance = move_balance - move['qty']

                            # last_balance_cost += abs(price_total)

                            move_out_amount -= price_total
                            move_out_total_amount += abs(price_total)

                            # move balance
                            i_col += 1
                            worksheet.write(i_row, i_col, move_balance or ' ', for_right_border_num_format)
                            i_col += 1
                            if move['lot'] == 'SP':
                                move_balance_amount += abs(price_total)
                            else:
                                move_balance_amount -= abs(price_total)

                            if count_start == count_move:  # last move apply
                                # last_price_unit = product.get_history_price(self.env.user.company_id.id, str(date_to))

                                if round(move_balance,2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance or ' ',
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount,
                                                    for_right_border_num_format)
                                    ending_balance += move_balance_amount
                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ',
                                                    for_right_border_num_format)


                                worksheet.write(i_row, 2, 'ENDING', for_right_border_num_format)


                                # end product row
                                worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
                                worksheet2.write(ending_row, 5,
                                                 move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                worksheet2.write(ending_row, 6, move_balance_amount if round(move_balance, 2) else 0.00,
                                                 for_center_bold_border)
                                # end product row
                                if not move_balance and move_balance_amount:
                                    missing_row += 1
                                    worksheet3.write(missing_row, 0, product.default_code, for_center_bold_border)
                                    worksheet3.write(missing_row, 1, move_balance, for_center_bold_border)
                                    worksheet3.write(missing_row, 2, move_balance_amount, for_center_bold_border)

                            else:

                                if round(move_balance,2):
                                    worksheet.write(i_row, i_col, move_balance_amount / move_balance,
                                                    for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, move_balance_amount or ' ', for_right_border_num_format)


                                else:
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                                    i_col += 1
                                    worksheet.write(i_row, i_col, ' ', for_right_border_num_format)



                            # if move_balance:
                            #     worksheet.write(i_row, i_col,last_balance_cost / move_balance or ' ',for_right_border_num_format)
                            #     i_col += 1
                            #
                            #     worksheet.write(i_row, i_col, last_balance_cost or ' ', for_right_border_num_format)
                            #
                            # else:
                            #     worksheet.write(i_row, i_col, ' ',for_right_border_num_format)
                            #     i_col += 1
                            #
                            #     worksheet.write(i_row, i_col,   ' ', for_right_border_num_format)
                else:
                    ending_balance += last_balance_cost

                    worksheet2.write(ending_row, 4, last_balance_qty, for_center_bold_border)
                    worksheet2.write(ending_row, 5, last_balance_cost / last_balance_qty if last_balance_qty else 0.00, for_center_bold_border)
                    worksheet2.write(ending_row, 6, last_balance_cost, for_center_bold_border)
                    if not last_balance_qty and last_balance_cost:
                        missing_row += 1
                        worksheet3.write(missing_row, 0, product.default_code, for_center_bold_border)
                        worksheet3.write(missing_row, 1, last_balance_qty, for_center_bold_border)
                        worksheet3.write(missing_row, 2, last_balance_cost, for_center_bold_border)

                i_row += 1
                # i_col = 0
                # worksheet.merge_range(i_row, i_col, i_row, 4, ' ', for_right_border_num_format)
                i_col = 5
                worksheet.write(i_row, i_col, move_in or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, move_in_amount or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, move_out or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, abs(move_out_amount) or ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_right_border_num_format)

            i_row += 1
            # i_col = 0
            # worksheet.write(i_row, i_col, i_row, 4, ' ', for_right_border_num_format)
            i_col = 5
            worksheet.write(i_row, i_col, ' Total ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, initial_total_amount, for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, move_in_total_amount, for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, move_out_total_amount, for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ending_balance, for_right_border_num_format)
            # end product row
            ending_row +=1
            # worksheet2.write(ending_row, 4, round(move_balance, 2), for_center_bold_border)
            # worksheet2.write(ending_row, 5,
            #                  move_balance_amount / move_balance if round(move_balance, 2) else 0.00,
            #                  for_center_bold_border)
            worksheet2.write(ending_row, 6, ending_balance if round(ending_balance, 2) else 0.00, for_center_bold_border)
            # end product row


            workbook.close()


class WizardProductMovementPurchaseReportXls(models.AbstractModel):
    _name = 'report.itaas_product_movement_report.purchase_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        if lines:
            print('test generate_xlsx_report by purchase warehouse')
            for_left = workbook.add_format({'align': 'left'})
            for_left_border = workbook.add_format({'align': 'left', 'border': True})
            for_left_bold = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True})
            for_left_bold_border = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True, 'border': True})

            for_right = workbook.add_format({'align': 'right'})
            for_right_border = workbook.add_format({'align': 'right', 'border': True})
            for_right_bold_border = workbook.add_format({'align': 'right', 'border': True, 'bold': True})
            for_right_border_num_format = workbook.add_format({'align': 'right', 'border': True, 'num_format': '#,##0.00'})
            for_right_bold_border_num_format = workbook.add_format(
                {'align': 'right', 'border': True, 'bold': True, 'num_format': '#,##0.00'})

            for_center = workbook.add_format({'align': 'center'})
            for_center_bold = workbook.add_format({'align': 'center', 'bold': True})
            for_center_border = workbook.add_format({'align': 'center', 'border': True})
            for_center_bold_border = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': True})
            for_center_border_num_format = workbook.add_format(
                {'align': 'center', 'border': True, 'num_format': '#,##0.00'})

            for_center_date = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy'})
            for_center_datetime = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy HH:MM'})

            # def convert_utc_to_usertz(date_time):
            #     if not date_time:
            #         return ''
            #     user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            #     tz = pytz.timezone('UTC')
            #     date_time = tz.localize(fields.Datetime.from_string(date_time)).astimezone(user_tz)
            #     date_time = date_time.strftime('%d/%m/%Y %H:%M')
            #
            #     return date_time

            worksheet = workbook.add_worksheet('รายงานรับสินค้า')
            # worksheet2 = workbook.add_worksheet('รายงานสินค้าคงเหลือ')
            # worksheet3 = workbook.add_worksheet('รายงานสินค้ามีปัญหามูลค่า')
            #
            ending_row = 0
            # worksheet2.write(0, 0, 'สินค้า', for_center_bold_border)
            # worksheet2.write(0, 1, 'ยกมา-QTY', for_center_bold_border)
            # worksheet2.write(0, 2, 'ต่อหน่วย', for_center_bold_border)
            # worksheet2.write(0, 3, 'คงเหลือ', for_center_bold_border)
            # worksheet2.write(0, 4, 'ยกไป-QTY', for_center_bold_border)
            # worksheet2.write(0, 5, 'ต่อหน่วย', for_center_bold_border)
            # worksheet2.write(0, 6, 'คงเหลือ', for_center_bold_border)
            # #
            # worksheet3.write(0, 0, 'สินค้า', for_center_bold_border)
            # worksheet3.write(0, 1, 'จำนวน', for_center_bold_border)
            # worksheet3.write(0, 2, 'มูลค่า', for_center_bold_border)


            i_row = 1
            worksheet.merge_range(i_row, 0, i_row, 13, 'รายงานรับสินค้า', for_center_bold_border)
            i_row += 1
            worksheet.merge_range(i_row, 0, i_row, 13,
                                  'ข้อมูลวันที่ ' + strToDate(str(lines.date_from)).strftime(
                                      "%d/%m/%Y") + " - " + strToDate(
                                      str(lines.date_to)).strftime("%d/%m/%Y"), for_center_bold_border)
            i_row += 2
            if lines.location_id:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.location_id.display_name, for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, 'Account', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.account_id.code, for_center_bold_border)
            else:
                i_col = 0
                worksheet.write(i_row, i_col, 'คลังสินค้า', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.warehouse_id.display_name, for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, 'Account', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, lines.account_id.code, for_center_bold_border)

            i_row += 3
            i_col = 0
            worksheet.merge_range(i_row, 0, i_row, 4, ' ', for_center_bold_border)
            i_col += 1
            worksheet.merge_range(i_row, 5, i_row, 7, 'ยอดเข้า', for_center_bold_border)
            # i_col += 1
            # worksheet.merge_range(i_row, 8, i_row, 10, 'ยอดออก', for_center_bold_border)
            # i_col += 1
            # worksheet.merge_range(i_row, 11, i_row, 13, 'คงเหลือ', for_center_bold_border)

            i_row += 1
            i_col = 0
            worksheet.write(i_row, i_col, 'วันที่', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'เลขที่เอกสาร', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'Picking Number', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'รหัสสินค้า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ชื่อสินค้า', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'จำนวน', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'ต้นทุน', for_center_bold_border)
            # i_col += 1
            # worksheet.write(i_row, i_col, 'มูลค่า', for_center_bold_border)

            str2d = fields.Date.from_string
            str2dt = fields.Datetime.from_string
            date_from = str2d(lines.date_from)
            date_to = str2d(lines.date_to)
            date_time_from = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_from), time.min))
            date_time_to = lines.convert_usertz_to_utc(datetime.combine(str2dt(lines.date_to), time.max))
            location_ids = lines._get_location()
            # product_ids = lines._get_stock_move_product(location_ids)
            # print('product_ids:', product_ids)
            if lines.location_id:
                warehouse = False
            else:
                warehouse = lines.warehouse_id


            # stock_move_results = lines._get_stock_move_results(date_from, date_to, warehouse, location_ids, product_ids)

            initial = 0.0
            initial_total_amount = 0.0
            move_in = 0.0
            move_in_total_amount = 0.0
            move_out = 0.0
            move_out_total_amount = 0.0
            ending_balance = 0.00
            missing_row = 0
            move_by_account = lines.get_stock_account_move_line_by_account(lines.account_id.id, date_from, date_to)
            for move in move_by_account:

                i_row += 1
                i_col = 0
                worksheet.write(i_row, i_col, move['date'] or ' ', for_center_date)
                i_col += 1
                worksheet.write(i_row, i_col, move['reference'] or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, move['picking_number'] or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, move['product_code'] or ' ', for_left_border)
                i_col += 1
                worksheet.write(i_row, i_col, move['product_name'] or ' ', for_left_border)

                if move['move_in'] and not move['move_out']:
                    # incomming
                    # move in
                    i_col += 1
                    worksheet.write(i_row, i_col, move['qty'] or ' ', for_right_border_num_format)
                    i_col += 1
                    if move['qty']:
                        price_unit = move['price_total'] / move['qty']
                    else:
                        price_unit = 0.00

                    worksheet.write(i_row, i_col, price_unit or ' ', for_right_border_num_format)
                    i_col += 1
                    price_total = move['price_total']
                    worksheet.write(i_row, i_col, move['price_total'] or ' ', for_right_border_num_format)

                    ending_balance += abs(price_total)


                elif not move['move_in'] and move['move_out']:

                    i_col += 1
                    worksheet.write(i_row, i_col, move['qty'] * (-1) or ' ', for_right_border_num_format)
                    i_col += 1
                    if move['qty']:
                        price_unit_out = move['price_total'] / move['qty']
                    else:
                        price_unit_out = 0.00

                    worksheet.write(i_row, i_col, abs(price_unit_out) or ' ', for_right_border_num_format)
                    i_col += 1
                    worksheet.write(i_row, i_col, move['price_total'] * (-1) or ' ', for_right_border_num_format)
                    ending_balance -= move['price_total']



            i_row += 1
            i_col = 5
            worksheet.write(i_row, i_col, ' Total ', for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, "", for_right_border_num_format)
            i_col += 1
            worksheet.write(i_row, i_col, ending_balance, for_right_border_num_format)

            workbook.close()
