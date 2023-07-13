# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).


from odoo import http


class Action(http.Controller):

    @http.route('/web/action/create_appointment', type='json', auth="user")
    def create_appointment(self, partner_id=None, branch_id=None, slot_id=None, appointment_date=None, type=None,
                           coupon_id=None):
        if partner_id and branch_id and slot_id and appointment_date and type and coupon_id:
            app_id = http.request.env['appointment.appointment'].sudo().create({
                'partner_id': partner_id,
                'branch_id': branch_id,
                'slot_id': slot_id,
                'appointment_date': appointment_date,
                'type': type,
                'coupon_id': coupon_id,
            })
        else:
            return False

    @http.route('/web/action/transfer', type='json', auth="user")
    def transfer(self, partner_id=None, coupon_id=None, note=None):
        if partner_id and coupon_id and note:
            coupon = http.request.env['wizard.coupon'].sudo().search([('id', '=', data['coupon_id'])])
            coupon.write({
                'coupon_id': coupon_id,
                'partner_id': partner_id,
                'note': note,
            })
        else:
            return False

    @http.route('/web/action/redeem', type='json', auth="user")
    def redeem(self, coupon_id=None, plate_number_id=None):
        if coupon_id and plate_number_id:
            coupon = http.request.env['wizard.coupon'].sudo().search([('id', '=', coupon_id)])
            coupon.write({
                'plate_number_id': plate_number_id
            })
            coupon.button_redeem()
        else:
            return False

    @http.route('/web/action/balance', type='json', auth="user")
    def balance(self, partner_id):
        if partner_id:
            partner = http.request.env['res.partner'].sudo().search([('id', '=', partner_id)])
            return abs(partner.credit)
        else:
            return 0.0

    @http.route('/web/action/add_money', type='json', auth="user")
    def add_money(self, partner_id=None, amount=None, payment_journal=None, branch_id=None):
        if partner_id and amount and payment_journal and branch_id:
            journal_id = http.request.env['account.journal'].sudo().search([('type', '=', payment_journal)])
            payment_method_ids = http.request.env['account.journal'].sudo().browse(journal_id). \
                _default_inbound_payment_methods()
            money = http.request.env['account.payment'].sudo().create({
                'partner_id': partner_id,
                'branch_id': branch_id,
                'amount': amount,
                'journal_id': journal_id.id,
                'payment_type': 'inbound',
                'add_to_wallet': True,
                'payment_method_id': payment_method_ids[0].id
            })
        else:
            return False

    @http.route('/web/action/get_plate', type='json', auth="user")
    def get_plate(self, partner_id):
        if partner_id:
            partner = http.request.env['res.partner'].sudo().search([('id', '=', partner_id)])
            cars = {}
            for car in partner.car_ids:
                cars.update({car.id: car.name})
            return cars
        else:
            return False

    @http.route('/web/action/create_profile', type='json', auth="user")
    def create_profile(self, image=None, company_type=None, name=None, last_name=None, car_id=None, title=None,
                       gender=None, birth_date=None, mobile=None, line_id=None,
                       email=None, street=None, member=None, member_number=None, member_date=None,
                       base_branch_id=None):
        if name:
            car = car_id.replace(" ", "")
            partner = http.request.env['res.partner'].sudo().create({
                'image': image,
                'company_type': company_type,
                'name': name,
                'last_name': last_name,
                'title': title,
                'gender': gender,
                'birth_date': birth_date,
                'mobile': mobile,
                'line_id': line_id,
                'email': email,
                'street': street,
                'member': member,
                'member_number': member_number,
                'member_date': member_date,
                'base_branch_id': base_branch_id,
                'car_ids': [(0, 0, {
                    'name': car,
                    'is_primary': True
                })]
            })
        else:
            return False

    @http.route('/web/action/update_profile', type='json', auth="user")
    def update_profile(self, partner_id=49, company_type=None, name=None, car_id=None, last_name=None, title=None, gender=None,
                       birth_date=None, mobile=None, line_id=None,
                       email=None, street=None, member=None, member_number=None, member_date=None,
                       base_branch_id=None):
        if partner_id:
            partner_rec = http.request.env['res.partner'].sudo().search([('id', '=', partner_id)])
            car = car_id.replace(" ", "")
            for c in partner_rec.car_ids:
                if c.is_primary:
                    c.name = car
            partner_rec.sudo().update({
                'company_type': company_type,
                'name': name,
                'last_name': last_name,
                'title': title,
                'gender': gender,
                'birth_date': birth_date,
                'mobile': mobile,
                'line_id': line_id,
                'email': email,
                'street': street,
                'member': member,
                'member_number': member_number,
                'member_date': member_date,
                'base_branch_id': base_branch_id,

            })
        else:
            return False

    @http.route('/web/action/member_color', type='json', auth="user")
    def member_color(self, partner_id=None):
        if partner_id:
            partner = http.request.env['res.partner'].sudo().search([('id', '=', partner_id)])
            return partner.membership_type_id.color
        else:
            return False

    @http.route('/web/action/signup', type='json', auth="user")
    def signup(self, mobile=None, otp=None, expiry_date=None, password=None):
        if mobile and otp and expiry_date:
            otp = http.request.env['wizard.otp'].sudo().create({
                'mobile': mobile,
                'otp': otp,
                'expiry_date': expiry_date,
                'password': password,
            })
        else:
            return False
