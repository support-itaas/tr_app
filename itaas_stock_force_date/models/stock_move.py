# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()
        # print ('COST')
        # print (cost)
        print ('_prepare_account_move_line==FORCE_DATE')
        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            valuation_amount = cost

        # print ('VALUEATION AMOUNT')
        # print (valuation_amount)

        if self._context.get('forced_ref'):
            ref = self._context['forced_ref']
        else:
            ref = self.picking_id.name

        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount)

        if self.company_id.currency_id.is_zero(debit_value):
            # check that all data is correct
            #############REMOVE To allow zero cost can record, this is case of getting something free
            # if self.company_id.currency_id.is_zero(debit_value):
            #     raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (self.product_id.display_name,))
            #############
            credit_value = debit_value

            partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
            debit_line_vals = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'debit': debit_value if debit_value > 0 else 0,
                'credit': -debit_value if debit_value < 0 else 0,
                'account_id': debit_account_id,
            }
            credit_line_vals = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'credit': credit_value if credit_value > 0 else 0,
                'debit': -credit_value if credit_value < 0 else 0,
                'account_id': credit_account_id,
            }
            res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
            if credit_value != debit_value:
                # for supplier returns of product in average costing method, in anglo saxon mode
                diff_amount = debit_value - credit_value
                price_diff_account = self.product_id.property_account_creditor_price_difference
                if not price_diff_account:
                    price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
                if not price_diff_account:
                    raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
                price_diff_line = {
                    'name': self.name,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'ref': ref,
                    'partner_id': partner_id,
                    'credit': diff_amount > 0 and diff_amount or 0,
                    'debit': diff_amount < 0 and -diff_amount or 0,
                    'account_id': price_diff_account.id,
                }
                res.append((0, 0, price_diff_line))
            return res
        else:
            res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            return res

    def _action_done(self):
        print ('-----_action_done by itaas stock move force date----')
        res = super(StockMove, self)._action_done()
        params = self._context.get('params')

        print (params)
        for move in self:
            if params and 'force_date' in params:
                res.write({'date': params.get('force_date')})
            if move.picking_id.force_date:
                res.write({'date': move.picking_id.force_date})
        print ('------END-by itaas stock forece date---')
        return res

    # def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
    #     print ('ORIGINAL--_create_account_move_line')
    #     self.ensure_one()
    #     AccountMove = self.env['account.move']
    #     quantity = self.env.context.get('forced_quantity', self.product_qty)
    #     quantity = quantity if self._is_in() else -1 * quantity
    #
    #     # Make an informative `ref` on the created account move to differentiate between classic
    #     # movements, vacuum and edition of past moves.
    #     ref = self.picking_id.name
    #     if self.env.context.get('force_valuation_amount'):
    #         if self.env.context.get('forced_quantity') == 0:
    #             ref = 'Revaluation of %s (negative inventory)' % ref
    #         elif self.env.context.get('forced_quantity') is not None:
    #             ref = 'Correction of %s (modification of past move)' % ref
    #
    #     move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value), credit_account_id, debit_account_id)
    #     if move_lines:
    #         date = self._context.get('force_period_date', fields.Date.context_today(self))
    #         new_account_move = AccountMove.sudo().create({
    #             'journal_id': journal_id,
    #             'line_ids': move_lines,
    #             'date': date,
    #             'ref': ref,
    #             'stock_move_id': self.id,
    #         })
    #         new_account_move.post()

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        # print ('JOURNAL',journal_id.company_id)
        params = self._context.get('params')
        print ('_create_account_move_line for stock force date')
        # print (params)
        if self.picking_id.force_date or 'force_date' in params:
            if self.picking_id.force_date:
                force_date = self.picking_id.force_date
            if params and 'force_date' in params:
                force_date = params.get('force_date')
            self.ensure_one()
            AccountMove = self.env['account.move']
            quantity = self.env.context.get('forced_quantity', self.product_qty)
            quantity = quantity if self._is_in() else -1 * quantity

            # Make an informative `ref` on the created account move to differentiate between classic
            # movements, vacuum and edition of past moves.
            ref = self.picking_id.name
            if self.env.context.get('force_valuation_amount'):
                if self.env.context.get('forced_quantity') == 0:
                    ref = 'Revaluation of %s (negative inventory)' % ref
                elif self.env.context.get('forced_quantity') is not None:
                    ref = 'Correction of %s (modification of past move)' % ref

            move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                      credit_account_id,
                                                                                      debit_account_id)
            print ('FORCE DATE')
            print(move_lines)
            if move_lines:
                # force_date = False
                print('force_date ',force_date)
                print('datetime.today() ',fields.Datetime.now())
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': force_date or fields.Datetime.now(),
                    'ref': ref,
                    'stock_move_id': self.id,
                    'company_id': self.env['account.journal'].browse(journal_id).company_id.id,
                })
                # print ('company',self.env['account.journal'].browse(journal_id).company_id.id)
                #
                # print ('New move id',new_account_move.company_id.id)
                new_account_move.post()
        else:
            #some issue for company does not apply for odoo standard function, replace here note by JA 16/02/2022
            # super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)
            self.ensure_one()
            AccountMove = self.env['account.move']
            quantity = self.env.context.get('forced_quantity', self.product_qty)
            quantity = quantity if self._is_in() else -1 * quantity

            # Make an informative `ref` on the created account move to differentiate between classic
            # movements, vacuum and edition of past moves.
            ref = self.picking_id.name
            if self.env.context.get('force_valuation_amount'):
                if self.env.context.get('forced_quantity') == 0:
                    ref = 'Revaluation of %s (negative inventory)' % ref
                elif self.env.context.get('forced_quantity') is not None:
                    ref = 'Correction of %s (modification of past move)' % ref

            move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                      credit_account_id,
                                                                                      debit_account_id)
            if move_lines:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': ref,
                    'stock_move_id': self.id,
                    'company_id': self.env['account.journal'].browse(journal_id).company_id.id,
                })
                new_account_move.post()
