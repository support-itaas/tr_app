# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


class wizard_coupon(models.Model):
    _inherit = 'wizard.coupon'

    # update coupon value
    @api.multi
    def update_coupons_value(self):
        for coupon in self:
            if not coupon.order_id:
                # print ('Update Coupon Order')
                pos_line_id = self.env['pos.order.line'].sudo().search([('package_id.name','=',coupon.coupon_running)],limit=1)
                coupon.update({'order_id': pos_line_id.order_id.id})


            for order in coupon.order_id:
                session = order.session_id
                pricelist = order.pricelist_id
                partner = order.partner_id
                fiscal_position_id = order.fiscal_position_id

                config = session.config_id
                for line in order.lines.filtered(lambda x: x.product_id == coupon.package_id):
                    total_amount = 0
                    pdt = line.product_id
                    # print ('--XXXXX')
                    # if not line.is_create():
                    #     continue

                    if line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.qty:
                        pack_price = line.price_subtotal / line.qty
                    else:
                        pack_price = line.price_unit

                    if pdt.is_pack:
                        print ('PD PaCK')
                        for pd in pdt.product_pack_id:
                            total_amount = total_amount + (
                                    pd.product_quantity * order._get_pdt_price_(pd.product_id, partner, pricelist,
                                                                               fiscal_position_id))

                            print ("TOTAL AMOUNT",total_amount)
                        for p in pdt.product_pack_id.filtered(lambda x: x.product_id == coupon.product_id):
                            if config.required_customer:
                                coupon_price = order._get_pdt_price_(p.product_id, partner, pricelist,
                                                                    fiscal_position_id)
                                amt = (coupon_price / total_amount) * pack_price
                                print ("TOTAL AMT", amt)
                                coupon.amount = amt

                    if pdt.is_coupon:
                        coupon.amount = amt
            if coupon.order_id:
                coupon.update({'purchase_date': coupon.order_id.date_order})

            #no order , direct update from package price
            if not coupon.order_id:
                package_id = coupon.package_id
                pack_price = package_id.lst_price
                total_amount = 0
                for pd in package_id.product_pack_id:
                    total_amount += pd.product_quantity * pd.product_id.lst_price


                for p in package_id.product_pack_id.filtered(lambda x: x.product_id == coupon.product_id):
                    amt = ((p.product_quantity * p.product_id.lst_price)/total_amount) * pack_price
                    coupon.amount = amt/p.product_quantity


                # for line in order.lines.filtered(lambda x: x.product_id == coupon.package_id):
                #     total_amount = 0
                #     pdt = line.product_id
                #     # print ('--XXXXX')
                #     # if not line.is_create():
                #     #     continue
                #
                #     if line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.qty:
                #         pack_price = line.price_subtotal / line.qty
                #     else:
                #         pack_price = line.price_unit
                #
                #     if pdt.is_pack:
                #         print ('PD PaCK')
                #         for pd in pdt.product_pack_id:
                #             total_amount = total_amount + (
                #                     pd.product_quantity * order._get_pdt_price_(pd.product_id, partner, pricelist,
                #                                                                fiscal_position_id))
                #
                #             print ("TOTAL AMOUNT",total_amount)
                #
                #         for p in pdt.product_pack_id.filtered(lambda x: x.product_id == coupon.product_id):
                #             if config.required_customer:
                #                 coupon_price = order._get_pdt_price_(p.product_id, partner, pricelist,
                #                                                     fiscal_position_id)
                #                 amt = (coupon_price / total_amount) * pack_price
                #                 print ("TOTAL AMT", amt)
                #                 coupon.amount = amt
                #
                #     if pdt.is_coupon:
                #         coupon.amount = amt

            if coupon.state == 'redeem' and (not coupon.move_id or (coupon.move_id and coupon.amount != coupon.move_id.amount) or (coupon.move_id and coupon.order_branch_id.sudo().company_id != coupon.move_id.sudo().company_id)):
                    if coupon.redeem_date and coupon.redeem_date < '2021-01-01':
                        coupon.redeem_date = coupon.purchase_date
                    coupon.create_actual_revenue()
            if coupon.state == 'expire' and (not coupon.move_id or (coupon.move_id and coupon.amount != coupon.move_id.amount) or (coupon.move_id and coupon.order_branch_id.sudo().company_id != coupon.move_id.sudo().company_id)):
                if coupon.redeem_date and coupon.redeem_date < '2021-01-01':
                    coupon.redeem_date = coupon.purchase_date
                coupon.expire_coupon()

