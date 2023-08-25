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
import requests
import json
from datetime import date, timedelta

import math
import re


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class ResPartner(models.Model):
    _inherit = 'res.partner'

    number_of_day_extend = fields.Integer(string='Day Extension')

    def update_coupon_day_extension(self):
        coupon_ids = self.env['wizard.coupon'].search(
            [('partner_id', '=', self.id), ('state', '=', 'draft')])
        car_settings = self.env['car.settings'].search([])
        if self.number_of_day_extend:
            day_extend = self.number_of_day_extend
        else:
            if car_settings:
                day_extend = car_settings.number_of_day_extend

        for coupon_id in coupon_ids:
            # print ('DAY EXTEND')
            # print (day_extend)
            # print (coupon_id.expiry_date)
            new_date = strToDate(coupon_id.expiry_date) + relativedelta(days=day_extend)
            # print (new_date)
            coupon_id.update({'expiry_date': new_date})

        self.member_expire_extend_notification()




    def member_expire_extend_notification(self):
        car_settings = self.env['car.settings'].search([])
        if self.number_of_day_extend:
            day_extend = self.number_of_day_extend
        else:
            if car_settings:
                day_extend = car_settings.number_of_day_extend

        if car_settings:
            val_notice = {
                'name': car_settings.extend_subject,
                'message': car_settings.extend_message + ',ขยายวันหมดอายุ: ' + str(day_extend) + ' วัน',
                'read_message': False,
                'partner_id': self.id,
                'message_at': fields.Datetime.now(),
            }
            # print (val_notice)

            notification = self.env['wizard.notification'].create(val_notice)
            if self.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = self.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', self.id),
                                                                        ('read_message', '=', False)])
                if serverToken:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': car_settings.extend_subject,
                                         'body': car_settings.extend_message,
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

