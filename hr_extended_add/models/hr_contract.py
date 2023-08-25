#-*-coding: utf-8 -*-
from odoo import api, fields, models, _

class hr_payroll_yearly_record(models.Model):
    _inherit = "hr.payroll.yearly.record"

    total_revenue_summary_for_tax_one = fields.Float(string='รายได้ไม่คงที่สำหรับคิดภาษีบุคคลธรรมดาสะสม')
    total_tax_one_paid = fields.Float(string='ภาษีบุคคลธรรมดา หัก ณ ที่จ่ายสะสม ต่อหนึ่งเดือน')


class contract_branch(models.Model):
    _inherit = 'contract.branch'

    partner_id = fields.Many2one('res.partner', string='Partner')
    description = fields.Char(string='Description')
    bank_ac = fields.Char(string='Bank Account')

    building = fields.Char(string='building', size=64)
    roomnumber = fields.Char(string='roomnumber', size=32)
    floornumber = fields.Char(string='floornumber', size=32)
    village = fields.Char(string='village', size=64)
    house_number = fields.Char(string='house_number', size=20)
    moo_number = fields.Char(string='moo_number', size=20)
    soi_number = fields.Char(string='soi_number', size=24)
    tumbon = fields.Char(string='tumbon', size=24)

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')

