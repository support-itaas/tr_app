# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError

class account_cheque_statement(models.Model):
    _inherit = "account.cheque.statement"


    @api.constrains('cheque_number')
    def _check_cheque_payment_unique(self):
        # This constraint could possibly underline flaws in bank statement import (eg. inability to
        # support hacks such as using dummy transactions to give additional informations)

        for cheque_record in self:
            if cheque_record.cheque_number:
                cr = self._cr
                cr.execute('SELECT id FROM account_cheque_statement WHERE cheque_number = %s and type = %s', (cheque_record.cheque_number,'pay',))
                res = cr.fetchall()
                if len(res) > 1 and cheque_record.cheque_number != '':
                    raise ValidationError(_('หมายเลขเช็ค %s มีอยู่แล้ว') % cheque_record.cheque_number)