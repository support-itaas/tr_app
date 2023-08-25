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


class POSSession (models.Model):
    _inherit = 'pos.session'


    def update_analytic_account_all_for_jv(self):
        account_move_line_ids = self.env['account.move.line'].search([('date','>=','2021-01-01'),('department_id','!=',False),('analytic_account_id','=',False)])
        for aml in account_move_line_ids:
            # print (aml.department_id.name)
            # print (aml.analytic_account_id)
            if aml.department_id and aml.department_id.analytic_account_id:
                # print (aml.move_id)
                aml.update({'analytic_account_id': aml.department_id.analytic_account_id.id})

    def update_analytic_account_all(self):
        session_ids = self.env['pos.session'].search([('start_at','>=','2021-01-01')])
        for session in session_ids:
            # print (session.name)
            session.update_analytic_account()

    def update_analytic_account(self):
        for session in self:
            if session.config_id and session.config_id.branch_id and session.config_id.branch_id.analytic_account_id:
                analytic_account_id = session.config_id.branch_id.analytic_account_id
                order_ids = session.order_ids.filtered(lambda o: o.account_move)
                if order_ids and analytic_account_id:
                    account_move_id = order_ids[0].account_move
                    account_move_id.line_ids.update({'analytic_account_id': analytic_account_id.id})



    def _confirm_orders(self):
        for session in self:
            super(POSSession, session)._confirm_orders()
            account_move_id = session.mapped('order_ids').mapped('account_move')
            account_move_id.line_ids.update({'operating_unit_id': session.config_id.operating_branch_id.id})
            # tax_move_line_ids = account_move_id.mapped('line_ids').filtered(lambda x: x.account_id.sale_tax_report)
            # if session.config_id.operating_branch_id and tax_move_line_ids:
            #     for tax_move_line in tax_move_line_ids:
            #         tax_move_line.update({'operating_unit_id': session.config_id.operating_branch_id.id})


    # def fix_session_coupon(self):
    #
    #     self.env['pos.session']
    #
    #     for order in self.order_ids:
    #         if order.lines.filtered(lambda o: o.price_unit < 0) and order.account_move:
    #             for line in order.lines.filtered(lambda o: o.price_unit < 0):
    #                 aml_line = order.account_move.line_ids.filtered(lambda x: x.product_id == line.product_id and x.date >= '2021-01-01')
    #                 if line.product_id.actual_income_account_id.id:
    #                     aml_line.update({'account_id': line.product_id.actual_income_account_id.id})

    def fix_session_coupon(self):
        for order in self.order_ids:

            if order.lines.filtered(lambda o: o.price_unit < 0) and order.account_move:
                for line in order.lines.filtered(lambda o: o.price_unit < 0):
                    aml_line = order.account_move.line_ids.filtered(lambda x: x.product_id == line.product_id and x.date >= '2021-01-01')
                    if line.product_id.actual_income_account_id.id:
                        aml_line.update({'account_id': line.product_id.actual_income_account_id.id})

            print ('Order',order.name)
            sum_price_subtotal = sum(line.price_subtotal for line in order.lines.filtered(lambda o:o.product_id.is_pack))
            sum_coupon = sum(coupon.amount for coupon in order.coupon_ids)

            print ('SUM PRICE',sum_price_subtotal)
            print('SUM COUPON', sum_coupon)
            dif = sum_price_subtotal - sum_coupon
            print ('DIFFF',dif)
            if abs(dif) > 1:
                order.fix_order_coupon()

            # for line in order.lines.filtered(lambda o:o.product_id.is_pack):
            #
            #     if abs(line.price_subtotal - )
            # print ('FXI ORDER')

        # account_order_ids = self.mapped('order_ids').mapped('account_move').mapped('line_ids').mapped('account_id')
        # account_invoice_ids = self.mapped('order_ids').mapped('invoice_id').mapped('move_id').mapped('line_ids').mapped('account_id')
        # account_ids = account_order_ids + account_invoice_ids
        # for account_id in account_ids:
        #     coupon_ids = self.mapped('order_ids').mapped('coupon_ids').filtered(
        #                         lambda o: o.product_id.property_account_income_id.id == account_id.id)
        #     sum_coupon =
        #
        #     self.mapped('order_ids').mapped('account_move').mapped('line_ids').mapped('account_id')
        #


