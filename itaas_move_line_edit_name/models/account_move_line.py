# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api ,_
from odoo.exceptions import UserError


class account_move_line_edit_name(models.Model):
    _inherit = "account.move.line"

    @api.model
    def create(self, vals):
        res = super(account_move_line_edit_name, self).create(vals)
        print('/////vals',vals)
        if vals.get('name'):
            name_temp = vals.get('name')
            print('name:',name_temp)
            try:
                name_temp = name_temp.split('-')
                res.update(
                    {'name': name_temp[2]})
            except:
                print('EXCEPT')

        print('/////res',res)
        return res
