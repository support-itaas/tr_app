# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt.Ltd.(<http://www.technaureus.com/>).
from odoo import api, fields, models, _
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta,date

def strToDatetime(strdate):
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # print strdate
    return datetime.strptime(strdate, DATETIME_FORMAT)


class PosSession(models.Model):
    _inherit = "pos.session"

    meter_1_start = fields.Float("มิเตอร์ล้างรถ(P1) เริ่ม")
    meter_1_end = fields.Float("มิเตอร์ล้างรถ(P1) สิ้นสุด")
    meter_2_start = fields.Float("มิเตอร์ล้างรถตู้(P2) เริ่ม")
    meter_2_end = fields.Float("มิเตอร์ล้างรถตู้(P2) สิ้นสุด")
    meter_3_start = fields.Float("มิเตอร์ล้างรถ VIP(P3) เริ่ม")
    meter_3_end = fields.Float("มิเตอร์ล้างรถ VIP(P3) สิ้นสุด")
    meter_4_start = fields.Float("มิเตอร์ล้างรถ(P4) เริ่ม")
    meter_4_end = fields.Float("มิเตอร์ล้างรถ(P4) สิ้นสุด")
    meter_5_start = fields.Float("มิเตอร์ล้างรถรวม เริ่ม")
    meter_5_end = fields.Float("มิเตอร์ล้างรถรวม สิ้นสุด")
    meter_6_start = fields.Float("มิเตอร์ดูดฝุ่น(1) เริ่ม")
    meter_6_end = fields.Float("มิเตอร์ดูดฝุ่น(1) สิ้นสุด")
    meter_7_start = fields.Float("มิเตอร์ดูดฝุ่น(2) เริ่มต้น")
    meter_7_end = fields.Float("มิเตอร์ดูดฝุ่น(2) สิ้นสุด")
    meter_8_start = fields.Float("มิเตอร์ซักพรม เริ่ม")
    meter_8_end = fields.Float("มิเตอร์ซักพรม สิ้นสุด")
    meter_9_start = fields.Float("Meter 9 Start")
    meter_9_end = fields.Float("Meter 9 End")
    meter_10_start = fields.Float("Meter 10 Start")
    meter_10_end = fields.Float("Meter 10 End")
    claim_coupon_ids = fields.Many2many('wizard.coupon', 'coupon_claim_session_rel', 'coupon_id', 'session_id',string='Claim Coupon')
    claim_coupon2_ids = fields.Many2many('wizard.coupon', 'coupon_claim_session_rel', 'coupon_id', 'session_id',string='Claim Coupon')
    use_coupon_by_branch_ids = fields.One2many('wizard.coupon','session_id',string='Use Coupon by Branch')
    use_coupon_by_other_ids = fields.One2many('wizard.coupon', 'session_id', string='Use Coupon by Others')
    branch_amount_total = fields.Float(string="Branch Amount Total", )
    branch_amount_total2 = fields.Float(string="Branch Amount Total", )
    sum_branch_amount_total = fields.Float(string="Branch Amount Total 1 - Branch Amount Total 2")
    sum_branch_amount_total2 = fields.Float(string="Branch Amount Total 1 - Branch Amount Total 2")


    @api.multi
    def check_claim_coupon(self):
        session_date = strToDatetime(self.start_at) + relativedelta(hours=7)
        print (session_date.date())
        coupon_ids = self.env['wizard.coupon'].sudo().search([('redeem_date', '=', session_date.date()),('state', '=', 'redeem'),'|',('branch_id', '=', self.config_id.branch_id.id),('order_branch_id', '=', self.config_id.branch_id.id)])
        print('coupon_ids:', coupon_ids)
        claim_coupon_ids = coupon_ids.filtered(lambda x: x.branch_id != x.order_branch_id)
        print('claim_coupon_ids:', claim_coupon_ids)
        self.claim_coupon_ids = [(6, 0, claim_coupon_ids.ids)]
        print('self.claim_coupon_ids:', self.claim_coupon_ids)

        branch_amount_total = 0.00
        branch_amount_total2 = 0.00
        for coupon in self.claim_coupon_ids:
            if coupon.sudo().order_branch_id.name == self.sudo().config_id.branch_id.name and coupon.sudo().branch_id.name != self.sudo().config_id.branch_id.name:
                print("bbbbbb")
                branch_amount = coupon.destination_branch_amount * -1
                branch_amount2 = coupon.destination_branch_amount
                branch_amount_total += branch_amount
                branch_amount_total2 += branch_amount2
            else:
                branch_amount = coupon.destination_branch_amount
                branch_amount2 = coupon.destination_branch_amount * -1
                branch_amount_total += branch_amount
                branch_amount_total2 += branch_amount2

            coupon.branch_amount = branch_amount
            coupon.branch_amount2 = branch_amount2
            self.branch_amount_total = branch_amount_total
            self.branch_amount_total2 = branch_amount_total2
            self.sum_branch_amount_total = branch_amount_total - branch_amount_total2
            self.sum_branch_amount_total2 = branch_amount_total2 - branch_amount_total
            print("branch_amount:", coupon.branch_amount)
            print("branch_amount_total:", self.branch_amount_total)

            # session_id = self.env['pos.session'].sudo().search([
            #     # ('config_id.branch_id', 'in', (coupon.order_branch_id.id, coupon.branch_id.id)),
            #     ('config_id.branch_id', '=', coupon.branch_id.id),
            # ], limit=1)
            # print("session_id:", session_id)
            #
            # for session in session_id:
            #     session_branch_amount_total.append(session.branch_amount_total)
            #     print("session:",session.branch_amount_total)
            #     print("session_branch_amount_total:",session_branch_amount_total)

                # for  in session_branch_amount_total:
                # print("sum:",session_branch_amount_total[0] - session_branch_amount_total[1])

            # self.sum_branch_amount_total = session_branch_amount_total[0] - session_branch_amount_total[1]




        # print ('claim_coupon_ids:',claim_coupon_ids)
        # coupon_ids.update({'session_id': self.id})

        # self.stock_bom_ids.sudo().unlink()
        # if claim_coupon_ids.sudo():
        #     print("coupon")
        #     for coupon in claim_coupon_ids:
        #         product = coupon.product_id.filtered(lambda x: x.select_stock_bom)
        #         # print('coupon_product :', product)
        #         if product.related_service_id and product.related_service_id.bom_ids:
        #             bom_line_ids = product.related_service_id.bom_ids[0].bom_line_ids
        #             print('coupon_bom_line_ids :', bom_line_ids)
        #             if coupon.session_id.sudo().stock_bom_ids and bom_line_ids:
        #                 for bom in bom_line_ids:
        #                     stock_bom_id = coupon.session_id.sudo().stock_bom_ids.filtered(lambda x: x.product_id == bom.product_id and x.product_uom_id == bom.product_uom_id)
        #                     print('coupon_stock_bom_id:', stock_bom_id)
        #                     if stock_bom_id:
        #                         stock_bom_id.update({
        #                             'product_qty': stock_bom_id.product_qty + bom.product_qty,
        #                         })
        #                     else:
        #                         value = {
        #                             'session_id': self.id,
        #                             'product_id': bom.product_id.id,
        #                             'product_qty': bom.product_qty,
        #                             'product_uom_id': bom.product_uom_id.id,
        #                         }
        #                         self.env['pos.session.bom'].sudo().create(value)
        #             else:
        #                 for bom in bom_line_ids:
        #                     value = {
        #                         'session_id': self.id,
        #                         'product_id': bom.product_id.id,
        #                         'product_qty': bom.product_qty,
        #                         'product_uom_id': bom.product_uom_id.id,
        #                     }
        #                     self.env['pos.session.bom'].sudo().create(value)


    @api.multi
    def action_pos_session_closing_control(self):

        if self.meter_1_end < self.meter_1_start:
            raise UserError(_("Please check meter-1 before close session"))
        if self.meter_2_end < self.meter_2_start:
            raise UserError(_("Please check meter-2 before close session"))
        if self.meter_3_end < self.meter_3_start:
            raise UserError(_("Please check meter-3 before close session"))
        if self.meter_4_end < self.meter_4_start:
            raise UserError(_("Please check meter-4 before close session"))
        if self.meter_5_end < self.meter_5_start:
            raise UserError(_("Please check meter-5 before close session"))
        if self.meter_6_end < self.meter_6_start:
            raise UserError(_("Please check meter-6 before close session"))
        if self.meter_7_end < self.meter_7_start:
            raise UserError(_("Please check meter-7 before close session"))
        if self.meter_8_end < self.meter_8_start:
            raise UserError(_("Please check meter-8 before close session"))
        if self.meter_9_end < self.meter_9_start:
            raise UserError(_("Please check meter-9 before close session"))
        if self.meter_10_end < self.meter_10_start:
            raise UserError(_("Please check meter-10 before close session"))

        return super(PosSession,self).action_pos_session_closing_control()