class wizard_coupon_advance(models.TransientModel):
    _name = 'wizard.coupon.advance'

    product_id = fields.Many2one('product.product', required=False, string="Coupon")
    from_date = fields.Date(string='Purchase From Date')
    to_date = fields.Date(string='Purchase To Date')
    redeem_from_date = fields.Date(string='Redeem From Date')
    redeem_to_date = fields.Date(string='Redeem To Date')
    expiry_from_date = fields.Date(string='Expiry From Date')
    expiry_to_date = fields.Date(string='Expiry To Date')
    state = fields.Selection([('draft', 'Available'), ('redeem', 'Redeemed'), ('expire', 'Expired')], string='state',
                             default='draft')


    def cancel_expire_and_extend(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['wizard.coupon'].browse(active_ids):
            print ('REcord',record.name)
            if record.state == 'expire' and record.move_id:
                record.move_id.sudo().button_cancel()
                record.move_id.sudo().unlink()
                record.redeem_date = False
                record.branch_id = False
                record.plate_number_id = False
                record.expiry_date = self.expiry_to_date
                record.state = 'draft'


    def update_sequence(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        # for record in self.env['wizard.coupon'].browse(active_ids):
        #     record.session_id  = record.order_id.session_id

        for record in self.env['wizard.coupon'].browse(active_ids):
            print('STEP-8')
            if not record.revenue_to_branch:
                source_branch_ratio = self.env['car.settings'].sudo().search([]).source_branch_ratio
                source_branch_amount = round(record.amount * (source_branch_ratio / 100), 2)
                destination_branch_ratio = self.env['car.settings'].sudo().search([]).destination_branch_ratio
                destination_branch_amount = round(record.amount - source_branch_amount, 2)
            else:
                source_branch_amount = 0
                destination_branch_amount = record.amount

            record.update({'source_branch_amount': source_branch_amount,
                          'note': 'redeem-amount',
                         'destination_branch_amount': destination_branch_amount, })



    def expire_income(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        domain = [('state', '=', 'expire'),('active', '=', True),('type', '=', 'e-coupon')]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.from_date:
            domain.append(('purchase_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('purchase_date', '<=', self.to_date))

        if self.expiry_from_date:
            domain.append(('expiry_date', '>=', self.expiry_from_date))

        if self.expiry_to_date:
            domain.append(('expiry_date', '<=', self.expiry_to_date))


        if self.product_id or self.from_date or self.to_date or self.expiry_from_date or self.expiry_to_date:
            coupon_ids = self.env['wizard.coupon'].search(domain)
            print ('COUNT:', len(coupon_ids))
            for coupon in coupon_ids:
                if not coupon.move_id:
                    coupon.expire_coupon()
                else:
                    if coupon.move_id.date != coupon.expiry_date:
                        coupon.expire_coupon()
        else:
            for coupon in self.env['wizard.coupon'].browse(active_ids):
                if not coupon.move_id:
                    coupon.expire_coupon()
                else:
                    if coupon.move_id.date != coupon.expiry_date:
                        coupon.expire_coupon()



        return {'type': 'ir.actions.act_window_close'}

    def actual_invoice(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        domain = [('state', '=', 'redeem'),('active', '=', True),('type', '=', 'e-coupon')]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.from_date:
            domain.append(('purchase_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('purchase_date', '<=', self.to_date))

        if self.redeem_from_date:
            domain.append(('redeem_date', '>=', self.redeem_from_date))

        if self.redeem_to_date:
            domain.append(('redeem_date', '<=', self.redeem_to_date))


        if self.product_id or self.from_date or self.to_date or self.redeem_from_date or self.redeem_to_date:
            coupon_ids = self.env['wizard.coupon'].search(domain)
            print ('COUNT:',len(coupon_ids))
            for coupon in coupon_ids:
                coupon.create_actual_revenue()
        else:
            for record in self.env['wizard.coupon'].browse(active_ids):
                record.create_actual_revenue()

        return {'type': 'ir.actions.act_window_close'}


    def update_coupons_value(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        domain = [('active', '=', True),('type', '=', 'e-coupon')]
        if self.product_id:
            domain.append(('product_id','=',self.product_id.id))
        if self.from_date:
            domain.append(('purchase_date','>=',self.from_date))
        if self.to_date:
            domain.append(('purchase_date','<=',self.to_date))

        if self.product_id or self.from_date or self.to_date:
            coupon_ids = self.env['wizard.coupon'].search(domain)
            print ('COUNT:', len(coupon_ids))
            for coupon in coupon_ids:
                print (coupon.name)
                coupon.update_coupons_value()
        else:
            for record in self.env['wizard.coupon'].browse(active_ids):
                record.update_coupons_value()

        return {'type': 'ir.actions.act_window_close'}

    def fix_account_entry(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['wizard.coupon'].browse(active_ids):
            for coupon in record:
                if not coupon.order_id and coupon.move_id and coupon.move_id.sudo().company_id.id == 1:
                    coupon.move_id.sudo().button_cancel()
                    coupon.move_id.sudo().unlink()
                elif coupon.order_id.sudo().company_id.id == 1 and coupon.order_branch_id.sudo().company_id.id != 1:
                    coupon.update({'order_id':False})
                    coupon.update({'partner_id':105714})
                    # coupon.update({'partner_id': 105714})
                    if coupon.move_id.sudo():
                        coupon.move_id.sudo().button_cancel()
                        coupon.move_id.sudo().unlink()




    def update_purchase_date(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        domain = [('active', '=', True), ('order_id', '!=', False)]

        if self.from_date:
            domain.append(('order_id.date_order','>=',self.from_date))
        if self.to_date:
            domain.append(('order_id.date_order','<=',self.to_date))

        if self.from_date or self.to_date:
            coupon_ids = self.env['wizard.coupon'].search(domain)
            for coupon in coupon_ids:
                # if coupon.purchase_date != coupon.order_id.date_order.date():
                #     print ('COUPON:',coupon.name)
                coupon.update({'purchase_date': coupon.order_id.date_order})
        else:
            for record in self.env['wizard.coupon'].browse(active_ids):
                for coupon in record:
                    print ('Update PURCHAD Date')
                    coupon.update({'purchase_date': coupon.order_id.date_order})

        return {'type': 'ir.actions.act_window_close'}


    def create_picking(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['wizard.coupon'].browse(active_ids):
            for coupon in record:
                coupon.sudo().create_picking()
        return {'type': 'ir.actions.act_window_close'}