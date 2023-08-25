# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare

_STATES = [
    ('draft', 'Draft'),
    ('to_mkt_approve', 'To MKT Approve'),
    ('to_approve', 'To be approved'),
    ('to_waiting', 'Waiting To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('done', 'Done')
]

class res_group(models.Model):
    _inherit = 'res.groups'

    group_name = fields.Char('Group name')
    pr_id = fields.Many2one('purchase.request' ,string='PR Id')
    po_id = fields.Many2one('purchase.order', string='PO Id')
    order = fields.Integer(string='Order')

class purchase_type(models.Model):
    _name = 'purchase.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Purchase Type')
    description = fields.Text(string='Description')
    user_ids = fields.Many2many('res.users', 'user_ids_1_level', string='Default User Email')
    user_ids_2_level = fields.Many2many('res.users', 'user_ids_2_level', string='Default User Email 2')

class Purchase_request_s(models.Model):
    _inherit = 'purchase.request'

    emp_id = fields.Many2one('hr.employee',string='Related Employee')
    department_id = fields.Many2one('hr.department',string='Department')
    # allow_group_ids = fields.One2many('res.groups','pr_id',string='Allow Groups',store=True)
    allow_group_ids = fields.Many2many('res.groups', string='Allow Groups',compute='_get_allow_group',store=True)
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')


    ########### Used
    check_uid = fields.Many2one('res.users', 'Check By',
                                track_visibility='onchange')

    check_date = fields.Date(string="Checked Date")

    approve_date = fields.Date(string="Approve Date")
    approve_uid = fields.Many2one('res.users', string="Purchase Request Approve")

    name = fields.Char('Request Reference', size=32, required=True,
                       default='New',
                       track_visibility='onchange')

    purchase_type = fields.Many2one('purchase.type',string='Purchase Type')
    order_type = fields.Many2one('purchase.order.type', string="Purchase Order Type")
    # ----------------------------------------------------------------------------
    # division_id = fields.Many2one('hr.department',string='Division')
    # location_id = fields.Many2one('res.partner',string='Location',readonly=1)
    # section_id = fields.Many2one('hr.department', string='Section')
    # addition = fields.Selection([('1', 'Manual'), ('2', 'Certificate'), ('3', 'Other'), ('4', 'None')], string="Addition Requirement")
    # mkt_approver = fields.Many2one('res.users',string='MKT Approver')

    # to_approve_date = fields.Date(string="Request Date")
    # to_approve_uid = fields.Many2one('res.users', string="Purchase Request")


    # approvate_date_time = fields.Char(string='Approve Date To Use',compute='get_approvate_date_time')
    # approvated_chk = fields.Boolean('Approvated Chk',default=False)
    # approvate_pr_to_po = fields.Char(string='Pr Date To Po Date')
    # pr_to_po_chk = fields.Boolean('Pr To Po Chk', default=False)
    ########### Don't use yet
    # analytic_account_id = fields.Many2one('account.analytic.account',
    #                                       'Job No',required=1,
    #                                       track_visibility='onchange')

    # project_id = fields.Many2one('project.project',string='Project',compute='_get_project_id',store=True)

    # project_budget_ids = fields.One2many('purchase.budget.line','purchase_request_id',string='Budget Info')
    # total_budget = fields.Float(string='Total Budget',compute='get_budget',store=True)
    # total_expense = fields.Float(string='Total Expense', compute='get_budget', store=True)
    # budget_status = fields.Selection([('under_budget','Under Budget'),('over_section_under_total_budget','Over Section Budget - Under Total Budget'),('over_budget','Over Budget')],compute='_check_budget_status',string='Budget Status',store=True)


    # validate_uid = fields.Many2one('res.users', string="Authorized Person")
    # validate_date = fields.Date(string="Validated Date")

    # request_date = fields.Date(string="Request Date")
    # request_uid = fields.Many2one('res.users', string="Purchase Request")
    # ---------------------------------------------------------------------------------

    @api.multi
    def button_draft(self):
        is_po = False
        for line in self.line_ids:
            if line.purchase_state != False:
                is_po = True
                break

        if self.state == 'approved' and is_po and not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_('Only purchase manager can cancel PR which was approved and created PO'))
        res = super(Purchase_request_s, self).button_draft()

        return res

    @api.multi
    def button_rejected(self):
        is_po = False
        self.pr_to_po_chk = False
        self.approvated_chk = False
        for line in self.line_ids:
            if line.purchase_state != False:
                is_po = True
                break

        if self.state == 'approved' and is_po and not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_('Only purchase manager can reject PR which was approved and created PO'))
        self.assigned_to = False
        res = super(Purchase_request_s, self).button_rejected()

        return res

    @api.multi
    @api.depends('state')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve','approved', 'rejected', 'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.onchange('requested_by','allow_group_ids','line_ids','line_ids.sub_total')
    def get_hr_emp(self):
        ''
        # print '_get_employee'
        # obj_user = self
        for obj_user in self:
            obj_emp = self.env['hr.employee'].search([('user_id','=',obj_user.requested_by.id)],limit=1)

            obj_user._get_allow_group()

            if obj_emp:
                obj_user.emp_id = obj_emp.id
                obj_user.department_id= obj_emp.department_id.id

                # obj_user.write({'department_id': obj_emp.department_id.id})
                # print "-----11111--"
                # print self.allow_group_ids
                found = False
                for group in self.allow_group_ids.sudo().sorted(lambda x: x.order):

                    # ################department structure
                    # department_id = obj_emp.department_id.id
                    # print "GROUP"
                    # print group.comment
                    # print obj_emp.department_id
                    # print obj_emp.department_id.parent_id
                    # print obj_emp.department_id.parent_id.parent_id
                    # print obj_emp.department_id.parent_id.manager_id
                    # print obj_emp.department_id.parent_id.parent_id.manager_id
                    # print obj_emp.department_id.parent_id.manager_id.user_id.name
                    # print obj_emp.department_id.parent_id.parent_id.manager_id.user_id.name
                    # print obj_emp.department_id.parent_id.manager_id.user_id.has_group(group.comment)

                    if obj_emp.department_id and obj_emp.department_id.manager_id and obj_emp.department_id.manager_id.user_id.sudo().has_group(group.comment):
                        ############## Assign department manager as approval
                        print ('Dep Manager')
                        obj_user.assigned_to = obj_emp.department_id.manager_id.user_id.id
                        found = True
                        break

                    elif obj_emp.department_id and obj_emp.department_id.parent_id and obj_emp.department_id.parent_id.manager_id and obj_emp.department_id.parent_id.manager_id.user_id.sudo().has_group(group.comment):
                        ########### Assigned manager of parent department as approval
                        print ("2222222222")
                        obj_user.assigned_to = obj_emp.department_id.parent_id.manager_id.user_id.id
                        found = True
                        break

                    elif obj_emp.department_id and obj_emp.department_id.parent_id and obj_emp.department_id.parent_id.parent_id and obj_emp.department_id.parent_id.parent_id.manager_id and obj_emp.department_id.parent_id.parent_id.manager_id.user_id.sudo().has_group(group.comment):
                        ########### Assigned manager of parent department as approval
                        print ("33333333")
                        obj_user.assigned_to = obj_emp.department_id.parent_id.parent_id.manager_id.user_id.id
                        found = True
                        break

                if not found:
                    # print "NOT FOUND"
                    for group in self.allow_group_ids.sudo().sorted(key=lambda r: r.name):
                        if group.comment == 'po_approval.group_dmd' or group.comment == 'po_approval.group_md' and group.users:
                            # print group.comment
                            print ("4")
                            obj_user.assigned_to = group.users[0].id
                            break

    @api.depends('total_amount')
    def _get_allow_group(self):
        # print '_get_allow_group'
        for pr in self:
            total_amount = int(pr.total_amount)
            group_ids = []
            allow_approve_group_ids = self.env['purchase.approval.matrix'].search([('purchase_type','=',pr.purchase_type.id),('type','=','PR'),('max_amount','>=',total_amount)], order='max_amount desc')
            for group in allow_approve_group_ids:
                group_ids.append(group.group_id.id)

            # print group_ids

            pr.update({
                'allow_group_ids': [(6, 0, group_ids)]
            })

            # print ("_get_allow_group")
            # print (pr.allow_group_ids)

    # @api.onchange('analytic_account_id')
    # def onchange_analytic(self):
    #     for line in self.line_ids:
    #         line.analytic_account_id = self.analytic_account_id.id


    # @api.model
    # def create(self, vals):
    #     request = super(Purchase_request_s, self).create(vals)
    #     request.write({'name': self.env['ir.sequence'].next_by_code('purchase.request'), })
    #     if vals.get('check_uid'):
    #         request.message_subscribe_users(user_ids=[request.check_uid.id])
    #     return request
    # @api.model
    # def create(self, vals):
    #     request = super(Purchase_request_s, self).create(vals)
    #     self.message_subscribe_users(user_ids=[20])
    #     return request

    # @api.model
    # def create(self, vals):
    #     request = super(Purchase_request_s, self).create(vals)
    #     print("create check_uid : "+str(request.check_uid.name))
    #     if vals.get('check_uid'):
    #         request.message_subscribe_users(user_ids=[request.check_uid.id])
    #     return request

    @api.multi
    def write(self, vals):
        # print("write pr")
        res = super(Purchase_request_s, self).write(vals)
        for request in self:
            if vals.get('check_uid'):
                self.message_subscribe_users(user_ids=[request.check_uid.id])
        return res

    @api.multi
    def button_to_approve(self):
        # print 'button_to_approve inherit'

        if self.env.user.id == self.requested_by.id:
            raise UserError(_('Request user and check user can not be the same person'))

        self.write({'check_date': date.today()})
        self.write({'check_uid': self.env.user.id})
        if not self.assigned_to:
            print ('GET Approval')
            self.get_hr_emp()
        return super(Purchase_request_s, self).button_to_approve()

    def notify_concern_person(self,msg,recipient_partners):
        print('notify_concern_person')
        self.env['mail.thread'].message_post(body=msg, message_type="email", subject="PR Approve Request", subtype="mail.mt_comment",
                                             partner_ids=recipient_partners)

    @api.multi
    def button_to_mkt_approve(self):
        return self.write({'state': 'to_approve'})

    @api.multi
    def _track_subtype(self, init_values):
        # print("init_values : " + str(init_values))
        for rec in self:
            # print("rec check_uid : " + str(rec.check_uid.name))
            # print("'state' in init_values : " + str('state' in init_values))
            # print("rec.state : " + str(rec.state))
            if 'state' in init_values and rec.state == 'draft':
                # print('mt_request_draft')
                if rec.check_uid.id:
                    rec.message_subscribe_users(user_ids=[rec.check_uid.id])
                return 'purchase_order_approved.mt_request_draft'

            if 'state' in init_values and rec.state == 'to_approve':
                # print('mt_request_to_approve')
                if rec.check_uid.id:
                    rec.message_unsubscribe_users(user_ids=[rec.check_uid.id])
                if rec.assigned_to.id:
                    rec.message_subscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_subscribe_users(user_ids=user_ids)
                return 'purchase_request.mt_request_to_approve'

            if 'state' in init_values and rec.state == 'to_waiting':
                # print('mt_request_to_waiting')
                if rec.assigned_to.id:
                    rec.message_subscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_unsubscribe_users(user_ids=user_ids)
                return 'purchase_request.mt_request_to_waiting'

            if 'state' in init_values and rec.state == 'approved':
                # print('mt_request_approved')
                if rec.assigned_to.id:
                    rec.message_unsubscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    user_ids_2_level = rec.purchase_type.user_ids_2_level.ids
                    rec.message_subscribe_users(user_ids=user_ids_2_level)
                return 'purchase_request.mt_request_approved'

            if 'requested_by' in init_values and 'state' not in init_values:
                rec.message_subscribe_users(user_ids=[rec.requested_by.id])
            # if 'check_uid' in init_values and 'state' not in init_values:
            #     rec.message_subscribe_users(user_ids=[rec.check_uid.id])
            # if 'assigned_to' in init_values and 'state' not in init_values:
            #     rec.message_subscribe_users(user_ids=[rec.assigned_to.id])

        return super(Purchase_request_s, self)._track_subtype(init_values)

    @api.one
    def button_approved(self):
        print('def button_approved')
        allow = False
        if not allow:
            for group in self.allow_group_ids:
                if self.env.user.id in group.users.ids :
                    allow = True
                    break

        check_line = self.check_line_sub_total()
        if self.state == "to_approve":
            if check_line:
                self.state = "to_waiting"
            else:
                if not allow:
                    if self.state == "to_approve":
                        self.state = "to_waiting"
                    else:
                        raise UserError(_('You are not authorized to approve'))
                if allow:
                    if self.assigned_to.id:
                        self.message_unsubscribe_users(user_ids=[self.assigned_to.id])
                    self.write({'approve_uid': self.env.user.id, 'assigned_to': self.env.user.id,
                                'approve_date': date.today()})
                    super(Purchase_request_s, self).button_approved()
        else:
            if not allow:
                if self.state == "to_approve":
                    self.state = "to_waiting"
                else:
                    raise UserError(_('You are not authorized to approve'))
            if allow:
                if self.assigned_to.id:
                    self.message_unsubscribe_users(user_ids=[self.assigned_to.id])
                self.write({'approve_uid': self.env.user.id, 'assigned_to': self.env.user.id,
                            'approve_date': date.today()})
                super(Purchase_request_s, self).button_approved()

        # if check_line:
        # print ('---233')
        # if self.state == "to_approve":
        #     self.state = "to_waiting"
        # if not allow:
        #     if self.state == "to_approve":
        #         self.state = "to_waiting"
        #     else:
        #         raise UserError(_('You are not authorized to approve'))

        ################################01/05/2019 - remove create expense line due to we direct access to each record #############

        # if allow:
        #     self.state = "to_waiting"
        # self.write({'approve_uid': self.env.user.id,'assigned_to': self.env.user.id, 'approve_date': date.today()})
        # print "OLD PR-APPROVE"
        # super(Purchase_request_s,self).button_approved()
        # else:
        #     if not allow:
        #         if self.state == "to_approve":
        #             self.state = "to_waiting"
        #         else:
        #             raise UserError(_('You are not authorized to approve'))
        #     if allow:
        #         self.write({'approve_uid': self.env.user.id,'assigned_to': self.env.user.id, 'approve_date': date.today()})
        #         # print "OLD PR-APPROVE"
        #         super(Purchase_request_s,self).button_approved()


    def check_line_sub_total(self):
        obj_line = self.line_ids.filtered(lambda r: r.sub_total == 0.0 or not r.sub_total)
        if obj_line:
            return True
        else:
            return False

