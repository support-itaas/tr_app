# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockInventoryValuationView(models.TransientModel):
    _name = 'stock.inventory.valuation.view'
    _description = 'Stock Inventory Valuation View'

    display_name = fields.Char()
    qty_at_date = fields.Float()
    code = fields.Char()
    uom_id = fields.Many2one(
        comodel_name='product.uom',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    cost_currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    lot = fields.Char(string='LOT')
    standard_price = fields.Float()
    stock_value = fields.Float()
    cost_method = fields.Char()
    location_name = fields.Char()



class StockInventoryValuationReport(models.TransientModel):
    _name = 'report.stock.inventory.valuation.report'
    _description = 'Stock Inventory Valuation Report'

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    compute_at_date = fields.Integer()
    date = fields.Datetime()
    ############ add by JA - 11/10/2020###########
    location_id = fields.Many2one('stock.location', string='Stock Location')
    category_id = fields.Many2one('product.category', string='Product Category')
    is_split_location = fields.Boolean(string='Split Location')
    is_show_cost = fields.Boolean(string='Show Cost')
    is_show_lot = fields.Boolean(string='Show LOT')

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='stock.inventory.valuation.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def get_product_lot_location_date(self,product_id,location_id,date):
        result = []
        # location_ids = []
        # location_ids.append(location_id)
        location_ids = self.env['stock.location'].search([('id', 'child_of', [location_id])])

        params = (date, tuple(location_ids.ids), tuple(location_ids.ids),product_id)

        query = """SELECT distinct(lot_id) FROM stock_move_line AS sml
                                               WHERE sml.state = 'done' and sml.date <= %s and (sml.location_id in %s or sml.location_dest_id in %s) and sml.product_id = %s"""

        self.env.cr.execute(query, params)
        res = self.env.cr.fetchall()
        for lot in res:
            print ('LOT',lot[0])
            params = (tuple(location_ids.ids), tuple(location_ids.ids), tuple(location_ids.ids), tuple(location_ids.ids), product_id, lot[0], date,)
            query = """SELECT
                            case when move.location_dest_id in %s then move.qty_done end as product_in,
                            case when move.location_id in %s then move.qty_done end as product_out,
                            move.id
                      FROM stock_move_line move
                      WHERE (move.location_id in %s or move.location_dest_id in %s)
                            and move.state = 'done' and move.product_id = %s
                            and move.lot_id = %s
                            and CAST(move.date AS date) <= %s
                      ORDER BY move.date
                    """
            self.env.cr.execute(query, params)
            res = self.env.cr.fetchall()
            qty = 0
            value = 0
            for line in res:
                if line[0]:
                    qty += line[0]
                    if self.env['stock.move.line'].browse(line[2]).location_id.usage == 'internal':
                        if lot[0]:
                            move_line_id = self.env['stock.move.line'].search([('lot_id','=',lot[0]),('location_dest_id.usage','=','internal'),('id','<',line[2]),('location_id.usage','!=','internal')],order='date desc',limit=1)
                            if move_line_id:
                                value += abs(move_line_id.move_id.price_unit) * line[0]
                            else:
                                value += abs(product_id.standard_price) * line[0]
                        else: #no lot
                            move_line_id = self.env['stock.move.line'].search(
                                [('location_dest_id.usage', '=', 'internal'),
                                 ('id', '<', line[2]), ('location_id.usage', '!=', 'internal')], order='date desc',
                                limit=1)
                            if move_line_id:
                                value += abs(move_line_id.move_id.price_unit) * line[0]
                            else:
                                value += abs(self.env['product.product'].browse(product_id).price_unir) * line[0]
                    else:
                        value += self.env['stock.move.line'].browse(line[2]).move_id.price_unit * line[0]
                if line[1]:
                    qty -= line[1]
                    if self.env['stock.move.line'].browse(line[2]).location_dest_id.usage == 'internal':
                        if lot[0]:
                            move_line_id = self.env['stock.move.line'].search([('lot_id','=',lot[0]),('location_dest_id','=',location_id),('id','<',line[2]),('location_id.usage','!=','internal')],order='date desc',limit=1)
                            if move_line_id:
                                value -= abs(move_line_id.move_id.price_unit) * line[1]
                            else:
                                value -= abs(self.env['product.product'].browse(product_id).standard_price) * line[1]
                        else: #no lot
                            move_line_id = self.env['stock.move.line'].search(
                                [('location_dest_id', '=', location_id.id),
                                 ('id', '<', line[2]), ('location_id.usage', '!=', 'internal')], order='date desc',
                                limit=1)
                            if move_line_id:
                                value -= abs(move_line_id.move_id.price_unit) * line[1]
                            else:
                                value -= abs(self.env['product.product'].browse(product_id).standard_price) * line[1]
                    else:
                        value -= abs(self.env['stock.move.line'].browse(line[2]).move_id.price_unit) * line[1]
            val = {
                'lot_id': self.env['stock.production.lot'].browse(lot[0]).name,
                'qty': qty,
                'value': value,
            }
            result.append(val)
        # print (result)
        return result


    @api.multi
    def _compute_results(self):
        self.ensure_one()
        ReportLine = self.env['stock.inventory.valuation.view']
        if not self.compute_at_date:
            self.date = fields.Datetime.now()
        ##########Original ############
        # products = self.env['product.product'].\
        #     search([('type', '=', 'product'), ('qty_available', '!=', 0)]).\
        #     with_context(dict(to_date=self.date, company_owned=True,
        #                       create=False, edit=False))
        # print ('-update--')
        # print (self.date)
        # print (self.location_id)
        ########New by JA - 11/10/2020 ################### get location if not specific and need to split #########
        if self.location_id:
            location_ids = self.location_id
        elif not self.location_id and self.is_split_location:
            location_ids = self.env['stock.location'].search(
                [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])])
        else:
            location_ids = False
        #####################################################
        if location_ids:
            # print ('location_ids',location_ids)
            for location_id in location_ids:
                # if self.category_id:
                #     products = self.env['product.product']. \
                #         search([('type', '=', 'product'), ('categ_id', 'child_of', self.category_id.id)]). \
                #         with_context(dict(to_date=self.date, company_owned=True,
                #                           create=False, edit=False, location=location_id.id))
                # else:
                #     products = self.env['product.product']. \
                #         search([('type', '=', 'product')]). \
                #         with_context(dict(to_date=self.date,
                #                           create=False, edit=False, location=location_id.id))

                params = (self.date, tuple(location_ids.ids), tuple(location_ids.ids))
                query = """SELECT distinct(product_id) FROM stock_move_line AS sml
                                                               WHERE sml.state = 'done' and sml.date <= %s and (sml.location_id in %s or sml.location_dest_id in %s)"""
                self.env.cr.execute(query, params)
                res = self.env.cr.fetchall()
                # print ('RES',res)
                product_ids = []
                # count = 0
                for product in res:
                    # count+=1
                    product_ids.append(product[0])
                    # if count > 5:
                    #     break

                products = self.env['product.product'].browse(product_ids)

                if self.category_id:
                    products = products.filtered(lambda x: x.categ_id == self.category_id and x.type == 'product' and x.active)
                else:
                    products = products.filtered(lambda x: x.type == 'product' and x.active)

                for product in products:
                    print ('Product',product.default_code)
                    # print (product.default_code)
                    # params = (self.date, tuple(location_ids.ids), tuple(location_ids.ids),product.id)



                    # query = """SELECT sum(move.product_uom_qty), sum(move.value) FROM stock_move AS move
                    #                                                                WHERE move.state = 'done' and move.date <= %s and (move.location_id in %s or move.location_dest_id in %s) and move.product_id = %s"""
                    # query = """SELECT move.product_uom_qty, move.value FROM stock_move AS move WHERE move.state = 'done' and move.date <= %s and (move.location_id in %s or move.location_dest_id in %s) and move.product_id = %s"""



                    if self.is_show_lot:
                        print ('---SHOW LOT----')
                        lot_ids = self.get_product_lot_location_date(product.id, location_id.id, self.date)
                        # print ('LOT IDS',lot_ids)
                        if len(lot_ids) > 0:
                            for lot in lot_ids:
                                # print ('lot',lot)
                                line = {
                                    'display_name': product.display_name,
                                    'code': product.default_code,
                                    'qty_at_date': lot['qty'],
                                    'uom_id': product.uom_id,
                                    'currency_id': product.currency_id,
                                    'cost_currency_id': product.cost_currency_id,
                                    'standard_price': lot['value']/lot['qty'] if lot['qty'] else 0,
                                    'stock_value': lot['value'],
                                    'cost_method': product.cost_method,
                                    'location_name': location_id.display_name,
                                    'lot': lot['lot_id'],
                                }
                                if lot['qty'] > 0:
                                    self.results += ReportLine.new(line)
                        else:
                            params = (tuple(location_ids.ids), tuple(location_ids.ids), tuple(location_ids.ids),
                                      tuple(location_ids.ids), product.id, self.date,)
                            query = """SELECT
                                                                            case when move.location_dest_id in %s then move.qty_done end as product_in,
                                                                            case when move.location_id in %s then move.qty_done end as product_out,
                                                                            move.id
                                                                      FROM stock_move_line move
                                                                      WHERE (move.location_id in %s or move.location_dest_id in %s)
                                                                            and move.state = 'done' and move.product_id = %s
                                                                            and CAST(move.date AS date) <= %s
                                                                      ORDER BY move.date
                                                                    """
                            self.env.cr.execute(query, params)
                            res = self.env.cr.fetchall()
                            qty = 0
                            value = 0
                            for line in res:
                                if line[0]:
                                    qty += line[0]
                                    if self.env['stock.move.line'].browse(line[2]).location_id.usage == 'internal':
                                        move_line_id = self.env['stock.move.line'].search(
                                            [('location_dest_id.usage', '=', 'internal'),
                                             ('id', '<', line[2]), ('move_id.value', '>', 0),('state', '=', 'done'),('location_id.usage', '!=', 'internal')],
                                            order='date desc', limit=1)
                                        if move_line_id:
                                            value += abs(move_line_id.move_id.price_unit) * line[0]
                                        else:
                                            value += abs(product.standard_price) * line[0]
                                    else:
                                        value += self.env['stock.move.line'].browse(line[2]).move_id.price_unit * line[
                                            0]
                                if line[1]:
                                    qty -= line[1]
                                    if self.env['stock.move.line'].browse(line[2]).location_dest_id.usage == 'internal':
                                        move_line_id = self.env['stock.move.line'].search(
                                            [('location_dest_id', '=', location_id),
                                             ('id', '<', line[2]), ('move_id.value', '>', 0),('state', '=', 'done'),('location_id.usage', '!=', 'internal')],
                                            order='date desc', limit=1)
                                        if move_line_id:
                                            value -= abs(move_line_id.move_id.price_unit) * line[1]
                                        else:
                                            value -= abs(product.standard_price) * line[1]
                                    else:
                                        value -= abs(self.env['stock.move.line'].browse(line[2]).move_id.price_unit) * \
                                                 line[1]

                            line = {
                                'display_name': product.display_name,
                                'code': product.default_code,
                                'qty_at_date': qty,
                                'uom_id': product.uom_id,
                                'currency_id': product.currency_id,
                                'cost_currency_id': product.cost_currency_id,
                                'standard_price': value/qty if qty else 0,
                                'stock_value': value,
                                'cost_method': product.cost_method,
                                'location_name': location_id.display_name,
                            }
                            if qty > 0:
                                self.results += ReportLine.new(line)

                    else:
                        print ('NOT SHOW LOT')
                        params = (tuple(location_ids.ids), tuple(location_ids.ids), tuple(location_ids.ids),
                                  tuple(location_ids.ids), product.id, self.date,)
                        query = """SELECT case when move.location_dest_id in %s then move.qty_done end as product_in,
                                          case when move.location_id in %s then move.qty_done end as product_out,
                                          move.id
                                          FROM stock_move_line move WHERE (move.location_id in %s or move.location_dest_id in %s)
                                          and move.state = 'done' and move.product_id = %s and CAST(move.date AS date) <= %s ORDER BY move.date
                                                                                            """
                        self.env.cr.execute(query, params)
                        res = self.env.cr.fetchall()
                        qty = 0
                        value = 0
                        for line in res:
                            if line[0]:
                                qty += line[0]

                                if self.env['stock.move.line'].browse(line[2]).location_id.usage == 'internal':
                                    print ('INTERNAL Trasner')
                                    move_line_id = self.env['stock.move.line'].search(
                                        [('location_dest_id.usage', '=', 'internal'),
                                         ('id', '<', line[2]),('move_id.value', '>', 0),('state', '=', 'done'), ('location_id.usage', '!=', 'internal')],
                                        order='date desc', limit=1)

                                    print ('MOVE LINE ID',move_line_id)
                                    if move_line_id:
                                        value += abs(move_line_id.move_id.price_unit) * line[0]
                                    else:
                                        value += abs(product.standard_price) * line[0]
                                else:
                                    value += self.env['stock.move.line'].browse(line[2]).move_id.price_unit * line[0]
                            if line[1]:
                                qty -= line[1]
                                if self.env['stock.move.line'].browse(line[2]).location_dest_id.usage == 'internal':
                                    #find value
                                    move_line_id = self.env['stock.move.line'].search(
                                        [('location_dest_id', '=', location_id),
                                         ('id', '<', line[2]), ('move_id.value', '>', 0),('state', '=', 'done'),('location_id.usage', '!=', 'internal')],
                                        order='date desc', limit=1)
                                    if move_line_id:
                                        value -= abs(move_line_id.move_id.price_unit) * line[1]
                                    else:
                                        value -= abs(product.standard_price) * line[1]
                                else:
                                    value -= abs(self.env['stock.move.line'].browse(line[2]).move_id.price_unit) * \
                                             line[1]

                        line = {
                            'display_name': product.display_name,
                            'code': product.default_code,
                            'qty_at_date': qty,
                            'uom_id': product.uom_id,
                            'currency_id': product.currency_id,
                            'cost_currency_id': product.cost_currency_id,
                            'standard_price': value / qty if qty else 0,
                            'stock_value': value,
                            'cost_method': product.cost_method,
                            'location_name': location_id.display_name,
                        }
                        if qty > 0:
                            self.results += ReportLine.new(line)

        else:
            # products = self.env['product.product']. \
            #     search([('type', '=', 'product')]). \
            #     with_context(dict(to_date=self.date, company_owned=True,
            #                       create=False, edit=False))
            params = (self.date,)
            query = """SELECT distinct(product_id) FROM stock_move_line AS sml
                                                                           WHERE sml.state = 'done' and sml.date <= %s"""
            self.env.cr.execute(query, params)
            res = self.env.cr.fetchall()
            # print ('RES',res)
            product_ids = []
            # count = 0
            for product in res:
                # count += 1
                product_ids.append(product[0])
                # if count > 5:
                #     break

            products = self.env['product.product'].browse(product_ids)
            if self.category_id:
                products = products.filtered(lambda x: x.categ_id == self.categ_id.id and x.type == 'product' and x.active)
            else:
                products = products.filtered(lambda x: x.type == 'product' and x.active)

            ########New by JA - 11/10/2020 ###################
            for product in products:
                line = {
                    'display_name': product.display_name,
                    'code': product.default_code,
                    'qty_at_date': product.qty_at_date,
                    'uom_id': product.uom_id,
                    'currency_id': product.currency_id,
                    'cost_currency_id': product.cost_currency_id,
                    'standard_price': product.stock_value/product.qty_at_date if product.qty_at_date else 0,
                    'stock_value': product.stock_value,
                    'cost_method': product.cost_method,
                    'location_name': "All",
                }

                if product.qty_at_date != 0:
                    self.results += ReportLine.new(line)

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref(
            'stock_inventory_valuation_report.'
            'action_stock_inventory_valuation_report_xlsx') or \
            self.env.ref('stock_inventory_valuation_report.'
                         'action_stock_inventory_valuation_report_pdf')
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'stock_inventory_valuation_report.'
                'report_stock_inventory_valuation_report_html').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
