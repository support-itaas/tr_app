# -*- coding: utf-8 -*-
import operator
from datetime import datetime, date
from io import BytesIO
from odoo.tools.float_utils import float_round
from dateutil.relativedelta import relativedelta
from odoo import tools
# from odoo import api, fields, models, _
from odoo.tools import float_compare, misc
from odoo.tools.translate import _
from odoo import api, models, fields, _
import xlwt
import time
import xlsxwriter
import base64
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class Product(models.Model):
    _inherit = "product.product"

    def _compute_quantities_dict_by_location(self, location_id, lot_id, owner_id, package_id, from_date=False, to_date=False):
        print ('_compute_quantities_dict')
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations_new(location_id.id)
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        if to_date and to_date < fields.Datetime.now(): #Only to_date as to_date will correspond to qty_available
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            domain_move_in += [('date', '>=', from_date)]
            domain_move_out += [('date', '>=', from_date)]
        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]


        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_in
        domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            if product.default_code == 'AVTN0600' or product.default_code == 'T11111':

                print (product.default_code)
                print(domain_quant)
                print ('-DETAIL-AVTN0600-')
                product_id = product.id
                rounding = product.uom_id.rounding
                res[product_id] = {}
                print ('QUANT')
                print (quants_res)
                if dates_in_the_past:
                    qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
                else:
                    qty_available = quants_res.get(product_id, 0.0)


                res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
                res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
                res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
                res[product_id]['virtual_available'] = float_round(
                    qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
                    precision_rounding=rounding)
            else:
                product_id = product.id
                rounding = product.uom_id.rounding
                res[product_id] = {}
                if dates_in_the_past:
                    qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
                else:
                    qty_available = quants_res.get(product_id, 0.0)
                res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
                res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
                res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
                res[product_id]['virtual_available'] = float_round(
                    qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
                    precision_rounding=rounding)

        return res

