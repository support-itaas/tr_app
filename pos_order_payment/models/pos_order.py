# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    # is_not_post = fields.Boolean(string='ไม่เอาไปนำฝาก', related='pos_statement_id.is_not_post',store=True)

    is_not_post = fields.Boolean(string='ไม่เอาไปนำฝาก', related=False, compute='get_post_status',store=True)

    @api.depends('pos_statement_id', 'journal_id','journal_id.is_bank_post')
    def get_post_status(self):
        for statement_id in self:
            # print ('get_post_status----')
            # print (statement_id.pos_statement_id.is_not_post)
            # print (statement_id.journal_id.is_bank_post)
            if statement_id.pos_statement_id and statement_id.pos_statement_id.is_not_post:
                # statement_id.write({'is_not_post': True})
                statement_id.is_not_post = True
            elif statement_id.journal_id and not statement_id.journal_id.is_bank_post:
                # print ('JOURNAL NOT POST')
                # print (statement_id.journal_id.name)
                statement_id.is_not_post = True
            else:
                statement_id.is_not_post = False
                # print ('ELSE--')


class POSOrder(models.Model):
    _inherit = 'pos.order'

    date_order = fields.Datetime(string='Order Date', readonly=False, index=True, default=fields.Datetime.now)
    is_not_post = fields.Boolean(string='ไม่เอาไปนำฝาก',default=False)

    @api.model
    def default_get(self, fields):
        res = super(POSOrder, self).default_get(fields)

        if self.env.user.pos_config_ids:
            config_id = self.env.user.pos_config_ids[0]
            res.update({'branch_id': config_id.branch_id.id,
                        'operating_branch_id': config_id.operating_branch_id.id,
                        })
        return res

    def _prepare_account_move_and_lines(self, session=None, move=None):
        # print ('--------_prepare_account_move_and_lines')
        def _flatten_tax_and_children(taxes, group_done=None):
            children = self.env['account.tax']
            if group_done is None:
                group_done = set()
            for tax in taxes.filtered(lambda t: t.amount_type == 'group'):
                if tax.id not in group_done:
                    group_done.add(tax.id)
                    children |= _flatten_tax_and_children(tax.children_tax_ids, group_done)
            return taxes + children

        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False
        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method

        def add_anglosaxon_lines(grouped_data):
            Product = self.env['product.product']
            Analytic = self.env['account.analytic.account']
            for product_key in list(grouped_data.keys()):
                if product_key[0] == "product":
                    line = grouped_data[product_key][0]
                    product = Product.browse(line['product_id'])
                    # In the SO part, the entries will be inverted by function compute_invoice_totals
                    price_unit = self._get_pos_anglo_saxon_price_unit(product, line['partner_id'], line['quantity'])
                    account_analytic = Analytic.browse(line.get('analytic_account_id'))
                    res = Product._anglo_saxon_sale_move_lines(
                        line['name'], product, product.uom_id, line['quantity'], price_unit,
                            fiscal_position=order.fiscal_position_id,
                            account_analytic=account_analytic)
                    if res:
                        line1, line2 = res
                        line1 = Product._convert_prepared_anglosaxon_line(line1, order.partner_id)
                        insert_data('counter_part', {
                            'name': line1['name'],
                            'account_id': line1['account_id'],
                            'credit': line1['credit'] or 0.0,
                            'debit': line1['debit'] or 0.0,
                            'partner_id': line1['partner_id']

                        })

                        line2 = Product._convert_prepared_anglosaxon_line(line2, order.partner_id)
                        insert_data('counter_part', {
                            'name': line2['name'],
                            'account_id': line2['account_id'],
                            'credit': line2['credit'] or 0.0,
                            'debit': line2['debit'] or 0.0,
                            'partner_id': line2['partner_id']
                        })

        for order in self.filtered(lambda o: not o.account_move or o.state == 'paid'):
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if move is None:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
                move = self._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)

            def insert_data(data_type, values):
                # print ('------INSERT DATA')
                # print (data_type)
                # print (values)
                # print ('---------------')
                # if have_to_group_by:
                values.update({
                    'partner_id': partner_id,
                    'move_id': move.id,
                })

                key = self._get_account_move_line_group_data_type_key(data_type, values, {'rounding_method': rounding_method})
                if not key:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                        if 'currency_id' in values:
                            current_value['amount_currency'] = current_value.get('amount_currency', 0.0) + values.get('amount_currency', 0.0)
                        if key[0] == 'tax' and rounding_method == 'round_globally':
                            if current_value['debit'] - current_value['credit'] > 0:
                                current_value['debit'] = current_value['debit'] - current_value['credit']
                                current_value['credit'] = 0
                            else:
                                current_value['credit'] = current_value['credit'] - current_value['debit']
                                current_value['debit'] = 0

                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id
            cur_company = order.company_id.currency_id
            amount_cur_company = 0.0
            date_order = (order.date_order or fields.Datetime.now())[:10]
            # print ('-----ORDER')
            # print (order.name)
            for line in order.lines:
                line = line.sudo()
                if cur != cur_company:
                    amount_subtotal = cur.with_context(date=date_order).compute(line.price_subtotal, cur_company)
                else:
                    amount_subtotal = line.price_subtotal

                # Search for the income account
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                # Just like for invoices, a group of taxes must be present on this base line
                # As well as its children
                base_line_tax_ids = _flatten_tax_and_children(line.tax_ids_after_fiscal_position).filtered(lambda tax: tax.type_tax_use in ['sale', 'none'])
                # print ('line.product_id')
                # print (line.product_id.is_pack)
                # print (x)
                if line.product_id.is_pack and line.product_id.product_pack_id:
                    # print('-PACK-----')
                    # print ('AMOUNT SUBTOTAL')
                    # print (amount_subtotal)
                    # print (line.product_id.name)

                    sum_credit = 0
                    sum_debit = 0
                    ##############################by JA - 18/10/2020 ################################################################################
                    count = 0     ####### use to count line item in the pack
                    amt_apply = 0 ####### This is actual amount will be post to GL need to summary of all item in the pack and compare with pack price
                    ##############################by JA - 18/10/2020 ################################################################################
                    for product_coupon_line_id in line.product_id.product_pack_id:
                        count +=1
                        pricelist = order.pricelist_id
                        fiscal_position_id = order.fiscal_position_id
                        total_amount = 0
                        config = order.session_id.config_id

                        pdt = line.product_id

                        # tax_id = self.env['account.tax']
                        # pack_price = self.env['account.tax']._fix_tax_included_price_company(line.price_unit, line.product_id.taxes_id,
                        #                                                      line.tax_ids_after_fiscal_position[0],
                        #                                                      line.product_id.company_id)


                        if line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include:
                            pack_price = line.tax_ids_after_fiscal_position[0].compute_all(line.price_unit)['total_excluded']
                            # print ('INCLUDE -VAT')
                        else:
                            # print ('NO VAT or EXC')
                            pack_price = line.price_unit


                        if pdt.is_pack:
                            for pd in pdt.product_pack_id:
                                total_amount = total_amount + (
                                        pd.product_quantity * self._get_pdt_price_(pd.product_id, partner_id, pricelist,
                                                                                   fiscal_position_id))
                            # print (total_amount)
                            coupon_price = product_coupon_line_id.product_quantity * self._get_pdt_price_(product_coupon_line_id.product_id, partner_id, pricelist,
                                                                fiscal_position_id)
                            # print(coupon_price)
                            amt = round((coupon_price / total_amount) * pack_price * line.qty,2)

                            # to fix gl not balance due to distribute value of the pack with each coupon value ratio, then the last one will keep the rest of the pack value###

                            if len(line.product_id.product_pack_id) == count:
                                amt = round((line.price_subtotal - amt_apply),2)
                            else:
                                ######not last one, accumulate to amt_apply#####
                                amt_apply += amt


                        if product_coupon_line_id.product_id.property_account_income_id.id:
                            income_account = product_coupon_line_id.product_id.property_account_income_id.id
                        elif product_coupon_line_id.product_id.categ_id.property_account_income_categ_id.id:
                            income_account = product_coupon_line_id.product_id.categ_id.property_account_income_categ_id.id
                        else:
                            raise UserError(_('Please define income '
                                              'account for this product: "%s" (id:%d).')
                                            % (product_coupon_line_id.product_id.name, product_coupon_line_id.product_id.id))

                        data = {
                            'name': product_coupon_line_id.product_id.name,
                            'quantity': product_coupon_line_id.product_quantity,
                            'product_id': product_coupon_line_id.product_id.id,
                            'account_id': income_account,
                            'analytic_account_id': order._prepare_analytic_account(line),
                            'credit': ((amt > 0) and amt) or 0.0,
                            'debit': ((amt < 0) and -amt) or 0.0,
                            'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                            'partner_id': partner_id

                        }
                        # print('DATA-TO-MV-LINE-NEWWW')
                        # print(data['credit'])
                        # print(data['debit'])
                        # sum_credit += data['credit']
                        # sum_debit += data['debit']
                        ##################for difference currency ######### no need for us
                        # if cur != cur_company:
                        #     data['currency_id'] = cur.id
                        #     data['amount_currency'] = -abs(line.price_subtotal) if data.get('credit') else abs(
                        #         line.price_subtotal)
                        #     amount_cur_company += data['credit'] - data['debit']
                        insert_data('product', data)
                    # print ('-----SUM PER LINE')
                    # print (sum_credit)
                    # print (sum_debit)
                    # print (line.price_subtotal)

                else:
                    # print ('-NO PACK')
                    data = {
                        'name': name,
                        'quantity': line.qty,
                        'product_id': line.product_id.id,
                        'account_id': income_account,
                        'analytic_account_id': order._prepare_analytic_account(line),
                        'credit': ((amount_subtotal > 0) and amount_subtotal) or 0.0,
                        'debit': ((amount_subtotal < 0) and -amount_subtotal) or 0.0,
                        'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                        'partner_id': partner_id
                    }
                    #################MOVE from line level to product in line_pack_ids
                    if cur != cur_company:
                        data['currency_id'] = cur.id
                        data['amount_currency'] = -abs(line.price_subtotal) if data.get('credit') else abs(line.price_subtotal)
                        amount_cur_company += data['credit'] - data['debit']
                    insert_data('product', data)
                    ######################################################################

                # Create the tax lines
                taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
                if not taxes:
                    continue
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for tax in taxes.compute_all(price, cur, line.qty)['taxes']:
                    if cur != cur_company:
                        round_tax = False if rounding_method == 'round_globally' else True
                        amount_tax = cur.with_context(date=date_order).compute(tax['amount'], cur_company, round=round_tax)
                    else:
                        amount_tax = tax['amount']
                    data = {
                        'name': _('Tax') + ' ' + tax['name'],
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': tax['account_id'] or income_account,
                        'credit': ((amount_tax > 0) and amount_tax) or 0.0,
                        'debit': ((amount_tax < 0) and -amount_tax) or 0.0,
                        'tax_line_id': tax['id'],
                        'partner_id': partner_id,
                        'order_id': order.id
                    }
                    if cur != cur_company:
                        data['currency_id'] = cur.id
                        data['amount_currency'] = -abs(tax['amount']) if data.get('credit') else abs(tax['amount'])
                        amount_cur_company += data['credit'] - data['debit']
                    insert_data('tax', data)

            # round tax lines per order
            if rounding_method == 'round_globally':
                for group_key, group_value in grouped_data.items():
                    if group_key[0] == 'tax':
                        for line in group_value:
                            line['credit'] = cur_company.round(line['credit'])
                            line['debit'] = cur_company.round(line['debit'])
                            if line.get('currency_id'):
                                line['amount_currency'] = cur.round(line.get('amount_currency', 0.0))

            # counterpart
            if cur != cur_company:
                # 'amount_cur_company' contains the sum of the AML converted in the company
                # currency. This makes the logic consistent with 'compute_invoice_totals' from
                # 'account.invoice'. It ensures that the counterpart line is the same amount than
                # the sum of the product and taxes lines.
                amount_total = amount_cur_company
            else:
                amount_total = order.amount_total
            data = {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'credit': ((amount_total < 0) and -amount_total) or 0.0,
                'debit': ((amount_total > 0) and amount_total) or 0.0,
                'partner_id': partner_id
            }
            if cur != cur_company:
                data['currency_id'] = cur.id
                data['amount_currency'] = -abs(order.amount_total) if data.get('credit') else abs(order.amount_total)
            insert_data('counter_part', data)

            order.write({'state': 'done', 'account_move': move.id})

        if self and order.company_id.anglo_saxon_accounting:
            add_anglosaxon_lines(grouped_data)

        return {
            'grouped_data': grouped_data,
            'move': move,
        }

    ##############JA - 02/09/2020 - To manage ruturn process ####
    @api.multi
    def refund(self):
        """Create a copy of order  for refund order"""
        # print ('------NEW REFUDN---')
        PosOrder = self.env['pos.order']
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)],
                                                         limit=1)
        if not current_session:
            # print ('-step-2')
            current_session = self.env['pos.session'].search(
                [('state', '!=', 'closed'), ('config_id', '=', self.session_id.config_id.id)],limit=1)

            if not current_session:
                raise UserError(
                    _('To return product(s), you need to open a session that will be used to register the refund.'))
        for order in self:
            clone = order.copy({
                # ot used, name forced by create
                'name': order.name + _(' REFUND'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': order.pos_reference,
                'lines': False,
            })
            for line in order.lines:
                clone_line = line.copy({
                    # required=True, copy=False
                    'name': line.name + _(' REFUND'),
                    'order_id': clone.id,
                    'qty': -line.qty,
                })
            PosOrder += clone

        return {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def _prepare_bank_statement_line_payment_values(self, data):
        res = super(POSOrder, self)._prepare_bank_statement_line_payment_values(data)
        if 'note' in data:
            res.update({'note':data['note']})

        return res

    def _prepare_analytic_account(self, line):
        '''This method is designed to be inherited in a custom module'''
        super(POSOrder, self)._prepare_analytic_account(line)
        analytic_account_id = False
        if self.branch_id and self.branch_id.analytic_account_id:
            analytic_account_id = self.branch_id.analytic_account_id.id
        return analytic_account_id




class pos_order_advance(models.TransientModel):
    _name = 'pos.order.advance'

    def create_picking(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['pos.order'].browse(active_ids):
            if not record.picking_id:
                record.create_picking()


            if record.picking_id.state == 'assigned':
                record.picking_id.update({'force_date': record.date_order})
                record.picking_id.force_assign()
                record.picking_id.button_validate()
                record.picking_id.picking_immediate_process()


    def get_coupon_balance(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['pos.order'].browse(active_ids):
            record.get_coupon_balance()

    def fix_order_coupon(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['pos.order'].browse(active_ids):
            record.fix_order_coupon()