class pos_order(models.Model):
    _inherit = 'pos.order'

    is_balance = fields.Boolean(string='Balance')

    # @api.depends('lines','lines.product_id','lines.package_id','amount_total','coupon_ids','coupon_ids.amount')
    def get_coupon_balance(self):
        for order in self:
            is_balance = True
            for line in order.lines.filtered(lambda o: o.product_id.sudo().is_pack):
                if not line.package_id:
                    coupon_ids = order.coupon_ids.filtered(lambda x: x.package_id == line.product_id.sudo())
                    if abs(line.price_subtotal - sum(coupon.amount for coupon in coupon_ids)) >= 1:
                        is_balance = False
                        break

                else:
                    coupon_ids = order.coupon_ids.filtered(
                        lambda x: x.package_id == line.product_id.sudo() and x.coupon_running == line.package_id.name)
                    if abs(line.price_subtotal - sum(coupon.amount for coupon in coupon_ids)) >= 1:
                        is_balance = False
                        break

            order.is_balance = is_balance


    def fix_order_coupon(self):
        for order in self:
            if order.invoice_id:
                 order.invoice_id.update_product_pack_to_aml()

            if order.account_move or order.invoice_id:
                for line in order.lines.filtered(lambda o: o.product_id.is_pack):
                    if not line.package_id:
                        coupon_ids = order.coupon_ids.filtered(lambda x: x.package_id == line.product_id)
                        if abs(line.price_subtotal - sum(coupon.amount for coupon in coupon_ids)) < 1:
                            continue
                    else:
                        coupon_ids = order.coupon_ids.filtered(lambda x: x.package_id == line.product_id and x.coupon_running == line.package_id.name)
                        if abs(line.price_subtotal - sum(coupon.amount for coupon in coupon_ids)) < 1:
                            continue


                    for product_line in line.product_id.product_pack_id:
                        total_qty = product_line.product_quantity * line.qty
                        if not line.package_id:
                            current_qty = len(order.coupon_ids.filtered(lambda x: x.product_id == product_line.product_id and x.package_id == line.product_id))
                        else:
                            current_qty = len(order.coupon_ids.filtered(
                                lambda x: x.product_id == product_line.product_id and x.package_id == line.product_id and x.coupon_running == line.package_id.name))

                        if total_qty > current_qty:
                            pending_qty = total_qty - current_qty
                            if pending_qty > 0:
                                if not line.package_id:
                                    coupon_ids = self.env['wizard.coupon'].search(
                                        [('package_id', '=', line.product_id.id),
                                         ('product_id', '=', product_line.product_id.id),
                                         ('partner_id', '=', order.partner_id.id),
                                         ('expiry_date', '>', order.date_order), ('order_id', '=', False)],
                                        limit=pending_qty)
                                    if not coupon_ids or len(coupon_ids) < pending_qty:
                                        coupon_ids = self.env['wizard.coupon'].search(
                                            [('package_id', '=', line.product_id.id),
                                             ('product_id', '=', product_line.product_id.id),
                                             ('partner_id', '=', order.partner_id.id),
                                             ('active', '=', False),
                                             ('expiry_date', '>', order.date_order), ('order_id', '=', False)],
                                            limit=pending_qty)

                                    if not coupon_ids or len(coupon_ids) < pending_qty:
                                        coupon_ids = self.env['wizard.coupon'].search(
                                            [('product_id', '=', product_line.product_id.id),
                                             ('partner_id', '=', order.partner_id.id), ('expiry_date', '>', order.date_order),('order_id', '=', False)],
                                            limit=pending_qty)

                                    if not coupon_ids or len(coupon_ids) < pending_qty:
                                        coupon_ids = self.env['wizard.coupon'].search(
                                            [('product_id', '=', product_line.product_id.id),('type', '=', 'e-coupon'),('expiry_date', '>', order.date_order),('order_id', '=', False)],
                                            limit=pending_qty)
                                        if coupon_ids:
                                            coupon_ids.update({'partner_id': order.partner_id.id})
                                            coupon_ids.update({'order_id': order.id})
                                            coupon_ids.update({'session_id': order.session_id.id})


                                    if coupon_ids:
                                        coupon_ids.update({'order_id': order.id})
                                        coupon_ids.update({'session_id': order.session_id.id})
                                        coupon_ids.update({'active': True})
                                        coupon_ids.update({'order_branch_id': order.branch_id.id})
                                        coupon_ids.update({'purchase_date': order.date_order})
                                        coupon_ids.update({'package_id': line.product_id.id})
                                        coupon_ids.update_coupons_value()
                                else:
                                    #package_id, paper coupon
                                    coupon_ids = self.env['wizard.coupon'].search(
                                        [('package_id', '=', line.product_id.id),
                                         ('product_id', '=', product_line.product_id.id), ('type', '=', 'paper'),
                                         ('coupon_running','=',line.package_id.name),
                                         ('expiry_date', '>', order.date_order), ('order_id', '=', False)],
                                        limit=pending_qty)

                                    if not coupon_ids or len(coupon_ids) < pending_qty:
                                        coupon_ids = self.env['wizard.coupon'].search(
                                            [('product_id', '=', product_line.product_id.id),
                                             ('coupon_running', '=', line.package_id.name),
                                             ('type', '=', 'paper'),
                                             ('expiry_date', '>', order.date_order),
                                             ('order_id', '=', False)],
                                            limit=pending_qty)
                                        if coupon_ids:
                                            coupon_ids.update({'partner_id': order.partner_id.id})
                                            coupon_ids.update({'order_id': order.id})
                                            coupon_ids.update({'session_id': order.session_id.id})

                                    if not coupon_ids or pending_qty > len(coupon_ids):
                                        pending_qty = pending_qty - len(coupon_ids)
                                        new_e_to_p_coupon = self.env['wizard.coupon'].search(
                                            [('product_id', '=', product_line.product_id.id),
                                             ('expiry_date', '>', order.date_order),
                                             ('order_id', '=', False)],
                                            limit=pending_qty)
                                        if new_e_to_p_coupon:
                                            new_e_to_p_coupon.update({'partner_id': order.partner_id.id})
                                            new_e_to_p_coupon.update({'type': 'paper'})
                                            new_e_to_p_coupon.update({'coupon_running': line.package_id.name})
                                            new_e_to_p_coupon.update({'order_branch_id': order.session_id.config_id.branch_id.id})
                                            coupon_ids = coupon_ids + new_e_to_p_coupon



                                    if coupon_ids:
                                        coupon_ids.update({'order_id': order.id})
                                        coupon_ids.update({'session_id': order.session_id.id})
                                        coupon_ids.update({'active': True})
                                        coupon_ids.update({'order_branch_id': order.branch_id.id})
                                        coupon_ids.update({'purchase_date': order.date_order})
                                        coupon_ids.update({'package_id': line.product_id.id})
                                        coupon_ids.update_coupons_value()
                                    # if coupon_ids:
                                    #     coupon_ids.update({'order_id': order.id})
                                    #     coupon_ids.update({'session_id': order.session_id.id})
                                    #     coupon_ids.update({'active': True})
                                    #     coupon_ids.update({'order_branch_id': order.branch_id.id})
                                    #     coupon_ids.update({'purchase_date': order.date_order})
                                    #     coupon_ids.update({'package_id': line.product_id.id})
                                    #     coupon_ids.update_coupons_value()




                        elif total_qty < current_qty:
                            pending_qty = current_qty - total_qty
                            draft_coupon_ids = self.env['wizard.coupon'].search(
                                [('package_id', '=', line.product_id.id),
                                 ('product_id', '=', product_line.product_id.id),
                                 ('order_id', '=', order.id),('state','=','draft')], limit=pending_qty)

                            pending_qty = pending_qty - len(draft_coupon_ids)
                            if draft_coupon_ids:
                                draft_coupon_ids.update({'order_id': False})

                            if pending_qty:
                                use_coupon_ids = self.env['wizard.coupon'].search(
                                    [('package_id', '=', line.product_id.id),
                                     ('product_id', '=', product_line.product_id.id),
                                     ('order_id', '=', order.id),
                                     ('state', '!=', 'draft')], limit=pending_qty)

                                if use_coupon_ids:
                                    for coupon in use_coupon_ids:
                                        coupon.update({'order_id': False})
                                        coupon.update({'state': 'draft'})
                                        if coupon.move_id and coupon.move_id.date >= '2021-01-01':
                                            coupon.move_id.sudo().button_cancel()
                                            coupon.move_id.sudo().unlink()



                        else:

                            for coupon in coupon_ids:
                                wrong_coupon = line.product_id.product_pack_id.filtered(lambda x: x.product_id == coupon.product_id)
                                if not wrong_coupon:
                                    coupon.update({'order_id': False})

                            coupon_ids.update_coupons_value()


            order.get_coupon_balance()





