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

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def stock_picking_scheduler(self, max_picking=50):
        # print ('MAX--')
        # print (max_picking)
        # print (self.env.user.company_id.name)
        if max_picking:
            picking_ids = self.search([('origin', 'like', 'CPN/'), ('picking_type_code', '=', 'outgoing'),('state','=','assigned')], limit=max_picking)
        else:
            picking_ids = self.search([('origin', 'like', 'CPN/'), ('picking_type_code', '=', 'outgoing'),('state','=','assigned')])

        # print ('PICKING')
        # print (picking_ids)
        for picking_id in picking_ids:
            # print (picking_id.name)
            if not picking_id.force_date:
                picking_id.update({'force_date': picking_id.scheduled_date})

            if not picking_id.move_lines:
                picking_id.unlink()
            else:
                picking_id.action_cancel()
                picking_id.action_back_to_draft()
                picking_id.action_assign()
                if picking_id.state == 'assigned':
                    # print ('Validate')
                    try:
                        picking_id.force_assign()
                        picking_id.button_validate()
                        picking_id.picking_immediate_process()
                    except:
                        continue

    def picking_immediate_process(self):
        print ('picking_immediate_process')
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in self:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

            print ('picking._check_backorder()')
            print (picking._check_backorder())
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        print ('PICK TO DO')
        print (pick_to_do)
        if pick_to_do:
            print ('ACTION DONE')
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False


class stock_picking_advance_validate(models.TransientModel):
    _name = "stock.picking.advance.validate"


    def picking_immediate_process(self,picking_id):
        print ('picking_immediate_process')
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in picking_id:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

            print ('picking._check_backorder()')
            print (picking._check_backorder())
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        print ('PICK TO DO')
        print (pick_to_do)
        if pick_to_do:
            print ('ACTION DONE')
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False

    def action_validate(self):
        context = self._context
        stock_ping_ids = self.env['stock.picking'].browse(context['active_ids'])
        for stock_picking in stock_ping_ids.filtered(lambda m: m.state != 'done'):
            if not stock_picking.force_date:
                stock_picking.update({'force_date': stock_picking.scheduled_date})
            stock_picking.action_cancel()
            stock_picking.action_back_to_draft()
            stock_picking.action_assign()
            print ('XXX')
            print (stock_picking.state)
            if stock_picking.state == 'assigned':
                stock_picking.button_validate()
                self.picking_immediate_process(stock_picking)


class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    @api.multi
    def create_picking_coupon_scheduler(self, max_coupon=0,com_id=0):
        # picking_coupon_ids = self.env['stock.picking'].sudo().search([('coupon_id', '!=', False)]).mapped('coupon_id')
        # print('create_picking_coupon_scheduler len picking_coupon_ids ', len(picking_coupon_ids))
        if max_coupon:
            if com_id:
                coupons = self.search([('redeem_date', '<=', date.today()),
                                       ('redeem_date', '>=', '2022-09-01'),
                                       ('picking_id', '=', False),
                                       ('order_branch_id.company_id', '=', com_id),
                                       ('state', '=', 'redeem'),
                                       ('product_id.related_service_id.type', 'in', ['product', 'consu'])], limit=max_coupon,
                                      order='redeem_date')
            else:
                coupons = self.search([('redeem_date', '<=', date.today()),
                                       ('redeem_date', '>=', '2022-09-01'),
                                       ('picking_id', '=', False),
                                       ('state', '=', 'redeem'),
                                       ('product_id.related_service_id.type', 'in', ['product', 'consu'])], limit=max_coupon, order='redeem_date')
        else:
            coupons = self.search([('redeem_date', '<=', date.today()),
                                   ('redeem_date', '>=', '2022-09-01'),
                                   ('picking_id', '=', False),
                                   ('state', '=', 'redeem'),
                                   ('product_id.related_service_id.type', 'in', ['product', 'consu'])], order='redeem_date')

        # print('create_picking_coupon_scheduler len coupons ', len(coupons))

        txt = ''

        txt += 'All Coupon:' + str(len(coupons)) + '\r\n'
        start = str(fields.Datetime.now())

        for coupon in coupons:
            print('coupon ', coupon, coupon.name)
            if not coupon.branch_id.sudo():
                coupon.branch_id = coupon.order_branch_id.sudo().id

            if coupon.state == 'redeem':
                try:
                    coupon.sudo().create_picking()
                    txt += 'Coupon:' + coupon.name + ':Done' + '\r\n'
                except:
                    # print ('EXCEPT:')
                    # print (coupon.name)
                    txt += 'Coupon:' + coupon.name + ':Error' + '\r\n'
                    continue
        val = {
            'start': 'create_picking_coupon_scheduler',
            'ava_time': start,
            'expire_time': str(fields.Datetime.now()),
            'total_time': txt,
        }
        self.env['wizard.log'].create(val)
