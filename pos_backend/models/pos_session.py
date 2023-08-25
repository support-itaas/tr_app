# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class Pos_Session(models.Model):
    _inherit = 'pos.session'

    mister_1_s = fields.Float('มิตเตอร์1_s')
    mister_1_e = fields.Float('มิตเตอร์1_e')
    mister_2_s = fields.Float('มิตเตอร์2_s')
    mister_2_e = fields.Float('มิตเตอร์2_e')
    mister_3_s = fields.Float('มิตเตอร์3_s')
    mister_3_e = fields.Float('มิตเตอร์3_e')
    mister_4_s = fields.Float('มิตเตอร์4_s')
    mister_4_e = fields.Float('มิตเตอร์4_e')
    mister_vacuum_1_s = fields.Float('มิตเตอร์ เครื่องดูดฝุ่น1_s')
    mister_vacuum_1_e = fields.Float('มิตเตอร์ เครื่องดูดฝุ่น1_e')
    mister_vacuum_2_s = fields.Float('มิตเตอร์ เครื่องดูดฝุ่น2_s')
    mister_vacuum_2_e = fields.Float('มิตเตอร์ เครื่องดูดฝุ่น2_e')
    mister_cleaner_s = fields.Float('มิตเตอร์ เครื่องทำความสะอาด_s')
    mister_cleaner_e = fields.Float('มิตเตอร์ เครื่องทำความสะอาด_e')


