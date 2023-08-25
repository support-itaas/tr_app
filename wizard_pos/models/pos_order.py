# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
import json
import logging

import requests

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"


    branch_id = fields.Many2one('project.project', 'Branch')
    operating_branch_id = fields.Many2one('operating.unit', 'Operating Branch')
    points = fields.Float("Points", compute='_compute_points', digits=dp.get_precision('Points'))
    star = fields.Many2one('star.level', 'Star Level', compute='_compute_star_level')
    pricelist_currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id',
                                            string='Pricelist Currency')
    wallet_amount = fields.Float(compute='_compute_wallet_amount', string='Wallet Amount')
    # for import
    name = fields.Char(string='Order Ref', required=True, readonly=False, copy=False, default='/')
    coupon_ids = fields.One2many('wizard.coupon','order_id',string='Coupon')
    is_create_coupon = fields.Boolean(string='Create Coupon',default=True)

    def delete_coupon(self):
        for obj in self:
            if obj.coupon_ids.filtered(lambda c: c.state == 'redeem'):
                raise UserError(
                    _('ไม่มีคูปอง หรือ บางคูปองถูกนำไปใช้แล้ว ตรวจสอบความถูกต้อง และ ยกเลิกการ Reedeem ก่อนลบอีกครั้ง'))

            if obj.statement_ids:
                statement_msg = ""
                for statement in obj.statement_ids:
                    statement_msg += statement.name + ','
                    statement.sudo().unlink()
                # message = _("statement %s ") % (statement_msg)
                # self.message_post(body=message)

            if obj.coupon_ids:
                coupon_msg = ""
                for coupon in obj.coupon_ids:
                    coupon_msg += coupon.name + ','
                    coupon.sudo().unlink()
                # message = _("ลบคูปอง %s ") % (coupon_msg)
                # self.message_post(body=message)

            obj.write({
                'state': 'draft',
            })

    def delete_payment(self):
        for obj in self:

            if obj.statement_ids:
                statement_msg = ""
                for statement in obj.statement_ids:
                    statement_msg += statement.name + ','
                    statement.sudo().unlink()
                # message = _("statement %s ") % (statement_msg)
                # self.message_post(body=message)

            obj.write({
                'state': 'draft',
            })


    @api.depends('statement_ids')
    def _compute_wallet_amount(self):
        amt = 0
        for order in self:
            for line in order.statement_ids:
                if line.statement_id.journal_id.wallet_journal:
                    amt = amt + line.amount
            order.wallet_amount = amt

    @api.multi
    @api.depends('amount_total','state')
    def _compute_points(self):
        car_settings = self.env['car.settings'].search([])
        if car_settings:
            for order in self:
                if car_settings.point_equal_amount != 0 and order.state != 'draft':
                    order.points = (order.amount_total / car_settings.point_equal_amount)

                    # if order.state == 'cancel':
                    #     order.points = (order.amount_total / car_settings.point_equal_amount) * (-1)
                    # else:
                    #     order.points = (order.amount_total / car_settings.point_equal_amount)

    @api.multi
    def _compute_star_level(self):
        for order in self:
            star_levels = self.env['star.level'].search([])
            for star_level in star_levels:
                if star_level.from_point <= order.points <= star_level.to_point and order.state != 'draft':
                    order.star = star_level.id

    @api.multi
    def place_order(self, partner_id=None, branch_id=None, use_wallet=False, order_line_data=[]):
        # for app api
        if branch_id == None:
            raise UserError(_('Please send the branch to place order'))
        if partner_id == None:
            raise UserError(_('Please send the partner to place order'))
        branch = self.env['project.project'].search([('id', '=', branch_id)],limit=1)
        config = self.env['pos.config'].search([('branch_id', '=', branch.id)],limit=1)
        if not config:
            raise UserError(_('There is no POS for selected branch'))
        session = self.env['pos.session'].search(
            [('config_id', '=', config.id), ('state', '=', 'opened')],limit=1)
        if not session:
            raise UserError(_('There is no active session running on selected branch. Try after sometime'))
        payment_journal_id = ''
        if use_wallet:
            if not config.journal_ids:
                raise UserError(_('There is no payment method configured. Please Configure'))
            payment_journal_id = (config.journal_ids.filtered(lambda j: j.wallet_journal)).id
            # for journal in config.journal_ids:
            #     if journal.wallet_journal:
            #         payment_journal_id = journal.id
            #         break
            if not payment_journal_id:
                raise UserError(_('There is no wallet payment method configured. Please Configure'))
        order_line_list = []
        if partner_id and branch_id and order_line_data:
            for line in order_line_data:
                pdt = self.env['product.product'].search([('id', '=', line['product_id'])])
                line.update({'tax_ids': [(6, 0, [x.id for x in pdt.taxes_id])]})
                order_line_list.append((0, 0, line))
            order = self.create({
                'session_id': session.id,
                'partner_id': partner_id,
                'lines': order_line_list,
                'branch_id': branch.id,
                'company_id': branch.company_id.id,
                'operating_branch_id': config.operating_branch_id.id,
            })
            if use_wallet:
                data = order.read()[0]
                currency = order.pricelist_id.currency_id
                data['journal'] = payment_journal_id
                data['amount'] = order.amount_total
                if not float_is_zero(order.amount_total, precision_rounding=currency.rounding or 0.01):
                    order.add_payment(data)
                if order.test_paid():
                    order.action_pos_order_paid()
        else:
            return False

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        session = self.env['pos.session'].search([('id', '=', order_fields['session_id'])])
        config = session.config_id
        order_fields.update({
            'branch_id': config.branch_id.id,
            'operating_branch_id': config.operating_branch_id.id
        })
        return order_fields

    @api.model
    def create(self, values):
        res = super(PosOrder, self).create(values)
        product_details = []
        service_products = []
        for order_line in res.lines:
            message = order_line.product_id.name + ' - ' + str(
                order_line.qty) + ' - ' + res.company_id.currency_id.symbol + ' ' + str(order_line.price_unit)
            product_details.append(message)
            if order_line.product_id.is_service:
                service_products.append(order_line)
        notification = self.env['wizard.notification'].create({
            'name': 'Your order ' + res.name + ' is created',
            'message': 'Your order ' + res.name + ' is successfully created at ' + res.date_order + '\n \n' + ' \n'.join(
                product_details) + '\n' + 'Total ' + ' - ' + res.company_id.currency_id.symbol + ' ' + str(
                res.amount_total) + '\n' + 'การสั่งซื้อนี้จะสมบูรณ์หลังการชำระเงินเรียบร้อยแล้วเท่านั้น ท่านสามารถแสดงรายละเอียดการสั่งซื้อ และ ยืนยันการชำระเงินได้ที่เจ้าหน้าที่ประจำสาขา',
            'read_message': False,
            'partner_id': res.partner_id.id,
            'message_at': fields.Datetime.now(),
        })
        if res.partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            deviceToken = res.partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', res.partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Your order is created',
                                     'body': 'Your order ' + res.name + ' is successfully created at ' + res.date_order + '\n \n' + ' \n'.join(
                                         product_details) + '\n' + 'Total ' + ' - ' + res.company_id.currency_id.symbol + ' ' + str(
                                         res.amount_total) + '\n' + 'การสั่งซื้อนี้จะสมบูรณ์หลังการชำระเงินเรียบร้อยแล้วเท่านั้น ท่านสามารถแสดงรายละเอียดการสั่งซื้อ และ ยืนยันการชำระเงินได้ที่เจ้าหน้าที่ประจำสาขา',
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

        # for product in service_products:
        #     for rec in range(int(product.qty)):
        #         ####### Change name from res.name to product name
        #         self.env['project.task'].create({
        #             'name': product.product_id.name,
        #             'project_id': res.branch_id.id,
        #             'user_id': res.session_id.user_id.id,
        #             'partner_id': res.partner_id.id,
        #             'date_deadline': fields.Datetime.now(),
        #             'order_id': res.id,
        #             'amount': product.price_unit,
        #         })
        return res

    @api.multi
    def _get_pdt_price_(self, product, partner, pricelist, fiscal_position_id):
        fpos = fiscal_position_id
        price = pricelist.get_product_price(
            product, 1.0, partner)
        tax_ids = product.taxes_id.filtered(
            lambda r: not product.company_id or r.company_id == product.company_id)
        tax_ids_after_fiscal_position = fpos.map_tax(tax_ids, product, partner) if fpos else tax_ids
        price_unit = self.env['account.tax']._fix_tax_included_price_company(price, product.taxes_id,
                                                                             tax_ids_after_fiscal_position,
                                                                             product.company_id)
        return price_unit


    @api.multi
    def create_coupons(self):
        for order in self:
            session = order.session_id
            pricelist = order.pricelist_id
            partner = order.partner_id
            fiscal_position_id = order.fiscal_position_id

            config = session.config_id
            for line in order.lines:
                total_amount = 0
                pdt = line.product_id
                print ('--XXXXX')
                if not line.is_create():
                    continue

                if line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.qty:
                    pack_price = line.price_subtotal / line.qty
                else:
                    pack_price = line.price_unit


                if pdt.is_pack:
                    for pd in pdt.product_pack_id:
                        total_amount = total_amount + (
                                pd.product_quantity * self._get_pdt_price_(pd.product_id, partner, pricelist,
                                                                           fiscal_position_id))
                    for p in pdt.product_pack_id:
                        if config.required_customer:
                            coupon_price = self._get_pdt_price_(p.product_id, partner, pricelist, fiscal_position_id)
                            amt = (coupon_price / total_amount) * pack_price
                            count = int(line.qty) * int(p.product_quantity)
                            for x in range(count):
                                coupon = self.env['wizard.coupon'].create({
                                    'package_id': pdt.id,
                                    'partner_id': partner.id,
                                    'product_id': p.product_id.id,
                                    'order_branch_id': config.branch_id.id,
                                    'amount': amt,
                                    'order_id': order.id,
                                })
                if pdt.is_coupon:
                    if config.required_customer:
                        for x in range(int(line.qty)):
                            coupon = self.env['wizard.coupon'].create({
                                'partner_id': partner.id,
                                'product_id': pdt.id,
                                'order_branch_id': config.branch_id.id,
                                'amount': pack_price,
                                'order_id': order.id,
                            })

    def _reconcile_payments(self):
        super(PosOrder, self)._reconcile_payments()
        for order in self:
            if order.wallet_amount > 0:
                aml = order.statement_ids.mapped('journal_entry_ids') | order.account_move.line_ids | order.invoice_id.move_id.line_ids
                aml = aml.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == order.partner_id.commercial_partner_id)
                search_aml = self.env['account.move.line'].search(
                    [('reconciled', '=', False), ('account_id.internal_type', '=', 'receivable'),
                     ('partner_id', '=', order.partner_id.commercial_partner_id.id)])
                aml = aml | search_aml
                try:
                    aml.reconcile()
                except Exception:
                    _logger.exception('Reconciliation did not work for order %s', order.name)

    @api.multi
    def action_pos_order_paid(self):
        super(PosOrder, self).action_pos_order_paid()
        ###########REMOVE TEMPORARY for Paid old order 10-12-2019
        ##### condition to do for new order
        if self.amount_total >= 0 and self.lines and self.lines[0].qty > 0 and self.is_create_coupon:
            print ('--BEFOE create_coupons')
            self.create_coupons()
            notification = self.env['wizard.notification'].create({
                'name': 'Payment received for ' + self.name,
                'message': 'Successfully received the amount ' + self.company_id.currency_id.symbol + ' ' + str(
                    self.amount_total) + ' for the order ' + self.name + ' at ' + fields.Datetime.now() + '.',
                'read_message': False,
                'partner_id': self.partner_id.id,
                'message_at': fields.Datetime.now(),
            })

            if self.partner_id.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                # serverToken = self.env['car.settings'].sudo().get_param('server_token') or False
                deviceToken = self.partner_id.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                        ('read_message', '=', False)])
                if serverToken:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': 'Payment Received',
                                         'body': 'Successfully received the amount ' + self.company_id.currency_id.symbol + ' ' + str(
                                             self.amount_total) + ' for the order ' + self.name + ' at ' + fields.Datetime.now() + '.',
                                         'badge': len(notifications),
                                         "click_action": "FCM_PLUGIN_ACTIVITY"
                                         },
                        'to':
                            deviceToken,
                        'priority': 'high',
                        'data': {"notification_count": len(notifications),
                                 'notification_id': notification.id},
                    }
                    response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

        else:
            ##### condition to do for return amount_total < 0, then search original pos_order that will have the pos_reference, then update coupon for that order for each
            #### product line or package then inactive it.
            pos_order_id = self.env['pos.order'].search([('pos_reference','=',self.pos_reference),('id','!=',self.id)],order='date_order',limit=1)
            if pos_order_id:
                for line in self.lines:
                    coupon_ids = self.env['wizard.coupon'].search([('package_id','=',line.product_id.id),('order_id','=',pos_order_id.id)])
                    # print (coupon_ids)
                    if coupon_ids:
                        coupon_ids.update({'active': False})

class pos_order_line(models.Model):
    _inherit = 'pos.order.line'

    def is_create(self):
        print ('--is_create--1')
        # super(pos_order_line, self).is_create()
        return True
