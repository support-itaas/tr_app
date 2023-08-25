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

def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '0' * (13 - len(ean))
    return ean[:-1] + str(ean_checksum(ean))

class ResPartnerMember(models.Model):
    _name = 'res.partner.member'
    _rec_name = 'level_id'

    level_id = fields.Many2one('membership.type',string='Membership Type')
    product_id = fields.Many2one('product.product', string="Free Coupon on Birthday",domain=[('is_coupon','=',True)])
    coupon_validity = fields.Integer(string='Validity Date')
    special_discount = fields.Float(string='Special Discount %')
    gift = fields.Text(string='Gift - ของรางวัล')
    birth_day_subject = fields.Char(string='Birth Day Subject')
    birth_day_message = fields.Text(string='Birth Day Message')
    branch_id = fields.Many2one('project.project', string="Order Branch")

    @api.multi
    def member_birthday_scheduler(self):
        today = datetime.now().date()
        current_month = calendar.month_name[today.month]
        partner_ids = self.env['res.partner'].search([('is_a_member', '=', True), ('birth_date', '!=', False)])
        print ('Partner IDS')
        # print (xxxx)
        for partner_id in partner_ids:
            birth_date = strToDate(partner_id.birth_date)
            # print (partner_id.name)
            # print (birth_date)
            # # print (partner_id.birth_date.day)
            # print ('today moth',today.month)
            # print ('today.day',today.day)
            # # birth_date_day = 17
            # print('BD moth',birth_date.month)
            # print('BD da', birth_date.day)
            if birth_date.month == today.month and birth_date.day == today.day:
                print ('LET SEND---')
                membership_id = self.env['res.partner.member'].search([('level_id','=',partner_id.membership_level.id)])
                if membership_id.product_id:
                    # print ('GODGOOOO')
                    coupon_id = membership_id.create_coupon(partner_id)
                    if coupon_id:
                        membership_id.member_send_notification(partner_id,coupon_id)
                    else:
                        raise UserError(_("ตรวจสอบการตั้งค่าคูปอง"))
                # if membership_id.

    @api.multi
    def member_coupon_expire_scheduler(self):
        # partner_ids = self.env['res.partner'].search(
        #     [('is_a_member', '=', True), ('birth_date', '!=', False), ('id', '=', 110434)], limit=10)
        today = datetime.now().date()
        expire_in_15_day = today + timedelta(days=15)
        # print ('15 Day')
        # print (expire_in_15_day)
        self.env.cr.execute('SELECT distinct partner_id FROM wizard_coupon WHERE expiry_date=%s and state = %s', (expire_in_15_day,'draft'))
        res = self.env.cr.dictfetchall()

        # print ('Unique Partner')
        # print (res)
        partner_s = []
        if res:
            for partner in res:
                partner_s.append(partner['partner_id'])

        # print (partner_s)
        partner_ids = self.env['res.partner'].browse(partner_s)

        for partner_id in partner_ids:
            self.env['res.partner.member'].coupon_expire_notification(partner_id)



    def create_coupon(self,partner_id):
        coupon_id = self.env['wizard.coupon'].create({
            'partner_id': partner_id.id,
            'product_id': self.product_id.id,
            'order_branch_id': self.branch_id.id,
            'type': 'e-coupon',
            'note': 'Membership Birth Day',
            'purchase_date':date.today(),
            'expiry_date': date.today() + relativedelta(months=2),
        })
        barcode = generate_ean(str(coupon_id.id))
        coupon_id.update({'barcode': barcode})
        coupon_id.update({'expiry_date': date.today() + relativedelta(days=self.coupon_validity)})
        print ('DONE---')
        print ('Coupong',coupon_id.name)
        return coupon_id


    def coupon_expire_notification(self,partner_id):
        val_notice = {
            'name': 'คูปองใกล้หมดอายุ',
            'message': 'คุณมีคูปองใกล้หมดอายุใน 15 วัน กรุณาตรวจสอบใน Wizard App',
            'read_message': False,
            'partner_id': partner_id.id,
            'message_at': fields.Datetime.now(),
        }
        # print (val_notice)

        notification = self.env['wizard.notification'].create(val_notice)
        if partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            deviceToken = partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'คูปองใกล้หมดอายุ',
                                     'body': 'คุณมีคูปองใกล้หมดอายุใน 15 วัน กรุณาตรวจสอบใน Wizard App',
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

    def member_send_notification(self,partner_id,coupon_id):
        val_notice = {
            'name': self.birth_day_subject,
            'message': self.birth_day_message + ',หมายเลขคูปองอ้างอิง:' + str(coupon_id.name),
            'read_message': False,
            'partner_id': partner_id.id,
            'message_at': fields.Datetime.now(),
        }
        # print (val_notice)

        notification = self.env['wizard.notification'].create(val_notice)
        if partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            deviceToken = partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': self.birth_day_subject,
                                     'body': self.birth_day_message,
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



