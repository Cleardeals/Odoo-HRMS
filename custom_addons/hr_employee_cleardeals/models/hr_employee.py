from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Identity & Personal
    personal_mobile = fields.Char(string='Personal Mobile')
    personal_email = fields.Char(string='Personal Email')
    emergency_contact_relation = fields.Char(string='Emergency Contact Relation')

    aadhar_number = fields.Char(string='Aadhar Number')
    pan_number = fields.Char(string='PAN Number')
    blood_group = fields.Selection(string='Blood Group', selection=[
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'), 
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ])
    passport_photo = fields.Binary(string='Passport Size Photo')
    cibil_score = fields.Integer(string='CIBIL Score')
    education_background = fields.Text(string='Education Background')


    # Bank Details
    bank_name = fields.Char(string='Bank Name')
    bank_acc_number = fields.Char(string='Bank Account Number')
    account_type = fields.Selection(string='Account Type', selection=[
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('salary', 'Salary'),
        ('other', 'Other'),
    ], default='savings')

    ifsc_code = fields.Char(string='IFSC Code')
    name_as_per_bank = fields.Char(string='Name as per Bank')

    # Override Create for CDxxxx ID
    @api.model
    def create(self, vals):
        if 'employee_id' not in vals or not vals['employee_id']:
            sequence = self.env['ir.sequence'].next_by_code('hr.employee') or 'CD0000'
            vals['employee_id'] = sequence
        return super(HrEmployee, self).create(vals)
