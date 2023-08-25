# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models
from datetime import date, datetime

class report_supplier_evaluation_report(models.AbstractModel):
    _name = 'report.print_tr_report.report_supplier_evaluation_id'

    @api.multi
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        date_from = datetime.strptime(str(data['form']['date_from']) + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        date_to = datetime.strptime(str(data['form']['date_to']) + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        print('date_to:',date_to)

        supplier_ids = []
        new_supplier_ids = []

        if data['form']['partner_ids']:

            supplier_ids = self.env['res.partner'].search(
                [('id', 'in', data['form']['partner_ids']), ('supplier', '=', True)])

        else:
            for eval in self.env['supplier.evaluation.line'].search([('date','>=',date_from),('date','<=',date_to)]):
                if eval.partner_id not in supplier_ids:
                    supplier_ids.append(eval.partner_id)

        len_partner = data['form']['to_no'] - data['form']['from_no']

        if len(supplier_ids) > len_partner:
            from_no = data['form']['from_no'] -1
            to_no = data['form']['to_no'] -1
            for x in range(from_no,to_no,1):
                new_supplier_ids.append(supplier_ids[x])

        if new_supplier_ids:
            supplier_ids = new_supplier_ids

        # now1 = date.today()
        month_name = 'x ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.'.split()[date_to.month]
        thai_year = date_to.year + 543
        print('thai_year:',thai_year)
        to_days = "%d %s %d" % (date_to.day, month_name, thai_year)
        to_year = "%d" % (thai_year)
        print('to_year:', to_year)

        date_from1 = datetime.strptime(data['form']['date_from'], '%Y-%m-%d')
        month_name1 = 'x ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.'.split()[date_from1.month]
        date_to1 = datetime.strptime(data['form']['date_to'], '%Y-%m-%d')
        month_name2 = 'x ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.'.split()[date_to1.month]
        t_month_y = str(month_name1) + ' - ' + str(month_name2) + ' ' + str(to_year)

        return {
            'doc_ids': docids,
            'doc_model': 'supplier.evaluation.line',
            'docs': docs,
            'supplier_ids':supplier_ids,
            'data': data['form'],
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'to_days': to_days,
            'to_year': to_year,
            't_month_y': t_month_y,

        }










    
