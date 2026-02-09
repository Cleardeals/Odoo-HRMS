import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ===================================================================
    #  HEADER / IDENTITY
    # ===================================================================
    #  • name              → base hr.employee  (Employee Name)
    #  • image_1920        → base hr.employee  (Employee Photo)
    #  • job_title         → base hr.version   (computed from job_id, overridable)
    #  • work_email        → base hr.employee  (Work Email)
    #  • work_phone        → base hr.employee  (Work Phone)
    #  • mobile_phone      → base hr.employee  (Work Mobile)

    # Custom Employee ID – auto-generated CD-XXXX
    employee_id = fields.Char(
        string='Employee ID',
        copy=False,
        readonly=True,
        index=True,
        tracking=True,
        help="Auto-generated Employee ID in format CD-XXXX",
    )

    # Lifecycle status ribbon
    employee_status = fields.Selection([
        ('onboarding', 'Onboarding'),
        ('active', 'Active'),
        ('notice', 'Notice Period'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
    ], string='Employee Status', default='onboarding', required=True, tracking=True)

    # ===================================================================
    #  TAB 1 – WORK INFORMATION
    # ===================================================================
    #  Reused from base:
    #  • department_id     → hr.version  (Many2one hr.department, create‑able)
    #  • job_id            → hr.version  (Many2one hr.job,        create‑able)
    #  • parent_id         → hr.employee (Many2one hr.employee – Manager)

    # Date of Joining (default: today)
    date_of_joining = fields.Date(
        string='Date of Joining',
        default=fields.Date.context_today,
        tracking=True,
        groups="hr.group_hr_user",
    )

    # Assets tracking (checkboxes)
    asset_laptop = fields.Boolean(string='Laptop Issued', tracking=True)
    asset_sim = fields.Boolean(string='SIM Card Issued', tracking=True)
    asset_phone = fields.Boolean(string='Phone Issued', tracking=True)
    asset_pc = fields.Boolean(string='PC/Desktop Issued', tracking=True)
    asset_physical_id = fields.Boolean(string='Physical ID Card Issued', tracking=True)

    # ===================================================================
    #  TAB 2 – PERSONAL DETAILS
    # ===================================================================
    #  Reused from base / addons:
    #  • legal_name        → hr.employee    (Full Legal Name)
    #  • sex               → hr.version     (Gender – male/female/other)
    #  • marital           → hr.version     (Marital Status)
    #  • birthday          → hr.employee    (Date of Birth)
    #  • private_phone     → hr.employee    (Personal Mobile)
    #  • private_email     → hr.employee    (Personal Email)
    #  • private_street…   → hr.version     (Structured address – Permanent)
    #  • emergency_contact → hr.employee    (Emergency Contact Name)
    #  • emergency_phone   → hr.employee    (Emergency Contact Phone)
    #  • identification_id → hr.version     (Aadhaar / National ID)

    # Blood group (not in base)
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string='Blood Group', groups="hr.group_hr_user", tracking=True)

    # Current address – separate text block with "same as permanent" toggle
    current_address = fields.Text(
        string='Current Address',
        groups="hr.group_hr_user",
        tracking=True,
    )
    same_as_permanent = fields.Boolean(
        string='Same as Permanent Address',
        groups="hr.group_hr_user",
    )

    # Emergency contact – relationship (base already has name + phone)
    emergency_contact_relationship = fields.Char(
        string='Relationship',
        groups="hr.group_hr_user",
        tracking=True,
    )

    # PAN (identification_id from base covers Aadhaar)
    pan_number = fields.Char(
        string='PAN Number',
        size=10,
        groups="hr.group_hr_user",
        tracking=True,
    )

    # Passport‑size photo (separate from the main avatar image_1920)
    passport_photo = fields.Binary(
        string='Passport Size Photo',
        attachment=True,
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 3 – INDIAN STATUTORY & BANK
    # ===================================================================

    # Bank information
    bank_name = fields.Char(string='Bank Name', groups="hr.group_hr_user", tracking=True)
    bank_acc_number = fields.Char(string='Account Number', groups="hr.group_hr_user", tracking=True)
    ifsc_code = fields.Char(string='IFSC Code', groups="hr.group_hr_user", tracking=True)
    account_type = fields.Selection([
        ('savings', 'Savings'),
        ('current', 'Current'),
    ], string='Account Type', default='savings', groups="hr.group_hr_user", tracking=True)

    # Payroll verification
    name_as_per_bank = fields.Char(string='Name as per Bank', groups="hr.group_hr_user", tracking=True)
    cibil_score = fields.Integer(string='CIBIL Score', groups="hr.group_hr_user", tracking=True)

    # Document upload – cancelled cheque / passbook
    bank_document_type = fields.Selection([
        ('cancelled_cheque', 'Cancelled Cheque'),
        ('passbook_copy', 'Passbook Copy'),
    ], string='Document Type', groups="hr.group_hr_user")
    bank_document = fields.Binary(
        string='Cancelled Cheque / Passbook Copy',
        attachment=True,
        groups="hr.group_hr_user",
    )
    bank_document_filename = fields.Char(
        string='Bank Document Filename',
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 4 – BACKGROUND & ACADEMICS
    # ===================================================================

    # Education summary
    education_background = fields.Text(
        string='Education Background',
        groups="hr.group_hr_user",
        help="Summary of 10th, 12th, Graduation, Post-Graduation, etc.",
    )

    # Experience documents from last employer
    relieving_letter = fields.Binary(string='Relieving Letter', attachment=True, groups="hr.group_hr_user")
    relieving_letter_filename = fields.Char(string='Relieving Letter Filename')

    experience_letter = fields.Binary(string='Experience Letter', attachment=True, groups="hr.group_hr_user")
    experience_letter_filename = fields.Char(string='Experience Letter Filename')

    # Last 3‑month salary slips
    salary_slip_1 = fields.Binary(string='Salary Slip – Month 1', attachment=True, groups="hr.group_hr_user")
    salary_slip_1_filename = fields.Char(string='Slip 1 Filename')

    salary_slip_2 = fields.Binary(string='Salary Slip – Month 2', attachment=True, groups="hr.group_hr_user")
    salary_slip_2_filename = fields.Char(string='Slip 2 Filename')

    salary_slip_3 = fields.Binary(string='Salary Slip – Month 3', attachment=True, groups="hr.group_hr_user")
    salary_slip_3_filename = fields.Char(string='Slip 3 Filename')

    # Resume & skill‑set (resume_line_ids / employee_skill_ids from hr_skills)
    resume_doc = fields.Binary(string='Resume (PDF)', attachment=True, groups="hr.group_hr_user")
    resume_doc_filename = fields.Char(string='Resume Filename')

    skill_set_summary = fields.Text(
        string='Skill Set Summary',
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 5 – DOCUMENT CHECKLIST (COMPLIANCE)
    # ===================================================================

    # Onboarding documents
    offer_letter = fields.Binary(string='Offer Letter', attachment=True, groups="hr.group_hr_user")
    offer_letter_filename = fields.Char(string='Offer Letter Filename')

    appointment_letter = fields.Binary(string='Appointment Letter', attachment=True, groups="hr.group_hr_user")
    appointment_letter_filename = fields.Char(string='Appointment Letter Filename')

    bond_document = fields.Binary(string='Bond Document', attachment=True, groups="hr.group_hr_user")
    bond_document_filename = fields.Char(string='Bond Filename')

    contract_document = fields.Binary(string='Contract', attachment=True, groups="hr.group_hr_user")
    contract_document_filename = fields.Char(string='Contract Filename')

    nda_document = fields.Binary(string='NDA', attachment=True, groups="hr.group_hr_user")
    nda_document_filename = fields.Char(string='NDA Filename')

    # Address proofs
    address_proof_type = fields.Selection([
        ('light_bill', 'Light Bill'),
        ('phone_bill', 'Phone Bill'),
        ('rent_agreement', 'Rent Agreement'),
    ], string='Address Proof Type', groups="hr.group_hr_user")

    address_proof_document = fields.Binary(string='Address Proof', attachment=True, groups="hr.group_hr_user")
    address_proof_filename = fields.Char(string='Address Proof Filename')

    # Other identity documents (uploads)
    #  • id_card           → base hr.employee   (ID Card Copy – Aadhaar card upload)
    #  • driving_license   → base hr.employee   (Driving License)
    passport_doc = fields.Binary(string='Passport Copy', attachment=True, groups="hr.group_hr_user")
    passport_doc_filename = fields.Char(string='Passport Filename')

    pan_card_doc = fields.Binary(string='PAN Card Copy', attachment=True, groups="hr.group_hr_user")
    pan_card_doc_filename = fields.Char(string='PAN Card Filename')

    # Internal lifecycle documents
    appraisal_doc = fields.Binary(string='Appraisal Document', attachment=True, groups="hr.group_hr_user")
    appraisal_doc_filename = fields.Char(string='Appraisal Filename')

    increment_letter = fields.Binary(string='Increment Letter', attachment=True, groups="hr.group_hr_user")
    increment_letter_filename = fields.Char(string='Increment Letter Filename')

    notice_period_doc = fields.Binary(string='Notice Period Document', attachment=True, groups="hr.group_hr_user")
    notice_period_doc_filename = fields.Char(string='Notice Period Filename')

    # ===================================================================
    #  COMPUTED / ONCHANGE
    # ===================================================================

    @api.onchange('same_as_permanent')
    def _onchange_same_as_permanent(self):
        """Copy structured permanent address into current_address text."""
        if self.same_as_permanent:
            parts = filter(None, [
                self.private_street,
                self.private_street2,
                self.private_city,
                self.private_state_id.name if self.private_state_id else '',
                self.private_zip,
                self.private_country_id.name if self.private_country_id else '',
            ])
            self.current_address = ', '.join(parts) or self.current_address

    # ===================================================================
    #  CONSTRAINTS
    # ===================================================================

    @api.constrains('identification_id')
    def _check_aadhar_format(self):
        """Aadhaar must be exactly 12 digits (spaces allowed for readability)."""
        for rec in self:
            if rec.identification_id:
                cleaned = rec.identification_id.replace(' ', '')
                if not re.match(r'^\d{12}$', cleaned):
                    raise ValidationError(
                        _('Aadhaar number must be exactly 12 digits.'))

    @api.constrains('pan_number')
    def _check_pan_format(self):
        """PAN format: ABCDE1234F (5 letters + 4 digits + 1 letter)."""
        for rec in self:
            if rec.pan_number:
                if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', rec.pan_number.upper()):
                    raise ValidationError(
                        _('PAN number must follow the format ABCDE1234F '
                          '(5 uppercase letters, 4 digits, 1 uppercase letter).'))

    # ===================================================================
    #  CRUD
    # ===================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate Employee ID with CD-XXXX sequence."""
        for vals in vals_list:
            # Check if employee_id is not provided or is 'New'/'False'
            if not vals.get('employee_id') or vals.get('employee_id') == '/':
                vals['employee_id'] = (
                    self.env['ir.sequence'].next_by_code('hr.employee.cd.id')
                    or 'CD-0000'
                )
        return super(HrEmployee, self).create(vals_list)