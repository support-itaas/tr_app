#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo import api, tools
from odoo.osv import osv
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

class res_comapany(models.Model):
    _inherit = 'res.company'

    is_create_employee_code = fields.Boolean(string='Auto Employee Code')

class hr_employee(models.Model):
    _inherit = "hr.employee"

    #tax_accomulate
    bank_account = fields.Char(string="Bank Account Number")
    bank_name = fields.Char(string="Bank Name")
    bank_note = fields.Char(string="Bank Note")
    employee_code = fields.Char(string="Employee Code",copy=False)
    sso_id = fields.Char(string="SSO ID")
    region = fields.Selection([('Buddhist', 'พุทธ'), ('Christian', 'คริส'), ('Islam', 'อิสลาม'), ('Others', 'อื่นๆ')],string="Region")
    military_status = fields.Char("Military Status")
    id_issue_date = fields.Date(string='ID issue date')
    id_expiry_date = fields.Date(string='ID expiry date')
    home_address = fields.Text(string='Home Address Detail')
    current_address = fields.Text(string='Current Address Detail')
    title = fields.Many2one('res.partner.title',string='Title')
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    is_temp_dept = fields.Boolean("Temp department", related='department_id.is_temp_dept')
    job_category = fields.Char(related='job_id.job_category.name', store=True)
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")


    _sql_constraints = [
        ('uniq_name_id', 'unique(identification_id,company_id)', "ID can't duplicate"),
        ('uniq_name_passport_id', 'unique(passport_id,company_id)', "Passport can't duplicate"),
        ('uniq_name_sso_id', 'unique(sso_id,company_id)', "SSO ID can't duplicate"),
        ('uniq_employee_code', 'unique(employee_code,company_id)', "Employee Code ID can't duplicate"),
    ]

    @api.onchange('operating_unit_id')
    def onchange_operating_unit_id(self):
        print('onchange_operating_unit_id')
        if self.operating_unit_id:
            # self.contract_id.operating_unit_id = self.operating_unit_id.id
            self.contract_id.write({
                'operating_unit_id': self.operating_unit_id.id,
            })


    @api.onchange('first_name', 'last_name')
    def onchange_name(self):
        space = ' '
        self.name = (self.first_name or '') + space + (self.last_name or '')

    @api.onchange('birthday')
    def _onchange_birth_date(self):
        """Updates age field when birth_date is changed"""
        if self.birthday:
            d1 = datetime.strptime(self.birthday, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
            age_year = str(self.age)
            age_month = str(relativedelta(d2, d1).months)
            age_day = str(relativedelta(d2, d1).days)
            self.age_full = (age_year or '') + ' ปี ' + (age_month or '') + ' เดือน ' + (age_day or '') + ' วัน'

    @api.model
    def update_ages(self):
        """Updates age field for all partners once a day"""
        for rec in self.env['hr.employee'].search([]):
            if rec.birthday:
                d1 = datetime.strptime(rec.birthday, "%Y-%m-%d").date()
                d2 = date.today()
                rec.age = relativedelta(d2, d1).years
                age_year = str(rec.age)
                age_month = str(relativedelta(d2, d1).months)
                age_day = str(relativedelta(d2, d1).days)
                rec.age_full = (age_year or '') + ' ปี ' + (age_month or '') + ' เดือน ' + (age_day or '') + ' วัน'

    @api.model
    def create(self, vals):
        if self.env.user.company_id.is_create_employee_code:
            vals['employee_code'] = self.env['ir.sequence'].next_by_code('emp.no')
        return super(hr_employee, self).create(vals)

    @api.onchange('department_id')
    def onchange_employee_department_id(self):
        result = {}
        if self.department_id:
            job_ids = self.env['hr.job'].search([('department_id','=',self.department_id.id)])
            if job_ids:
                jobs = []
                for job in job_ids:
                    jobs.append(job.id)
                    result['domain'] = {'job_id': [('id', 'in', jobs)]}
            self.parent_id = self.department_id.manager_id.id

        return result

class hr_department(models.Model):
    _inherit = "hr.department"

    # allow_access = fields.Boolean("อนุญาติให้เข้าถึงได้",default=False)
    is_temp_dept = fields.Boolean("Temp department",default=False)


class hr_job_categ(models.Model):
    _name = 'hr.job.categ'
    _description = 'HR JOB Level'

    name = fields.Char("JOB Level", required=True)
    code = fields.Integer("Code", required=True)


class hr_job(models.Model):
    _inherit = "hr.job"

    job_category = fields.Many2one("hr.job.categ")