class purchase_budget_line(models.Model):
    _name = "purchase.budget.line"

    name = fields.Char(string='Budget Type')
    budget = fields.Float(string='Budget')
    expense = fields.Float(string='Current Expense')
    purchase_request_id = fields.Many2one('purchase.request')

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)
    number = fields.Integer(compute='get_number', store=True)

    # project_id = fields.Many2one('project.project',compute="_get_project_id", store=True,string='Project')

    # @api.depends('analytic_account_id')
    # def _get_project_id(self):
    #     for line in self:
    #         if line.analytic_account_id and line.analytic_account_id.project_ids:
    #             line.project_id = line.analytic_account_id.project_ids[0].id

    @api.multi
    @api.depends('product_id','request_id')
    def get_number(self):
        # print("get_number)"
        for request in self.mapped('request_id'):
            number = 1
            for line in request.line_ids:
                line.number = number
                number += 1

    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_mkt_approve','to_approve', 'approved', 'rejected','done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_po_id.id
            self.product_qty = 1
            self.name = name
            self.price_unit = self.product_id.standard_price


class product_template(models.Model):
    _inherit = 'product.template'

    purchase_price = fields.Float(string='Purchase Price')


class Purchase_order_s(models.Model):
    _inherit = 'purchase.order'

    emp_id = fields.Many2one('hr.employee', string='Related Employee')
    # section_id = fields.Many2one('hr.department', string='Section')
    department_id = fields.Many2one('hr.department', string='Department')
    # division_id = fields.Many2one('hr.department', string='Division')
    # location_id = fields.Many2one('res.partner', string='Location', readonly=1)
    # allow_group_ids = fields.One2many('res.groups', 'po_id', string='Allow Groups', compute='_get_allow_group', store=True)
    allow_group_ids = fields.Many2many('res.groups', string='Allow Groups', compute='_get_allow_group', store=True)
    # --------------------------------------
    assigned_to = fields.Many2one('res.users', 'Approver',track_visibility='onchange')
    user_check_id = fields.Many2one('res.users', 'Check by',track_visibility='onchange')
    check_date = fields.Date(string="Checked Date")

    user_create_id = fields.Many2one('res.users', 'Responsible')
    date_approve = fields.Datetime('Approval Date',related='date_approved')
    date_approved = fields.Datetime('Approved Date')
    # ------------------
    # check_uid = fields.Many2one('res.users', 'Check By',track_visibility='onchange')
    purchase_type = fields.Many2one('purchase.type', string='Purchase Type')
    # matrix_id = fields.Many2one('purchase.approval.matrix', compute='_compute_purchase_type', copy=True,string='Purchase Matrix')#11-09-2019
    matrix_id = fields.Many2one('purchase.approval.matrix',copy=True,string='Purchase Matrix')
    new_note = fields.Text(string="Notes")
    approve_date = fields.Date(string="Approve Date")
    approve_uid = fields.Many2one('res.users', string="Purchase Request Approve")

    # @api.model
    # def create(self, vals):
    #     request = super(Purchase_order_s, self).create(vals)
    #     if vals.get('user_check_id'):
    #         request.message_subscribe_users(user_ids=[request.user_check_id.id])
    #     if vals.get('assigned_to'):
    #         request.message_subscribe_users(user_ids=[request.assigned_to.id])
    #     return request
    #
    # @api.multi
    # def write(self, vals):
    #     res = super(Purchase_order_s, self).write(vals)
    #     for request in self:
    #         if vals.get('user_check_id'):
    #             self.message_subscribe_users(user_ids=[request.user_check_id.id])
    #         if vals.get('assigned_to'):
    #             self.message_subscribe_users(user_ids=[request.assigned_to.id])
    #     return res

    @api.multi
    def action_po_by_email_send(self):
        # print 'SEND_PO_BY_EMAIL'
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_po', False):
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            else:
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'purchase_mark_rfq_sent': True,
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            result.append((po.id, name))
        return result

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    requested_by = fields.Many2one('res.users', 'Requested by',required=True,
                                   default=_get_default_requested_by)

    # @api.onchange('amount_total')
    # def _search_purchase_type(self):
    #     if self.amount_total:
    #
    #         if self.purchase_type:
    #             print('purchase_type: '+str(self.purchase_type))
    #             purchase_type_matrix = self.env['purchase.approval.matrix'].search([
    #                 ('purchase_type', '=', self.purchase_type.id), ('max_amount', '>=', self.amount_total)],
    #                 order='max_amount asc')
    #             if purchase_type_matrix:
    #                 if len(purchase_type_matrix)>1:
    #                     self.matrix_id = purchase_type_matrix[len(purchase_type_matrix)-1]
    #                 else:
    #                     self.matrix_id = purchase_type_matrix[len(purchase_type_matrix) - 1]

    # don't use
    def _get_allow_group_user(self):
        print('def _get_allow_group_user')
        self.env.user.id
        obj_user = self
        allow_group_ids = []
        if self.purchase_type:
            purchase_type_matrix = self.env['purchase.approval.matrix'].search([
                ('purchase_type', '=', self.purchase_type.id), ('max_amount', '>', self.amount_total)],
                order='max_amount asc')
            print(purchase_type_matrix)
            print(len(purchase_type_matrix))
            matrix_id = False
            if purchase_type_matrix:
                if len(purchase_type_matrix) > 1:
                    matrix_id = purchase_type_matrix[0]
                else:
                    matrix_id = purchase_type_matrix[0]

            allow_user_id = False
            allow_validate = False

            if matrix_id:
                print('matrix_id'+str(matrix_id))
                print('matrix_id' + str(matrix_id.group_id.name))
                print('matrix_id' + str(matrix_id.group_id))
                for l in purchase_type_matrix:
                    print(l.group_id)
                    allow_group_ids.append(l.group_id.id)
                groups_matrix = self.env['purchase.approval.matrix'].search([
                    ('purchase_type', '=', self.purchase_type.id), ('group_id', '=', matrix_id.group_id.id)],
                )
                print(groups_matrix)
                obj_emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
                print(obj_emp.name)
                print(obj_emp.user_id.name)
                allow_user_id = self.env['res.groups'].sudo().search([('users','in',self.env.user.id)])
                print(allow_user_id)
                allow_user_ids = []
                for x in allow_user_id:
                    allow_user_ids.append(x.id)
                for id in allow_group_ids:
                    if id in allow_user_ids:
                        allow_validate = True
                        print('12345')
                        break
                if allow_user_ids:
                    print(allow_user_ids[0])
                    group_result = []
                    gids = []
                    gids_txt = ''
                    #[262, 218] (262, 218)
                    i = 0
                    for line_gid in purchase_type_matrix:
                        i+=1
                        gids.append(line_gid.group_id.id)
                        gids_txt += str(line_gid.group_id.id)
                        if i != len(purchase_type_matrix):
                            gids_txt += ','

                    print(gids_txt)
                    # self._cr.execute("select uid from res_groups_users_rel where gid=" + str(matrix_id.group_id.id))
                    self._cr.execute("select uid from res_groups_users_rel where gid in (" + str(gids_txt)+")")
                    ress = self._cr.fetchall()
                    for ids in ress:
                        group_result.append(ids[0])

                    print(group_result)
                    if self._uid in group_result:
                        print(str(group_result) + str(self._uid))
                        print('sale permission')
                        allow_validate = True
                    # edit mod 22-11-2019
                    # self.assigned_to = group_result[0]
                    if not self.assigned_to:
                        self.assigned_to = group_result[0]
                    else:
                        self.assigned_to = self.assigned_to
                    #end

                print(allow_validate)
                return allow_validate

    @api.onchange('create_uid', 'allow_group_ids','order_line','order_line.sub_total')
    def _get_hr_emp(self):
        print('def _get_hr_emp')
        for obj_user in self:
            obj_emp = obj_user.requested_by.employee_ids.filtered(lambda x: x.active)
            print(obj_emp)
            if obj_emp:
                emp = obj_emp[0]
                obj_user.update({'emp_id': emp.id,
                                 'department_id': emp.department_id.id})

        # print ('def _get_hr_emp old version')
        # self._get_allow_group_user()
        # for obj_user in self:
        #     obj_emp = self.env['hr.employee'].search([('user_id','=',obj_user.requested_by.id)],limit=1)
        #
        #     obj_user._get_allow_group()
        #
        #     if obj_emp:
        #         obj_user.emp_id = obj_emp.id
        #         obj_user.department_id= obj_emp.department_id.id
        #
        #         # obj_user.write({'department_id': obj_emp.department_id.id})
        #         # print "-----11111--"
        #         print(self.allow_group_ids)
        #         found = False
        #         for group in self.allow_group_ids.sorted(lambda x: x.order):
        #             print(group)
        #             # ################department structure
        #             department_id = obj_emp.department_id.id
        #             if group.comment:
        #                 # print("GROUP")
        #                 # print(group.comment)
        #                 # print(obj_emp.department_id)
        #                 # print(obj_emp.department_id.manager_id)
        #                 # print(obj_emp.department_id.manager_id.user_id)
        #                 # print(obj_emp.department_id.manager_id.user_id.has_group(group.comment))
        #                 # print(obj_emp.department_id.parent_id)
        #                 # print(obj_emp.department_id.parent_id.parent_id)
        #                 # print(obj_emp.department_id.parent_id.manager_id)
        #                 # print(obj_emp.department_id.parent_id.parent_id.manager_id)
        #                 # print(obj_emp.department_id.parent_id.manager_id.user_id.name)
        #                 # print(obj_emp.department_id.parent_id.parent_id.manager_id.user_id.name)
        #                 # print(obj_emp.department_id.parent_id.manager_id.user_id.has_group(group.comment))
        #                 # print(',,,')
        #                 # print(group.comment)
        #                 # print('...')
        #                 if obj_emp.department_id and obj_emp.department_id.manager_id and obj_emp.department_id.manager_id.user_id.has_group(group.comment):
        #                     ############## Assign department manager as approval
        #                     # print("111111111")
        #                     obj_user.assigned_to = obj_emp.department_id.manager_id.user_id.id
        #                     # found = True # 17-09-2019
        #                     # print("obj_user.assigned_to : " + str(obj_user.assigned_to))
        #                     found = True
        #                     break
        #
        #                 elif obj_emp.department_id and obj_emp.department_id.parent_id and obj_emp.department_id.parent_id.manager_id and obj_emp.department_id.parent_id.manager_id.user_id.has_group(group.comment):
        #                     ########### Assigned manager of parent department as approval
        #                     # print("2222222222")
        #                     obj_user.assigned_to = obj_emp.department_id.parent_id.manager_id.user_id.id
        #                     # found = True # 17-09-2019
        #                     # print("obj_user.assigned_to : " + str(obj_user.assigned_to))
        #                     found = True
        #                     break
        #
        #                 elif obj_emp.department_id and obj_emp.department_id.parent_id and obj_emp.department_id.parent_id.parent_id and obj_emp.department_id.parent_id.parent_id.manager_id and obj_emp.department_id.parent_id.parent_id.manager_id.user_id.has_group(group.comment):
        #                     ########## Assigned manager of parent department as approval
        #                     # print("33333333")
        #                     obj_user.assigned_to = obj_emp.department_id.parent_id.parent_id.manager_id.user_id.id
        #                     # found = True # 17-09-2019
        #                     # print("obj_user.assigned_to : " + str(obj_user.assigned_to))
        #                     found = True
        #                     break
        #
        #         if not found:
        #             # print("NOT FOUND")
        #             for group in self.allow_group_ids.sorted(key=lambda r: r.name):
        #                 if group.comment == 'po_approval.group_dmd' or group.comment == 'po_approval.group_md' and group.users:
        #                     # print group.comment
        #                     # print "4"
        #                     obj_user.assigned_to = group.users[0].id
        #                     break

    @api.multi
    def button_confirm(self):
        # print("def button_confirm")
        allow = False
        for group in self.allow_group_ids:
            # print("group : " + str(group.name))
            if self.env.user.id in group.users.ids:
                allow = True
                break
        # print("allow : " + str(allow))

        if self.env.user.id != 1 and self.create_uid.id == self.env.user.id:
            raise UserError(_('Create and submit purchase can not be the same person'))

        if self.env.user.id != 1 and self.env.user.id != self.user_check_id.id and not allow:
            raise UserError(_("Please check, The person who can check/confirm this order is (%s)") % self.user_check_id.name)

        if self.user_check_id:
            self.message_unsubscribe_users(user_ids=[self.user_check_id.id])

        self.write({'user_check_id': self.env.user.id,
                    'state': 'to approve'})

        return super(Purchase_order_s, self).button_confirm()

    @api.depends('requested_by','purchase_type','amount_total')
    def _get_allow_group(self):
        print("def _get_allow_group")
        manager = False
        for obj in self:
            by_user = obj.requested_by.employee_ids.filtered(lambda x: x.active)
            if by_user:
                by_user = by_user[0]
                manager = by_user[0].parent_id.user_id.id
            if obj.purchase_type:
                purchase_type_matrix = obj.env['purchase.approval.matrix'].search([('type', '=', 'PO'),
                                                                                   ('purchase_type', '=',obj.purchase_type.id),
                                                                                   ('max_amount', '>=',obj.amount_total)],
                                                                                  order='max_amount ASC', limit=1)
                print("purchase_type_matrix : " + str(purchase_type_matrix.name))
                print("purchase_type_matrix : " + str(purchase_type_matrix.id))
                if purchase_type_matrix:
                    user_ids = purchase_type_matrix.group_id.users
                    # print('user_ids : ' + str(user_ids.ids))
                    # print('manager : ' + str(manager))
                    if user_ids:
                        if manager and manager in user_ids.ids:
                            assigned_to = manager
                        else:
                            assigned_to = user_ids[0].id
                    else:
                        assigned_to = False
                    obj.update({
                        'assigned_to':assigned_to,
                        'matrix_id': purchase_type_matrix.id,
                        'allow_group_ids': [(6, 0, [purchase_type_matrix.group_id.id])]
                    })

        # print 'def _get_allow_group old version'
        # for po in self:
        #     total_amount = int(po.amount_untaxed)
        #     group_ids = []
        #     allow_approve_group_ids = self.env['purchase.approval.matrix'].search(
        #         [('type','=','PO'),('max_amount', '>=', total_amount)], order='max_amount desc')
        #     for group in allow_approve_group_ids:
        #         group_ids.append(group.group_id.id)
        #     po.update({
        #         'allow_group_ids': [(6, 0, group_ids)]
        #     })

    @api.multi
    def button_approve(self, force=False):
        # print('button_approve-PO')
        # allow_group_user = self._get_allow_group_user()
        allow = False
        for group in self.allow_group_ids:
            # print("group : " + str(group.name))
            if self.env.user.id in group.users.ids:
                allow = True
                break
        # print("allow : " + str(allow))

        if self.env.user.id == self.assigned_to.id:
            if self.order_line:
                for line in self.order_line:
                    standard_price = line.price_unit
                    line.product_id.write({'purchase_price': standard_price})

        elif not allow and self.env.user.id != 1:
            raise UserError(_('You are not authorized to approve'))

        self.write({'assigned_to': self.env.user.id,})
        ######################## Add end of approval process #############
        ######################## JA - 08-06-2020, add product price list to the product price list after approve, get from standard########
        self._add_supplier_to_product()
        return super(Purchase_order_s, self).button_approve()

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id
        currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = currency.id
        self.origin = requisition.name
        self.partner_ref = requisition.name  # to control vendor bill based on agreement reference
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(
                    line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(
                    lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Compute price_unit in appropriate currency
            if requisition.company_id.currency_id != currency:
                price_unit = requisition.company_id.currency_id.compute(price_unit, currency)

            # Create PO line
            order_lines.append((0, 0, {
                'name': name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_po_id.id,
                'product_qty': product_qty,
                'price_unit': price_unit,
                'taxes_id': [(6, 0, taxes_ids)],
                'date_planned': requisition.schedule_date or fields.Date.today(),
                'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
                'account_analytic_id': line.account_analytic_id.id,
                'pr_number': line.pr_number,
            }))
        self.order_line = order_lines

    # @api.multi
    # def _create_picking(self):
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
    #             pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             if not pickings:
    #                 res = order._prepare_picking()
    #                 picking = StockPicking.create(res)
    #             else:
    #                 picking = pickings[0]
    #             moves = order.order_line._create_stock_moves(picking)
    #             moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
    #             seq = 0
    #             for move in sorted(moves, key=lambda move: move.date_expected):
    #                 seq += 5
    #                 move.sequence = seq
    #             moves._action_assign()
    #             picking.message_post_with_view('mail.message_origin_link',
    #                                            values={'self': picking, 'origin': order},
    #                                            subtype_id=self.env.ref('mail.mt_note').id)
    #
    #
    # @api.multi
    # def _create_picking(self):
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
    #             pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             if not pickings:
    #                 res = order._prepare_picking()
    #                 picking = StockPicking.create(res)
    #             else:
    #                 picking = pickings[0]
    #             moves = order.order_line._create_stock_moves(picking)
    #             moves = moves.filtered(lambda x: x.state not in ('done', 'cancel')).action_confirm()
    #             moves.force_assign()
    #             picking.message_post_with_view('mail.message_origin_link',
    #                                            values={'self': picking, 'origin': order},
    #                                            subtype_id=self.env.ref('mail.mt_note').id)
    #     return True


    @api.multi
    def get_pr_number(self):
        pr_number = ""
        for line in self.order_line.filtered(lambda x: x.pr_id):
            if line.pr_id:
                return line.pr_id.id
        return pr_number

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)

        if self.order_line:
            project_id = self.order_line[0].account_analytic_id.id

        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'request_by': self.requested_by.id,
            'department_id': self.department_id.id,
            'date_planned': self.date_planned,
            # 'analytic_account_id': project_id,
            'pr_id': self.get_pr_number(),
            'new_note': self.new_note,
        }

    # @api.multi
    # def all_get_receive_date(self):
    #     # print 'all_get_receive_date'
    #     obj_po = self.env['purchase.order'].search([])
    #     for po in obj_po:
    #         for line in po.order_line:
    #             line._get_receive_date()

    # @api.multi
    # def button_cancel(self):
    #     print 'button_cancel po'
    #     for order in self:
    #         # request_id = self.env['purchase.request'].search([('name', '=', order.pr_number)])
    #         expense_topo_id = self.env['project.analytic.line.expense.topo'].search([('po_id', '=', order.id)])
    #         print expense_topo_id
    #         if expense_topo_id:
    #             expense_topo_id.unlink()
    #
    #     return super(Purchase_order_s, self).button_cancel()

    @api.one
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res_val = super(Purchase_order_s, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        # print('res_val: ', res_val)
        res_val[0]['new_note'] = self.new_note
        # print('res_val: ', res_val)
        return res_val[0]


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    receive_date = fields.Datetime(string='Receive Date', compute='_get_receive_date', store=True)

    # project_id = fields.Many2one('project.project', compute="_get_project_id", store=True,string='Project')
    #
    # @api.depends('account_analytic_id')
    # def _get_project_id(self):
    #     for line in self:
    #         if line.account_analytic_id and line.account_analytic_id.project_ids:
    #             line.project_id = line.account_analytic_id.project_ids[0].id

    @api.depends('move_ids', 'move_ids.date','move_ids.state')
    def _get_receive_date(self):
        # print '_get_receive_date'
        for line in self:
            # print len(line.move_ids)
            # if len(line.move_ids):
            picking_ids = self.env['stock.picking'].search([('group_id.name','=',line.order_id.name)])
            # print picking_ids
            if picking_ids:
                if len(picking_ids):
                    for pic in picking_ids:
                        # print '===========3'
                        if pic.state == 'done':
                            # print '===========4'
                            line.receive_date = pic.scheduled_date
            else:
                if line.move_ids:
                    if len(line.move_ids):
                        # print '=========2'
                        for move in line.move_ids:
                            # print '===========3'
                            if move.state == 'done':
                                # print '===========4'
                                line.receive_date = move.date

class Stockpicking(models.Model):
    _inherit = 'stock.picking'

    new_note = fields.Text(string="Notes")


class Saleorder(models.Model):
    _inherit = 'sale.order'

    new_note = fields.Text(string="Notes")

    @api.multi
    def _action_confirm(self):
        res = super(Saleorder, self)._action_confirm()
        picking_ids = self.mapped('picking_ids')
        for picking in picking_ids:
            print ('origin :',self.origin)
            print ('new_note :',self.new_note)
            picking.write({'new_note': self.new_note})

        return res

    #     for order in self:
    #         order.order_line._action_launch_procurement_rule()
    #         print('new _action_confirm PICKING')
    #         if order.picking_ids:
    #             for picking in order.picking_ids:
    #                 # print ('ORGIN')
    #                 print ('origin :',self.origin)
    #                 print ('new_note :',self.new_note)
    #                 picking.write({'new_note': self.new_note})



