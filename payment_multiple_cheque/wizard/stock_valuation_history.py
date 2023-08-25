# -*- coding: utf-8 -*-


from datetime import datetime
from odoo import tools
# from odoo import api, fields, models, _
from odoo.tools.translate import _
from odoo import api, models, fields, _

class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'


    location_id = fields.Many2one('stock.location', string='Stock Location')
    category_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product')


    def print_inventory_value(self, data):
        data = {}
        data['form'] = self.read(['date', 'location_id', 'category_id'])[0]
        # return self.env['report'].get_action(self, 'stock_extended.report_stockhistory_id', data=data)

        return self.env.ref('stock_extended.action_report_stock_history').report_action(self, data=data, config=False)

    @api.multi
    def get_stock_value(self,data):
        result = {}
        StockMove = self.env['stock.move']
        to_date = data['form']['date']

        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        domain = [('type','=','product')]
        if data['form']['category_id']:
            domain.append(('category_id','=',data['form']['category_id'][0]))

        product_ids = self.env['product.product'].search(domain)
        for product in product_ids:
            stock_qty = 0.00
            stock_value = 0.00

            if to_date:
                price_used = product.get_history_price(
                    self.env.user.company_id.id,
                    date=to_date,
                ) if product.cost_method in ['standard', 'average'] else 0.0
                if product.product_tmpl_id.valuation == 'manual_periodic':
                    domain = [('product_id', '=', product.id),
                              ('date', '<=', to_date)] + StockMove._get_all_base_domain()
                    moves = StockMove.search(domain)
                    stock_qty = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.cost_method == 'fifo':
                        stock_value = sum(moves.mapped('value'))
                        # product.stock_fifo_manual_move_ids = StockMove.browse(moves.ids)
                    elif product.cost_method in ['standard', 'average']:
                        stock_value = product.qty_at_date * price_used
                elif product.product_tmpl_id.valuation == 'real_time':
                    valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                    value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                    0, 0, [])
                    stock_qty = quantity
                    if product.cost_method == 'fifo':
                        stock_value = value
                        # product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                    elif product.cost_method in ['standard', 'average']:
                        stock_value = quantity * price_used

            else:
                if product.product_tmpl_id.valuation == 'manual_periodic':
                    stock_qty = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.cost_method == 'fifo':
                        stock_value, product.stock_fifo_manual_move_ids = product._sum_remaining_values()
                    elif product.cost_method in ['standard', 'average']:
                        stock_value = product.qty_at_date * product.standard_price
                elif product.product_tmpl_id.valuation == 'real_time':
                    valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                    value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                    0, 0, [])
                    stock_qty = quantity
                    if product.cost_method == 'fifo':
                        stock_value = value
                        # product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                    elif product.cost_method in ['standard', 'average']:
                        stock_value = quantity * product.standard_price

            result[product.id] = {
                'name': product.name,
                'unit': product.uom_id.name,
                'qty': stock_qty,
                'value': stock_value,
            }
        result = [value for key, value in result.items()]

        return result

    def get_inventory(self, data):
        # print data
        # print data['form']['date']
        # print data['form']['location_id'][0]

        #query#
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

            # print domain
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
