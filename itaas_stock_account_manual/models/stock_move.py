# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class StockMove(models.Model):
    _inherit = 'stock.move'

    def cost_from_bill(self,bill_id):
        cost = 0

        if bill_id and bill_id.invoice_line_ids.filtered(lambda m: m.product_id.id == self.product_id.id):
            line_id = bill_id.invoice_line_ids.filtered(lambda m: m.product_id.id == self.product_id.id)
            if line_id.invoice_line_tax_ids and line_id.invoice_line_tax_ids[0].price_include:
                cost = line_id.price_unit / 1.07
            else:
                cost = line_id.price_unit
            return cost
        return cost

    #update cost after get vendor bill
    def _get_price_unit(self):
        # print ('_get_price_unit')
        # print ('self.picking_id.origin',self.picking_id.origin)
        # print ('bill_id',self.picking_id.bill_id)
        if self.purchase_line_id and self.purchase_line_id.invoice_lines and len(self.purchase_line_id.invoice_lines) == 1:
            self.price_unit = self.purchase_line_id.invoice_lines.price_unit
            return self.purchase_line_id.invoice_lines.price_unit
        elif not self.purchase_line_id and self.picking_id and self.picking_id.bill_id and self.cost_from_bill(self.picking_id.bill_id):
            # print (xx)
            return self.cost_from_bill(self.picking_id.bill_id)
        else:
            return super(StockMove, self)._get_price_unit()

    def get_analytic_account_id(self):
        analytic_account_id = False
        for move in self:
            pos_config_id = self.env['pos.config'].search([('stock_location_id','=',self.location_id.id)],limit=1)
            if pos_config_id and pos_config_id.branch_id and pos_config_id.branch_id.analytic_account_id:
                analytic_account_id = pos_config_id.branch_id.analytic_account_id
        return analytic_account_id

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove,self)._prepare_account_move_line(qty,cost,credit_account_id,debit_account_id)

        # print ('_prepare_account_move_line', res)
        print ('_prepare_account_move_line==stock account manual')
        analytic_account_id = self.get_analytic_account_id()
        # print(analytic_account_id)
        for line in res:
            if line[2]['debit'] > 0 and analytic_account_id:
                line[2]['analytic_account_id'] = analytic_account_id.id
        print ('RES',res)
        return res

    def get_average_price_unit(self):
        for move in self:
            all_value = 0
            all_qty = 0
            stock_move_before_ids = self.env['stock.move'].search([('state','=','done'),('date','<',move.date),('product_id','=',move.product_id.id)])
            for stock_move in stock_move_before_ids:
                if stock_move._is_in():
                    all_qty += stock_move.product_uom_qty
                    all_value += stock_move.value
                elif stock_move._is_out():
                    all_qty += stock_move.product_uom_qty *(-1)
                    all_value += stock_move.value

            # print (move.id)
            # print(move.price_unit)
            # print (all_value)
            # print (all_qty)
            if move._is_in() or move._is_out():
                if all_qty:
                    new_standard_price = all_value/all_qty
                else:
                    new_standard_price = move.price_unit
            else:
                new_standard_price = move.product_id.standard_price
            # print (new_standard_price)
            # print ('---------')
            if move._is_out():
                move.update({'price_unit': new_standard_price * (-1)})
                move.update({'value': move.product_uom_qty * move.price_unit})
            # elif move._is_in()
            move.product_id.sudo().with_context(force_company=move.company_id.id) \
                .standard_price = new_standard_price
            move._set_standard_price_from_move(new_standard_price,move.date,move.product_id)

    @api.multi
    def _set_standard_price_from_move(self, value,date,product_id):
        ''' Store the standard price change in order to be able to retrieve the cost of a product for a given date'''
        PriceHistory = self.env['product.price.history']
        history_id = PriceHistory.create({
            'datetime':date,
            'product_id': product_id.id,
            'cost': value,
            'company_id': self._context.get('force_company', self.env.user.company_id.id),
        })
        print (history_id.datetime)

    def update_accounting_entry(self):
        for move in self.filtered(lambda m: m.product_id.valuation == 'real_time' and m._is_out()):
            # move.get_average_price_unit()
            # move.update({'value': move.product_uom_qty * move.price_unit})
            if move.account_move_ids:
                move.account_move_ids.button_cancel()
                move.account_move_ids.unlink()
            move.with_context(force_period_date=move.date + relativedelta(hours=+7))._account_entry_move()


    def update_cost(self):
        print ('---1-update-cost')
        for move in self:
            if move.account_move_ids:
                move.account_move_ids.button_cancel()
                move.account_move_ids.unlink()

            #update price unit cost
            move._get_price_unit()

            if move._is_in() and move._is_out():
                raise UserError(_(
                    "The move lines are not in a consistent state: some are entering and other are leaving the company."))
            company_src = move.mapped('move_line_ids.location_id.company_id')
            company_dst = move.mapped('move_line_ids.location_dest_id.company_id')

            try:
                if company_src:
                    company_src.ensure_one()
                if company_dst:
                    company_dst.ensure_one()
            except ValueError:
                raise UserError(_(
                    "The move lines are not in a consistent states: they do not share the same origin or destination company."))
            if company_src and company_dst and company_src.id != company_dst.id:
                raise UserError(_(
                    "The move lines are not in a consistent states: they are doing an intercompany in a single step while they should go through the intercompany transit location."))
            move._run_valuation()

        for move in self.filtered(lambda m: m.product_id.valuation == 'real_time' and (m._is_in() or m._is_out() or m._is_dropshipped() or m._is_dropshipped_returned())):
            # print ('---UPDATE COST')
            move.with_context(force_period_date=strToDate(move.date) + relativedelta(hours=+7))._account_entry_move()
            move.account_move_ids.update({'date': move.date})

    def action_delete_gl(self):
        print ('---1-update-cost')
        for move in self:
            if move.account_move_ids:
                move.account_move_ids.button_cancel()
                move.account_move_ids.unlink()


class stock_move_advance(models.TransientModel):
    _name = "stock.move.advance"


    def action_confirm(self):
        context = self._context
        # if context.get('active_model') == 'res.partner' and context.get('active_ids'):
        stock_move_ids = self.env['stock.move'].browse(context['active_ids'])
        for stock_move in stock_move_ids:
            stock_move.update_cost()

    def action_delete_gl(self):
        context = self._context
        stock_move_ids = self.env['stock.move'].browse(context['active_ids'])
        for stock_move in stock_move_ids:
            stock_move.action_delete_gl()


    def update_unit_cost(self):
        context = self._context
        # if context.get('active_model') == 'res.partner' and context.get('active_ids'):
        stock_move_ids = self.env['stock.move'].browse(context['active_ids'])
        for stock_move in stock_move_ids:
            stock_move.account_move_ids.update({'date': stock_move.date})
            # stock_move.get_average_price_unit()
            # stock_move.update_accounting_entry()