class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    location_id = fields.Many2one('stock.location', string='Stock Location')
    # category_id = fields.Many2one('product.category', string='Product Category')#old 31-08-2019
    # category_id = fields.Many2many('product.category', string='Product Category')
    category_id = fields.Many2one('product.category', string='Product Category')
    count_category = fields.Integer('Count Category', default=0)
    product_id = fields.Many2one('product.product', string='Product')
    product_code_form = fields.Char(string='Product Code Form')
    product_code_to = fields.Char(string='Product Code To')

    product_form = fields.Many2one('product.product',string='Product Form')
    product_to = fields.Many2one('product.product', string='Product to')

    restrict_locations = fields.Many2many('stock.location', string='Restrict Location')
    account_id = fields.Many2one('account.account',string='Account')
    report_type = fields.Selection([('account','Account'),('location','Location')],string='Report Type')
    is_show_location = fields.Boolean(string='Show Location')

    @api.model
    def default_get(self, fields):
        res = super(StockQuantityHistory,self).default_get(fields)
        if self.env.user.restrict_locations:
            restrict_locations = self.env.user.stock_location_ids.filtered(lambda x: x.usage == 'internal').ids
        else:
            restrict_locations = self.env['stock.location'].search([('usage', '=', 'internal')]).ids
        res.update({'restrict_locations':restrict_locations})
        return res

    @api.onchange('product_form','product_to')
    def on_product_form_to(self):
        if self:
            if self.product_form:
                self.product_code_form = self.product_form.default_code
            #default_code
            if self.product_to:
                self.product_code_to = self.product_to.default_code

    @api.onchange('category_id')
    def on_category_id(self):
        self.product_code_form = False
        self.product_code_to = False
        count_category = 0
        for line in self.category_id:
            count_category += 1
        self.count_category = count_category

    def print_inventory_value(self, data):
        data = {}
        data['form'] = self.read(['date', 'location_id', 'category_id','product_code_form','product_code_to','account_id'])[0]
        # return self.env['report'].get_action(self, 'stock_extended.report_stockhistory_id', data=data)
        print('form_data: '+str(data))
        return self.env.ref('stock_extended.action_report_stock_history').report_action(self, data=data, config=False)

    def open_table_inventory_value(self):
        self.ensure_one()
        # print('open_table_inventory_value')
        if self.compute_at_date:
            tree_view_id = self.env.ref('stock.view_stock_product_tree').id
            form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
            # We pass `to_date` in the context so that `qty_available` will be computed across
            # moves until date.
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Products'),
                'res_model': 'product.product',
                'context': dict(self.env.context, to_date=self.date),
            }
            # print('action: '+str(action))
            # print(dict(self.env.context, to_date=self.date))
            return action

    @api.multi
    def get_stock_value(self,data):
        # print('get_stock_value')
        # print(data)
        result = {}
        StockMove = self.env['stock.move']
        if data['form']['date']:
            to_date = data['form']['date']
        else:
            to_date = str(datetime.today().date())
        if data['form']['account_id']:
            stock_account_id = data['form']['account_id'][0]
        else:
            stock_account_id = False
        # print("to_date: "+str(to_date))
        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        if stock_account_id:
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                             FROM account_move_line AS aml
                            WHERE aml.product_id IS NOT NULL AND aml.account_id = %%s AND aml.company_id=%%s %s
                         GROUP BY aml.product_id, aml.account_id"""
            params = (stock_account_id,self.env.user.company_id.id,)
        else:
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                                         FROM account_move_line AS aml
                                        WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                                     GROUP BY aml.product_id, aml.account_id"""
            params = (self.env.user.company_id.id,)

        # print ('TODATE',to_date)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)

        else:
            # print('else')
            query = query % ('',)

        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        # print(res)
        for row in res:
            # print(row)
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        # print(fifo_automated_values)
        domain = [('type','=','product')]
        location_id = False
        # if data['form']['category_id']:#old 31-08-2019
        if data['form']['category_id'] :
            # print(data['form']['category_id'])
            # domain.append(('categ_id','=',data['form']['category_id'][0]))#old 31-08-2019
            domain.append(('categ_id', 'in', data['form']['category_id']))

        if data['form']['product_code_form'] and  data['form']['product_code_to']:#31-08-2019
            # print(data['form']['product_code_form'])
            domain.append(('default_code', '>=', str(data['form']['product_code_form'])))
            domain.append(('default_code', '<=', str(data['form']['product_code_to'])))

        if data['form']['location_id']:#03-09-2019
            # print(data['form']['location_id'])
            location_id = data['form']['location_id'][0]
            domain.append(('location_id', '=', str(data['form']['location_id'][0])))

        if data['form']['account_id']:  # 03-09-2019
            domain.append(('categ_id.property_stock_valuation_account_id', '=', data['form']['account_id'][0]))
            # data['form']['account_id'][0]
        print('>>'+str(domain))
        product_ids = self.env['product.product'].search(domain)
        # print(product_ids)

        print ('COUNT PRODUCT-1',len(product_ids))

        stock_product_ids=[]
        for line in product_ids.filtered(lambda x: x.product_tmpl_id.valuation == 'real_time'):
            stock_product_ids.append(line.id)

        product_final_ids = self.env['product.product'].search([('id', 'in', stock_product_ids)],order = 'default_code')
        # print ('COUNT PRODUCT-2', len(product_final_ids))
        # print (xxx)
        count_product = 0
        for product in product_final_ids:
            # count_product +=1
            result[product.id] = {}

            stock_qty = 0.00
            stock_value = 0.00

            if to_date:
                price_used = product.get_history_price(
                    self.env.user.company_id.id,
                    date=to_date,
                ) if product.cost_method in ['standard', 'average'] else 0.0

                if product.product_tmpl_id.valuation == 'real_time':
                    valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                    value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])


                    stock_qty = quantity
                    stock_value = value
                    if stock_qty and stock_value:
                        avg_price = stock_value / stock_qty
                    else:
                        avg_price = 0

                    if data['form']['report_type'] == 'account' and not self.is_show_location:
                        if stock_qty > 0 or stock_value > 0:
                            result[product.id][0] = {
                                'product_id': product.id,
                                'name': product.name,
                                'product_default_code': product.default_code or '',
                                'unit': product.uom_id.name,
                                'qty': stock_qty,
                                'account': product.categ_id.property_stock_valuation_account_id.code,
                                'value': round(stock_value, 2),
                                'stock_quant_ids': False,
                                'avg_price': avg_price,
                            }
                    else:
                        #only gl available
                        gl_stock_qty = stock_qty
                        if stock_qty > 0 or stock_value > 0:
                            print ('XXXX-1',strToDate(to_date))
                            print('XXXX-2', datetime.today().date())
                            if strToDate(to_date) != datetime.today().date():
                                if self.location_id:
                                    location_ids = self.location_id
                                else:
                                    location_ids = product.sudo().stock_move_ids.mapped('location_dest_id')

                                for location_id in location_ids.filtered(lambda x: x.usage == 'internal' and x.company_id.id == self.env.user.company_id.id):
                                # if self.location_id:
                                    stock_quant_ids = self.env['stock.quant'].search(
                                        [('product_id', '=', product.id), ('location_id', '=', location_id.id)])
                                    stock_qty = sum(stock_quant_id.quantity for stock_quant_id in stock_quant_ids)
                                    # print ('ORIGINAL VALUE by LOCATION',stock_qty)


                                    domain_move_in_loc = [('location_dest_id','=',location_id.id)]
                                    domain_move_out_loc = [('location_id', '=', location_id.id)]
                                    domain_move_in = [('product_id', 'in', product.ids)] + domain_move_in_loc
                                    domain_move_out = [('product_id', 'in', product.ids)] + domain_move_out_loc
                                    domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in
                                    domain_move_out_done = [('state', '=', 'done'),('date', '>', to_date)] + domain_move_out

                                    move_in_qty = abs(sum(move.quantity_done for move in self.env['stock.move'].search(domain_move_in_done)))
                                    move_out_qty = abs(sum(move.quantity_done for move in self.env['stock.move'].search(domain_move_out_done)))
                                    stock_qty = stock_qty + move_out_qty - move_in_qty

                                    if stock_qty <= 0:
                                        continue
                                    # if not stock_qty:
                                    #     continue

                                    result[product.id][location_id.id] = {
                                        'product_id': product.id,
                                        'name': product.name,
                                        'product_default_code': product.default_code or '',
                                        'unit': product.uom_id.name,
                                        'qty': stock_qty,
                                        'account': product.categ_id.property_stock_valuation_account_id.code,
                                        'value': round(stock_value, 2),
                                        'stock_quant_ids': stock_quant_ids,
                                        'avg_price': avg_price,
                                    }
                                    print ('RESULT11111111111',result)

                            else:
                                # print ('TO DATE TODAY')
                                if self.location_id:
                                    location_ids = self.location_id
                                else:
                                    location_ids = product.stock_quant_ids.sudo().mapped('location_id')

                                for location_id in location_ids.sudo().sorted(key=lambda l: l.id).filtered(lambda x: x.usage == 'internal' and x.company_id.id == self.env.user.company_id.id):
                                    print ('XXX sort---')
                                    stock_quant_ids = self.env['stock.quant'].search(
                                        [('product_id', '=', product.id), ('location_id', '=', location_id.id)])
                                    stock_qty = sum(stock_quant_id.quantity for stock_quant_id in stock_quant_ids)
                                    if stock_qty <= 0:
                                        continue
                                    # print ('Location',location_id.id)
                                    # print ('product', product.id)
                                    # 'unit': product.uom_id.name + '|' + str(gl_stock_qty),

                                    result[product.id][location_id.id] = {
                                        'product_id': product.id,
                                        'name': product.name,
                                        'product_default_code': product.default_code or '',
                                        'unit': product.uom_id.name,
                                        'qty': stock_qty,
                                        'account': product.categ_id.property_stock_valuation_account_id.code,
                                        'value': round(stock_value, 2),
                                        'stock_quant_ids': stock_quant_ids,
                                        'avg_price': avg_price,
                                    }

        result = [value for key, value in result.items()]

        return result

    def get_inventory(self, data):
        # print(data)
        # print(data['form']['date'])
        # print(data['form']['location_id'][0])
        print('query get_inventory')
        stock_history_obj = self.env['stock.quantity.history']
        # data = self.read(cr, uid, ids, context=context)[0]
        if data['form']['location_id'] and data['form']['location_id'][0] and not data['form']['category_id']:
            self.env.cr.execute('SELECT s.product_id, p.name, sum(s.quantity) as quantity, count(s.product_id) as product_id_count FROM stock_quantity_history s JOIN product_template p ON p.id=s.product_template_id where s.date <= %s and s.location_id = %s and type = %s group by s.product_id, p.name order by p.name',(data['form']['date'],data['form']['location_id'][0],'product'))
        if data['form']['category_id'] and data['form']['category_id'][0] and not data['form']['location_id']:
            self.env.cr.execute('SELECT s.product_id, p.name, sum(s.quantity) as quantity, count(s.product_id) as product_id_count FROM stock_quantity_history s JOIN product_template p ON p.id=s.product_template_id where s.date <= %s and p.categ_id = %s and type = %s group by s.product_id, p.name order by p.name',(data['form']['date'],data['form']['category_id'][0],'product'))
        if data['form']['category_id'] and data['form']['location_id'] and data['form']['location_id'][0] and data['form']['category_id'][0]:
            self.env.cr.execute(
                'SELECT s.product_id, p.name, sum(s.quantity) as quantity, count(s.product_id) as product_id_count FROM stock_quantity_history s JOIN product_template p ON p.id=s.product_template_id where s.date <= %s and s.location_id = %s and p.categ_id = %s and type = %s NULL group by s.product_id, p.name order by p.name',
                (data['form']['date'], data['form']['location_id'][0],data['form']['category_id'][0],'product'))
        if not data['form']['category_id'] and not data['form']['location_id']:
            self.env.cr.execute(
                'SELECT s.product_id, p.name, sum(s.quantity) as quantity, count(s.product_id) as product_id_count FROM stock_quantity_history s JOIN product_template p ON p.id=s.product_template_id where s.date <= %s and type = %s group by s.product_id, p.name order by p.name',
                (data['form']['date'],'product'))

        # print(str(data['form']['category_id']) + ' ' + str(data['form']['location_id']))
        res = self.env.cr.dictfetchall()
        # print "res"
        # print res
        group_lines = {}
        for line in res:
            domain = [('date', '<=', data['form']['date']), ('product_id', '=', line['product_id'])]

            if data['form']['location_id'] and data['form']['location_id'][0]:
                domain.append(('location_id', '=', data['form']['location_id'][0]))
            # if data['form']['category_id'][0]:
            #     domain.append(('categ_id', '=', data['form']['category_id'][0]))

            print(domain)
            line['__domain'] = domain
            group_lines.setdefault(str(domain), stock_history_obj.search(domain))
            #print 'Test group_lines'
            #print group_lines

        line_ids = set()
        for ids in group_lines.values():
            for product_id in ids:
                line_ids.add(product_id.id)

        lines_rec = {}
        if line_ids:
            # print "line_ids"
            # print line_ids
            move_ids = tuple(abs(line_id) for line_id in line_ids)
            # print "move_ids"
            # print move_ids
            self.env.cr.execute('SELECT id, product_id, price_unit_on_quant, company_id, quantity FROM stock_quantity_history WHERE move_id in %s', (move_ids,))
            res_new = self.env.cr.dictfetchall()
            # print "res_new"
            # print res_new
            lines_rec = tuple(rec for rec in res_new if rec['id'] in line_ids)
        # print "lines_rec"
        # print lines_rec
        lines_dict = dict((line['id'], line) for line in lines_rec)
        # print "lines_dict"
        # print lines_dict
        product_ids = list(set(line_rec['product_id'] for line_rec in lines_rec))
        # print "product_ids"
        # print product_ids
        # products_rec = self.env['product.product'].read(product_ids, ['cost_method', 'id'])
        products_rec = self.env['product.product'].browse(product_ids).read(['cost_method', 'id'])
        # print "products_rec"
        # print products_rec
        products_dict = dict((product['id'], product) for product in products_rec)
        # print "products_dict"
        # print products_dict
        cost_method_product_ids = list(set(product['id'] for product in products_rec if product['cost_method'] != 'real'))
        histories = []
        if cost_method_product_ids:
            self.env.cr.execute('SELECT DISTINCT ON (product_id, company_id) product_id, company_id, cost FROM product_price_history WHERE product_id in %s AND datetime <= %s ORDER BY product_id, company_id, datetime DESC', (tuple(cost_method_product_ids), data['form']['date']))
            histories = self.env.cr.dictfetchall()
        histories_dict = {}
        for history in histories:
            histories_dict[(history['product_id'], history['company_id'])] = history['cost']
        for line in res:
            inv_value = 0.0
            lines = group_lines.get(str(line.get('__domain', domain)))
            #print lines
            for line_id in lines:
                # print line_id
                # print "lines_dict"
                # print lines_dict
                line_rec = lines_dict[line_id.id]
                # print "line_rec"
                # print line_rec
                product = products_dict[line_rec['product_id']]
                line['unit'] = self.env['product.product'].browse(line_rec['product_id']).uom_id.name
                if product['cost_method'] == 'real':
                    price = line_rec['price_unit_on_quant']
                else:
                    price = histories_dict.get((product['id'], line_rec['company_id']), 0.0)
                inv_value += price * line_rec['quantity']
            line['inventory_value'] = inv_value
            #print "len(RES)"
            #print len(res)
        return res

    def get_primary_details(self):
        res = {}
        res.update({'user': self.env.user.partner_id.name or '',
                    'company': self.env.user.company_id.name or '',
                    'vat': self.env.user.company_id.vat or ''})
        return res


    @api.multi
    def print_inventory_value_excel(self,data):
        print('print_inventory_value_excel')
        # print(data)
        # print(self.date)
        data = {}
        data['form'] = self.read(['date', 'location_id', 'category_id', 'product_code_form', 'product_code_to','account_id','report_type'])[0]
        # print(data)
        inventory = self.get_stock_value(data)
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
        for_center.num_format_str = '@'

        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

        for_left_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

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

        worksheet = workbook.add_sheet('stock')

        worksheet.col(0).width = 3000
        worksheet.col(1).width = 3000
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 3000
        worksheet.col(4).width = 3000
        worksheet.col(5).width = 3000
        worksheet.col(6).width = 3000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        today = datetime.today()
        total_qty = total_amount = 0
        if self.location_id:
            location_name = str(self.location_id.complete_name)#self.location_id.name
        else:
            location_name = "Warehouse"
        # print(location_name)
        if self.date:
            to_date = self.date
        else:
            to_date = str(datetime.today().date())
        worksheet.write_merge(0, 0, 0, 9, self.env.user.company_id.name, for_center_bold)
        worksheet.write_merge(1, 1, 0, 9, "รายละเอียดสินคาคงเหลือ", for_center_bold)
        worksheet.write_merge(2, 2, 0, 9, "ณ วันที่ " + strToDate(to_date).strftime("%d/%m/%Y"), for_center_bold)
        # worksheet.write_merge(3, 3, 0, 9, "คลังสินค้า " + str(location_name.encode('utf-8')), for_center_bold)#old code 03-09-2019
        worksheet.write_merge(3, 3, 0, 9, "คลังสินค้า " + str(location_name), for_center_bold)

        # worksheet.write_merge(5, 5, 0, 3, "ชื่อผูประกอบการ: " + str(self.env.user.company_id.name), for_left_bold)
        # worksheet.write_merge(5, 5, 4, 6, "เลขประจําตัวผูเสียภาษีอากร: " + str(self.env.user.company_id.vat), for_right_bold)
        # worksheet.write_merge(6, 6, 0, 3, "ชื่อสถานประกอบการ: " + str(self.env.user.company_id.name), for_left_bold)

        row = 5
        no = 0
        worksheet.write(row, 0, "ลำดับ", for_center_bold)
        worksheet.write(row, 1, 'รหัสสินค้า', for_center_bold)
        worksheet.write(row, 2, 'ชื่อสินค้า', for_center_bold)
        worksheet.write(row, 3, 'จำนวนหน่วย', for_center_bold)
        worksheet.write(row, 4, 'หน่วย', for_center_bold)
        worksheet.write(row, 5, 'ราคาต่อหน่วย', for_center_bold)
        worksheet.write(row, 6, 'จำนวนเงิน', for_center_bold)
        # book 0624
        # worksheet.write(row, 7, 'น้ำหนัก Unit of Measure', for_center_bold)
        # worksheet.write(row, 7, 'ราคาต่อหน่วย', for_center_bold)
        # worksheet.write(row, 8, 'จำนวนเงิน', for_center_bold)
        worksheet.write(row, 7,'Account', for_center_bold)
        worksheet.write(row, 8, 'Location', for_center_bold)
        worksheet.write(row, 9, 'หมายเหตุ', for_center_bold)
        worksheet.write(row, 10, 'ราคาขาย', for_center_bold)


        product_prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        count = count_qty = 0
        account_ids = []
        stock_account_ids = []

        if self.account_id:
            stock_account_ids.append(self.account_id.code)
        else:
            stock_account_ids = ['13-01-01-01','13-01-01-02','13-01-01-03','13-01-01-04','13-01-01-05','13-01-01-06']


        if self.is_show_location:
            for stock_account in stock_account_ids:
                sum_qty_by_account = sum_value_by_account = no = 0
                to_date = strToDate(self.date)

                record_ids = self.env['stock.record.yearly'].search([('date','=',str(to_date)),('account_id.code','=',stock_account)],order='product_id')
                if record_ids:
                    for product_inventory_line in record_ids:
                        row += 1
                        no += 1
                        value = product_inventory_line.value
                        sum_value_by_account += product_inventory_line.value
                        sum_qty_by_account += product_inventory_line.qty

                        total_qty += product_inventory_line.qty
                        product_id = product_inventory_line.product_id
                        worksheet.write(row, 0, no, for_left)
                        worksheet.write(row, 1, product_id.default_code, for_left)
                        worksheet.write(row, 2, product_id.name, for_left)

                        # book 0708
                        worksheet.write(row, 3, "{0:,.2f}".format(product_inventory_line.qty),for_right)
                        worksheet.write(row, 4, product_id.uom_id.name, for_left)
                        worksheet.write(row, 5, product_inventory_line.value / product_inventory_line.qty, for_right)
                        worksheet.write(row, 6, "{0:,.2f}".format(product_inventory_line.value), for_right)
                        worksheet.write(row, 7, stock_account, for_left)
                        worksheet.write(row, 8, product_inventory_line.location.name, for_left)
                        if product_id.is_extra_old:
                            worksheet.write(row, 9, 'ตั้งค่าเผื่อสินค้าล้าสมัย', for_left)

                        total_amount += round(value, 2)

                    if sum_qty_by_account:
                        row += 1
                        worksheet.write(row, 0, "รวม", for_center_bold)
                        worksheet.write(row, 3, "{0:,.2f}".format(sum_qty_by_account), for_right)
                        worksheet.write(row, 6, "{0:,.2f}".format(sum_value_by_account), for_right)
                else:
                    print ('amature')
                    for stock_account in stock_account_ids:
                        sum_qty_by_account = sum_value_by_account = no = 0
                        for product_inventory_line in inventory:
                            for location_inventory_line in product_inventory_line:
                                if product_inventory_line[location_inventory_line]['account'] != stock_account:
                                    continue
                                # print ('location LINE ACCOUNT', location_inventory_line)
                                # print ('location LINE ACCOUNT', product_inventory_line[location_inventory_line])

                                row += 1
                                no += 1
                                value = product_inventory_line[location_inventory_line]['qty'] * \
                                        product_inventory_line[location_inventory_line]['avg_price']
                                sum_value_by_account += product_inventory_line[location_inventory_line]['qty'] * \
                                                        product_inventory_line[location_inventory_line]['avg_price']
                                sum_qty_by_account += product_inventory_line[location_inventory_line]['qty']

                                total_qty += product_inventory_line[location_inventory_line]['qty']
                                product_id = self.env['product.product'].browse(
                                    product_inventory_line[location_inventory_line]['product_id'])
                                worksheet.write(row, 0, no, for_left)
                                worksheet.write(row, 1, product_id.default_code, for_left)
                                worksheet.write(row, 2, product_id.name, for_left)

                                # book 0708
                                worksheet.write(row, 3, "{0:,.2f}".format(
                                    product_inventory_line[location_inventory_line]['qty']), for_right)
                                worksheet.write(row, 4, product_inventory_line[location_inventory_line]['unit'],
                                                for_left)
                                if product_inventory_line[location_inventory_line]['qty'] != 0:
                                    worksheet.write(row, 5, "{0:,.2f}".format(
                                        product_inventory_line[location_inventory_line]['avg_price']), for_right)
                                else:
                                    worksheet.write(row, 5, '', for_right)
                                #
                                worksheet.write(row, 6, "{0:,.2f}".format(
                                    product_inventory_line[location_inventory_line]['avg_price'] *
                                    product_inventory_line[location_inventory_line]['qty']), for_right)
                                worksheet.write(row, 7, product_inventory_line[location_inventory_line]['account'],
                                                for_left)
                                location_id = self.env['stock.location'].browse(location_inventory_line)

                                if location_id:
                                    worksheet.write(row, 8, location_id.name, for_left)
                                else:
                                    worksheet.write(row, 8, "", for_left)

                                if product_id.is_extra_old:
                                    worksheet.write(row, 9, 'ตั้งค่าเผื่อสินค้าล้าสมัย', for_left)

                                # if product_id.is_extra_old:
                                worksheet.write(row, 10, product_id.lst_price, for_left)

                                total_amount += round(value, 2)
                        if sum_qty_by_account:
                            row += 1
                            worksheet.write(row, 0, "รวม", for_center_bold)
                            worksheet.write(row, 3, "{0:,.2f}".format(sum_qty_by_account), for_right)
                            worksheet.write(row, 6, "{0:,.2f}".format(sum_value_by_account), for_right)


        else:
            print ('XXXXX  NO SHow locaiton')
            for stock_account in stock_account_ids:
                sum_qty_by_account = sum_value_by_account = no = 0
                for product_inventory_line in inventory:
                    for location_inventory_line in product_inventory_line:
                        if product_inventory_line[location_inventory_line]['account'] != stock_account:
                            continue
                        # print ('location LINE ACCOUNT', location_inventory_line)
                        # print ('location LINE ACCOUNT', product_inventory_line[location_inventory_line])

                        row += 1
                        no += 1
                        value = product_inventory_line[location_inventory_line]['qty'] * product_inventory_line[location_inventory_line]['avg_price']
                        sum_value_by_account += product_inventory_line[location_inventory_line]['qty'] * product_inventory_line[location_inventory_line]['avg_price']
                        sum_qty_by_account += product_inventory_line[location_inventory_line]['qty']

                        total_qty += product_inventory_line[location_inventory_line]['qty']
                        product_id = self.env['product.product'].browse(product_inventory_line[location_inventory_line]['product_id'])
                        worksheet.write(row, 0, no, for_left)
                        worksheet.write(row, 1, product_id.default_code, for_left)
                        worksheet.write(row, 2, product_id.name, for_left)

                        # book 0708
                        worksheet.write(row, 3, "{0:,.2f}".format(product_inventory_line[location_inventory_line]['qty']), for_right)
                        worksheet.write(row, 4, product_inventory_line[location_inventory_line]['unit'], for_left)
                        if product_inventory_line[location_inventory_line]['qty'] != 0:
                            worksheet.write(row, 5, "{0:,.2f}".format(product_inventory_line[location_inventory_line]['avg_price']), for_right)
                        else:
                            worksheet.write(row, 5, '', for_right)
                        #
                        worksheet.write(row, 6, "{0:,.2f}".format(product_inventory_line[location_inventory_line]['avg_price'] * product_inventory_line[location_inventory_line]['qty']), for_right)
                        worksheet.write(row, 7, product_inventory_line[location_inventory_line]['account'], for_left)
                        location_id = self.env['stock.location'].browse(location_inventory_line)

                        if location_id:
                            worksheet.write(row, 8, location_id.name, for_left)
                        else:
                            worksheet.write(row, 8, "", for_left)

                        if product_id.is_extra_old:
                            worksheet.write(row, 9, 'ตั้งค่าเผื่อสินค้าล้าสมัย', for_left)

                        worksheet.write(row, 10, product_id.lst_price, for_left)

                        total_amount += round(value, 2)
                if sum_qty_by_account:
                    row += 1
                    worksheet.write(row, 0, "รวม", for_center_bold)
                    worksheet.write(row, 3, "{0:,.2f}".format(sum_qty_by_account), for_right)
                    worksheet.write(row, 6, "{0:,.2f}".format(sum_value_by_account), for_right)

        row += 2
        worksheet.write(row, 3, "{0:,.2f}".format(total_qty), for_left)
        worksheet.write(row, 6, "{0:,.2f}".format(total_amount), for_left)
        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE stock_inventory_export CASCADE")
        wizard_id = self.env['stock.inventory.export'].create(
            vals={'name': 'Stock Report.xls', 'report_file': ctx['report_file']})
        # print wizard_id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.inventory.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

    # @api.multi
    # def open_table_bottom(self):
    #     print 'open_table_bottom 111'
    #     self.ensure_one()
    #     ctx = dict(
    #         self._context,
    #         history_date=self.date,
    #         location_id=self.location_id.id,
    #         category_id=self.category_id.id,
    #         search_default_group_by_product=True,
    #         search_default_group_by_location=True)
    #
    #     print 'open_table_bottom 222'
    #     print self.location_id.id
    #     print self.category_id.id
    #     action = self.env['ir.model.data'].xmlid_to_object('stock_account.action_stock_history')
    #     print action
    #     if not action:
    #         print 'open_table_bottom 333'
    #         action = {
    #             'view_type': 'form',
    #             'view_mode': 'tree,graph,pivot',
    #             'res_model': 'stock.history',
    #             'type': 'ir.actions.act_window',
    #         }
    #     else:
    #         print 'open_table_bottom 444'
    #         action = action[0].read()[0]
    #
    #     print 'open_table_bottom 555'
    #     action['domain'] = "[('date', '<=', '" + self.date + "')]"
    #     action['domain1'] = [('location_id', '=', self.location_id.id), ('category_id', '=', self.category_id.id)]
    #     action['name'] = _('Stock Value At Date')
    #     action['context'] = ctx
    #     print action['domain']
    #     print action['domain1']
    #     return action
