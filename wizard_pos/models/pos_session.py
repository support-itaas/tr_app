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
    claim_coupon_ids = fields.Many2many('wizard.coupon', 'coupon_claim_session_rel', 'coupon_id', 'session_id',
                                           string='Claim Coupon')
    use_coupon_by_branch_ids = fields.One2many('wizard.coupon','session_id',string='Use Coupon by Branch')
    use_coupon_by_other_ids = fields.One2many('wizard.coupon', 'session_id', string='Use Coupon by Others')


    @api.multi
    def check_claim_coupon(self):
        session_date = strToDatetime(self.start_at) + relativedelta(hours=7)
        print (session_date.date())
        coupon_ids = self.env['wizard.coupon'].search([('redeem_date', '=', session_date.date()),('state', '=', 'redeem'),'|',('branch_id', '=', self.config_id.branch_id.id),('order_branch_id', '=', self.config_id.branch_id.id)])
        claim_coupon_ids = coupon_ids.filtered(lambda x: x.branch_id != x.order_branch_id)
        self.claim_coupon_ids = [(6, 0, claim_coupon_ids.ids)]
        # print (coupon_ids)
        # coupon_ids.update({'session_id': self.id})

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


