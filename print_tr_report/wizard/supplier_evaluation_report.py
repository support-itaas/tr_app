# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, models, fields, _
from datetime import datetime, date
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import pytz

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class wizard_suplier_evaluation(models.TransientModel):
    _name = 'wizard.suplier.evaluation'

    partner_ids = fields.Many2many('res.partner', string='Partner')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    total_supplier = fields.Integer(string='Total Supplier')
    from_no = fields.Integer(string='Start From',default=1)
    to_no = fields.Integer(string='End To')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    report_type = fields.Selection([('type_2', 'สรุปการประเมินผู้ขาย'),('type_1', 'การประเมินผู้ขาย')], string='Report type'
                                   ,default='type_2')
    industry_id = fields.Many2one('res.partner.industry',string='Industry')

    @api.onchange('date_from','date_to','industry_id')
    def onchange_date_from_to(self):
        domain = [('date','>=',self.date_from),('date','<=',self.date_to)]
        if self.industry_id:
            domain += [('partner_id.industry_id','>=',self.industry_id.id)]
        supplier_ids = self.env['supplier.evaluation.line'].search(domain)
        supplier = []
        if supplier_ids:
            supplier = supplier_ids.mapped('partner_id')

        self.total_supplier = len(supplier)
        self.to_no = len(supplier)

    @api.model
    def default_get(self, fields):
        res = super(wizard_suplier_evaluation, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, 1, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def print_pdf_report(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'report_type', 'partner_ids', 'industry_id','company_id','from_no','to_no'])[0]
        if data['form']['report_type'] == 'type_1':
            return self.env.ref('print_tr_report.report_supplier_evaluation').report_action(self, data=data,
                                                                                            config=False)
        elif data['form']['report_type'] == 'type_2':
            return self.env.ref('print_tr_report.supplier_assessment_report').report_action(self, data=data,
                                                                                            config=False)

    def get_function_eval(self, date_from, date_to, partner_id):
        print ('def get_function_eval')
        type_ids = self.env['evaluation.type'].search([])
        if type_ids:
            i = 0
            val_line_s = {}

            for type in type_ids:
                evaluation_ids = self.env['supplier.evaluation.line'].search(
                    [('date', '>=', date_from), ('date', '<=', date_to),
                     ('partner_id', '=', partner_id),('name', '=', type.id)])
                if evaluation_ids:
                    num_t = 0
                    num_f = 0
                    for eval in evaluation_ids:

                        found = False
                        if i > 0:
                            # print "more than one"
                            for x in range(0, i):
                                # print "start top loop"

                                if eval.name.id == val_line_s[x]['name']:
                                    found = True
                                    # print "found same product"
                                    if eval.pass_fail:
                                        val_line_s[x]['num_t'] += 1
                                    else:
                                        val_line_s[x]['num_f'] += 1
                                    break

                            if not found:
                                # print "not found same product"
                                print ("not found same product")

                                if eval.pass_fail:
                                    num_t += 1
                                else:
                                    num_f += 1

                                val_line_s[i] = {
                                    'name': eval.name.id,
                                    'num_t': int(num_t),
                                    'num_f': int(num_f),
                                }
                                i += 1
                        # first time
                        else:
                            # print "First done"
                            if eval.pass_fail:
                                num_t += 1
                            else:
                                num_f += 1

                            val_line_s[i] = {
                                'name': eval.name.id,
                                'num_t': num_t,
                                'num_f': num_f,
                            }
                            i += 1

            val_line_s = [value for key, value in val_line_s.items()]
            if val_line_s:
                print ('val_line_s-----1')
                type_ids1 = self.env['evaluation.type'].search([('name', '=ilike', 'คุณภาพ' + '%')], limit=1)
                type_ids2 = self.env['evaluation.type'].search([('name', '=ilike', 'ส่งมอบ' + '%')], limit=1)
                total_1 = 0
                total_2 = 0
                for vals in val_line_s:
                    if vals['name'] == type_ids1.id:
                        total_1 += ((vals['num_t']*70)/(vals['num_t']+vals['num_f']))
                    if vals['name'] == type_ids2.id:
                        total_2 += ((vals['num_t'] * 30) / (vals['num_t'] + vals['num_f']))
                t_total = total_1 + total_2
                if t_total > 90:
                    grade = 'A'
                elif t_total > 80 and t_total < 91:
                    grade = 'B'
                elif t_total > 69 and t_total < 81:
                    grade = 'C'
                else:
                    grade = 'F'

            return grade

        # val_line_s = {}
        #
        # i = 0
        # num_t = 0
        # num_f = 0
        #
        # evaluation_ids = self.env['supplier.evaluation.line'].search(
        #     [('date', '>=', date_from), ('date', '<=', date_to),
        #      ('partner_id', '=', partner_id)])
        #
        #
        # for eval in evaluation_ids:
        #
        #     found = False
        #     if i > 0:
        #         # print "more than one"
        #         for x in range(0, i):
        #             # print "start top loop"
        #
        #             if eval.name.id == val_line_s[x]['name']:
        #                 # print "found same product"
        #                 if eval.pass_fail:
        #                     val_line_s[x]['num_t'] += 1
        #                 else:
        #                     val_line_s[x]['num_f'] += 1
        #                 break
        #
        #         if not found:
        #             # print "not found same product"
        #             if eval.pass_fail:
        #                 num_t += 1
        #             else:
        #                 num_f += 1
        #
        #             val_line_s[i] = {
        #                 'name': eval.name.id,
        #                 'id': eval,
        #                 'num_t': num_t,
        #                 'num_f': num_f,
        #             }
        #             i += 1
        #     # first time
        #     else:
        #         # print "First done"
        #         if eval.pass_fail:
        #             num_t += 1
        #         else:
        #             num_f += 1
        #
        #         val_line_s[i] = {
        #             'name': eval.name.id,
        #             'id': eval,
        #             'num_t': num_t,
        #             'num_f': num_f,
        #         }
        #         i += 1
        #
        # val_line_s = [value for key, value in val_line_s.items()]
        # print (val_line_s)
        # return val_line_s

    def get_score_supplier_evaluation(self, supplier_evaluation_ids, date_from, date_to):
        type_quality = self.env['supplier.evaluation.line'].search([('id', 'in', supplier_evaluation_ids.ids),
                                                                    ('name', '=ilike', '%' +'quality' +'%'),
                                                                    ('date', '>=', date_from),
                                                                    ('date', '<=', date_to)])
        type_delivery = self.env['supplier.evaluation.line'].search([('id', 'in', supplier_evaluation_ids.ids),
                                                                     ('name', '=ilike', '%' +'delivery'+ '%'),
                                                                     ('date', '>=', date_from),
                                                                     ('date', '<=', date_to)])

        return_type_quality = len(type_quality.filtered(lambda x: x.is_return))
        pass_type_quality = len(type_quality.filtered(lambda x: x.pass_fail))
        score_pass_type_quality = (pass_type_quality * 70) / len(type_quality)
        pass_type_delivery = len(type_delivery.filtered(lambda x: x.pass_fail))
        score_pass_type_delivery = (pass_type_delivery * 30) / len(type_delivery)

        score_total = score_pass_type_quality + score_pass_type_delivery
        if score_total > 90:
            grade = 'A'
        elif score_total > 80 and score_total < 91:
            grade = 'B'
        elif score_total > 69 and score_total < 81:
            grade = 'C'
        else:
            grade = 'F'

        return {'type_quality': len(type_quality),
                'pass_type_quality': pass_type_quality,
                'fail_type_quality': len(type_quality) - pass_type_quality,
                'return_type_quality': return_type_quality,
                'score_quality': score_pass_type_quality,
                'type_delivery': len(type_delivery),
                'pass_type_delivery': pass_type_delivery,
                'fail_type_delivery': len(type_delivery) - pass_type_delivery,
                'score_delivery': score_pass_type_delivery,
                'score_total': score_total,
                'grade': grade,
                }


