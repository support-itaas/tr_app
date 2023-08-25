# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models
import requests
import json
from dateutil.relativedelta import relativedelta

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.multi
    def action_pos_order_paid(self):
        super(PosOrder, self).action_pos_order_paid()
        for line in self.lines.filtered(lambda o: o.product_id.gift_voucher_amount):
            order_lenght = len(str(self.id))
            print ('order_lenght',order_lenght)
            print (str(self.id)[0:5])
            code = str(self.partner_id.id) + str(self.id)[order_lenght-3:order_lenght]
            print ('CODE',code)
            voucher_val = {
                'number':code,
                'code': code,
                'start_date': fields.datetime.today(),
                'method': 'special_customer',
                'customer_id':self.partner_id.id,
                'end_date': fields.datetime.today() + relativedelta(days=365),
                'apply_type': 'fixed_amount',
                'value': line.product_id.gift_voucher_amount,
                'source': self.name,
            }
            voucher_id = self.env['pos.voucher'].sudo().create(voucher_val)

            if voucher_id:
                message = 'ยินดีด้วยคุณได้รับ Voucher Promotion มูลค่า ' + str(line.product_id.gift_voucher_amount) + ' Code:' + voucher_id.code + ' กรุณานำโค้ดนี้ไปโชว์ที่สาขาเพื่อเป็นส่วนลดในการสั่งซื้อครั้งต่อไป ที่มีมูลค่ามากกว่า 1000 บาทขึ้นไป'


            print ('VOUCHER')
            voucher_notification = self.env['wizard.notification'].sudo().create({
                'name': 'Congratulations',
                'message': message,
                'read_message': False,
                'partner_id': self.partner_id.id,
                'message_at': fields.Datetime.now(),
            })

            if self.partner_id.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = self.partner_id.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                        ('read_message', '=', False)])

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Voucher Promotion',
                                     'body': 'ยินดีด้วยคุณได้รับ Voucher Promotion',
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': voucher_notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                         data=json.dumps(body))
