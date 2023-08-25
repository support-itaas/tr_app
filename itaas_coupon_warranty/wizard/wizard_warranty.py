# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
from io import BytesIO
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
import xlwt
from decimal import *
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT

class wizard_warranty_record(models.Model):
    _name = 'wizard.warranty.record'

    name = fields.Char(string='Coupon Name')
    date = fields.Datetime(string='Date',default=fields.datetime.today())
    responsible_id = fields.Many2one('res.users',string='User')
    branch_id = fields.Many2one('project.project',string='Branch')

    # def action_confirm(self):
    #     print ('xxx')
    print()
    def create_coupon_warranty(self,):
        print("create_coupon_warranty")
        # warranty_hr = self.env['car.settings'].sudo().search([]).warranty_hr
        coupon_old = self.env['wizard.coupon'].search([('name', '=', self.name), ('state', '=', 'redeem'), ('package_id.is_coupon_warranty', '=', True)], limit=1)

        # warranty_day = self.date - relativedelta(days=warranty_hr / 24)
        # print('warranty_day :', warranty_day)
        # print('coupon_old:', coupon_old)
        # # print('redeem_date:', strToDatetime(coupon_old.redeem_date) - relativedelta(days=warranty_hr / 24))
        # print('redeem_date:', coupon_old.redeem_date)
        # print('date:', self.date)

        # if self.date == coupon_old.redeem_date:
        coupon_id = self.env['wizard.coupon'].create({
            'partner_id': coupon_old.partner_id.id,
            'product_id': coupon_old.product_id.id,
            'order_branch_id': coupon_old.order_branch_id.id,
            'branch_id': coupon_old.branch_id.id,
            'plate_number_id': coupon_old.plate_number_id.id,
            'package_id': coupon_old.package_id.id,
            'barcode': coupon_old.barcode,
            'type': coupon_old.type,
            'note': coupon_old.note,
            'purchase_date': coupon_old.purchase_date,
            'expiry_date': coupon_old.expiry_date,
            'source_operating_unit_id': coupon_old.source_operating_unit_id.id,
            'destination_operating_unit_id': coupon_old.destination_operating_unit_id.id,
        })
        return coupon_id
        # else:
        #     raise UserError(_('ไม่สามารถสร้าง Coupon Warranty เนื่องจากบริการนี้ใช้เกิน 24 ชั่วโมง'))



class wizard_warranty(models.TransientModel):
    _name = 'wizard.warranty'

    name = fields.Char(string='Coupon Number')

    def check_coupon(self):
        # print (self.name)
        warranty_hr = self.env['car.settings'].sudo().search([]).warranty_hr
        print (warranty_hr)

        warranty_day = fields.date.today() - relativedelta(days=warranty_hr/24)
        print (warranty_day)
        cr = self._cr
        cr.execute('SELECT id FROM wizard_coupon WHERE name = %s and state = %s and redeem_date > %s',(self.name,'redeem',str(warranty_day),))
        res = cr.fetchall()
        if not res:
            raise UserError(_('ไม่พบข้อมูล'))
        else:
            cr.execute('SELECT id FROM wizard_warranty_record WHERE name = %s',
                       (self.name,))
            res = cr.fetchall()
            if not res:
                return self.action_confirm()
            else:
                raise UserError(_('มาใช้บริการล้างซ้ำไปแล้ว'))

    def action_confirm(self):
        val = {
            'name':self.name,
            'date': fields.Datetime.now(),
            'responsible_id': self.env.user.id,
        }
        print("val: ",val)
        wiz = self.env['wizard.warranty.record'].sudo().create(val)
        action = self.env.ref('itaas_coupon_warranty.action_coupon_warranty_record').read()[0]
        action['views'] = [(self.env.ref('itaas_coupon_warranty.view_wizard_warranty_confirm_form').id, 'form')]
        action['res_id'] = wiz.id

        return action

    # def action_confirm(self):
    #     action = self.env.ref('account.action_move_journal_line').read()[0]
    #     action['target'] = 'inline'
    #     action['context'] = dict(self.env.context)
    #     action['context']['view_no_maturity'] = False
    #     action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
    #     action['res_id'] = self.copy().id
    #     return action