class report_supplier_assessment(models.AbstractModel):
    _name = 'report.print_tr_report.supplier_assessment_report_id'

    @api.multi
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        date_from = datetime.strptime(str(data['form']['date_from']), DEFAULT_SERVER_DATE_FORMAT)
        year = date_from.year
        # date_from = self.convert_usertz_to_utc(date_from)
        # date_to = datetime.strptime(str(data['form']['date_to']) + " 23:59:59", DEFAULT_SERVER_DATETIME_FORMAT)
        # date_to = self.convert_usertz_to_utc(date_to)

        print('date_from : ', data['form']['date_from'])
        print('date_to : ',data['form']['date_to'])


        evaluation_ids = self.env['supplier.evaluation.line'].search([('date', '>=', data['form']['date_from']),
                                                                      ('date', '<=', data['form']['date_to']),])
        supplier_ids = evaluation_ids.mapped('partner_id')
        if data['form']['industry_id']:
            # print (data['form']['industry_id'][0])
            supplier_ids = supplier_ids.filtered(lambda x: x.industry_id.id == data['form']['industry_id'][0])

        print('year:',year)
        return {
            'doc_ids': docids,
            'doc_model': 'supplier.evaluation.line',
            'docs': docs,
            'supplier_ids': supplier_ids,
            'evaluation_ids': evaluation_ids,
            'data': data['form'],
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'year': year,
        }

    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time


