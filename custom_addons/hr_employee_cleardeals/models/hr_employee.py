import base64
import binascii
import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

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
        string="Employee ID",
        copy=False,
        readonly=False,
        index=True,
        tracking=True,
        help="Auto-generated Employee ID in format CD-XXXX",
    )

    # Lifecycle status ribbon
    employee_status = fields.Selection(
        [
            ("onboarding", "Onboarding"),
            ("active", "Active"),
            ("notice", "Notice Period"),
            ("resigned", "Resigned"),
            ("terminated", "Terminated"),
        ],
        string="Employee Status",
        default="onboarding",
        required=True,
        tracking=True,
    )

    # ====================================================================
    # DOCUMENT VAULT INTEGRATION
    # ====================================================================
    # Note: oh_employee_documents_expiry already provides:
    # - document_ids field
    # - document_count computed field
    # - action_document_view() smart button
    # We only add the auto-sync functionality here

    # ===================================================================
    #  TAB 1 – WORK INFORMATION
    # ===================================================================
    #  Reused from base:
    #  • department_id     → hr.version  (Many2one hr.department, create‑able)
    #  • job_id            → hr.version  (Many2one hr.job,        create‑able)
    #  • parent_id         → hr.employee (Many2one hr.employee – Manager)

    # Date of Joining (default: today)
    date_of_joining = fields.Date(
        string="Date of Joining",
        default=fields.Date.context_today,
        tracking=True,
        groups="hr.group_hr_user",
    )

    # Assets tracking (checkboxes)
    asset_laptop = fields.Boolean(string="Laptop Issued", tracking=True)
    asset_sim = fields.Boolean(string="SIM Card Issued", tracking=True)
    asset_phone = fields.Boolean(string="Phone Issued", tracking=True)
    asset_pc = fields.Boolean(string="PC/Desktop Issued", tracking=True)
    asset_physical_id = fields.Boolean(string="Physical ID Card Issued", tracking=True)

    # ===================================================================
    #  TAB 2 – PERSONAL DETAILS
    # ===================================================================
    #  Reused from base / addons:
    #  • legal_name        → hr.employee    (Full Legal Name)
    #  • sex               → hr.version     (Gender - male/female/other)
    #  • marital           → hr.version     (Marital Status)
    #  • birthday          → hr.employee    (Date of Birth)
    #  • private_phone     → hr.employee    (Personal Mobile)
    #  • private_email     → hr.employee    (Personal Email)
    #  • private_street…   → hr.version     (Structured address - Permanent)
    #  • emergency_contact → hr.employee    (Emergency Contact Name)
    #  • emergency_phone   → hr.employee    (Emergency Contact Phone)
    #  • identification_id → hr.version     (Aadhaar / National ID)

    # Blood group (not in base)
    blood_group = fields.Selection(
        [
            ("a+", "A+"),
            ("a-", "A-"),
            ("b+", "B+"),
            ("b-", "B-"),
            ("ab+", "AB+"),
            ("ab-", "AB-"),
            ("o+", "O+"),
            ("o-", "O-"),
        ],
        string="Blood Group",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # Current address-separate text block with "same as permanent" toggle
    current_address = fields.Text(
        string="Current Address",
        groups="hr.group_hr_user",
        tracking=True,
    )
    same_as_permanent = fields.Boolean(
        string="Same as Permanent Address",
        groups="hr.group_hr_user",
    )

    # Emergency contact-relationship (base already has name + phone)
    emergency_contact_relationship = fields.Char(
        string="Relationship",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # PAN (identification_id from base covers Aadhaar)
    pan_number = fields.Char(
        string="PAN Number",
        size=10,
        groups="hr.group_hr_user",
        tracking=True,
    )

    # Passport-size photo (separate from the main avatar image_1920)
    passport_photo = fields.Binary(
        string="Passport Size Photo",
        attachment=True,
        groups="hr.group_hr_user",
    )
    passport_photo_filename = fields.Char(
        string="Passport Photo Filename",
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 3 - INDIAN STATUTORY & BANK
    # ===================================================================

    # Bank information
    bank_name = fields.Char(
        string="Bank Name",
        groups="hr.group_hr_user",
        tracking=True,
    )
    bank_acc_number = fields.Char(
        string="Account Number",
        groups="hr.group_hr_user",
        tracking=True,
    )
    ifsc_code = fields.Char(
        string="IFSC Code",
        groups="hr.group_hr_user",
        tracking=True,
    )
    account_type = fields.Selection(
        [
            ("savings", "Savings"),
            ("current", "Current"),
            ("salary", "Salary"),
        ],
        string="Account Type",
        default="savings",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # Payroll verification
    name_as_per_bank = fields.Char(
        string="Name as per Bank",
        groups="hr.group_hr_user",
        tracking=True,
    )
    cibil_score = fields.Integer(
        string="CIBIL Score",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # Document upload - cancelled cheque / passbook
    bank_document_type = fields.Selection(
        [
            ("cancelled_cheque", "Cancelled Cheque"),
            ("passbook_copy", "Passbook Copy"),
        ],
        string="Document Type",
        groups="hr.group_hr_user",
    )
    bank_document = fields.Binary(
        string="Cancelled Cheque / Passbook Copy",
        attachment=True,
        groups="hr.group_hr_user",
    )
    bank_document_filename = fields.Char(
        string="Bank Document Filename",
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 4 - BACKGROUND & ACADEMICS
    # ===================================================================

    # Education summary
    education_background = fields.Text(
        string="Education Background",
        groups="hr.group_hr_user",
        help="Summary of 10th, 12th, Graduation, Post-Graduation, etc.",
    )

    # Experience documents from last employer
    relieving_letter = fields.Binary(
        string="Relieving Letter",
        attachment=True,
        groups="hr.group_hr_user",
    )
    relieving_letter_filename = fields.Char(string="Relieving Letter Filename")

    experience_letter = fields.Binary(
        string="Experience Letter",
        attachment=True,
        groups="hr.group_hr_user",
    )
    experience_letter_filename = fields.Char(string="Experience Letter Filename")

    # Last 3-month salary slips
    salary_slip_1 = fields.Binary(
        string="Salary Slip - Month 1",
        attachment=True,
        groups="hr.group_hr_user",
    )
    salary_slip_1_filename = fields.Char(string="Slip 1 Filename")

    salary_slip_2 = fields.Binary(
        string="Salary Slip - Month 2",
        attachment=True,
        groups="hr.group_hr_user",
    )
    salary_slip_2_filename = fields.Char(string="Slip 2 Filename")

    salary_slip_3 = fields.Binary(
        string="Salary Slip - Month 3",
        attachment=True,
        groups="hr.group_hr_user",
    )
    salary_slip_3_filename = fields.Char(string="Slip 3 Filename")

    # Resume & skill-set (resume_line_ids / employee_skill_ids from hr_skills)
    resume_doc = fields.Binary(
        string="Resume (PDF)",
        attachment=True,
        groups="hr.group_hr_user",
    )
    resume_doc_filename = fields.Char(string="Resume Filename")

    skill_set_summary = fields.Text(
        string="Skill Set Summary",
        groups="hr.group_hr_user",
    )

    # ===================================================================
    #  TAB 5 - DOCUMENT CHECKLIST (COMPLIANCE)
    # ===================================================================

    # Onboarding documents
    offer_letter = fields.Binary(
        string="Offer Letter",
        attachment=True,
        groups="hr.group_hr_user",
    )
    offer_letter_filename = fields.Char(string="Offer Letter Filename")

    appointment_letter = fields.Binary(
        string="Appointment Letter",
        attachment=True,
        groups="hr.group_hr_user",
    )
    appointment_letter_filename = fields.Char(string="Appointment Letter Filename")

    bond_document = fields.Binary(
        string="Bond Document",
        attachment=True,
        groups="hr.group_hr_user",
    )
    bond_document_filename = fields.Char(string="Bond Filename")

    contract_document = fields.Binary(
        string="Contract",
        attachment=True,
        groups="hr.group_hr_user",
    )
    contract_document_filename = fields.Char(string="Contract Filename")

    nda_document = fields.Binary(
        string="NDA",
        attachment=True,
        groups="hr.group_hr_user",
    )
    nda_document_filename = fields.Char(string="NDA Filename")

    # Address proofs
    address_proof_type = fields.Selection(
        [
            ("light_bill", "Light Bill"),
            ("phone_bill", "Phone Bill"),
            ("rent_agreement", "Rent Agreement"),
        ],
        string="Address Proof Type",
        groups="hr.group_hr_user",
    )

    address_proof_document = fields.Binary(
        string="Address Proof",
        attachment=True,
        groups="hr.group_hr_user",
    )
    address_proof_filename = fields.Char(string="Address Proof Filename")

    # Other identity documents (uploads)
    #  • id_card           → base hr.employee   (ID Card Copy - Aadhaar card upload)
    #  • driving_license   → base hr.employee   (Driving License)
    passport_doc = fields.Binary(
        string="Passport Copy",
        attachment=True,
        groups="hr.group_hr_user",
    )
    passport_doc_filename = fields.Char(string="Passport Filename")

    pan_card_doc = fields.Binary(
        string="PAN Card Copy",
        attachment=True,
        groups="hr.group_hr_user",
    )
    pan_card_doc_filename = fields.Char(string="PAN Card Filename")

    # Internal lifecycle documents
    appraisal_doc = fields.Binary(
        string="Appraisal Document",
        attachment=True,
        groups="hr.group_hr_user",
    )
    appraisal_doc_filename = fields.Char(string="Appraisal Filename")

    increment_letter = fields.Binary(
        string="Increment Letter",
        attachment=True,
        groups="hr.group_hr_user",
    )
    increment_letter_filename = fields.Char(string="Increment Letter Filename")

    notice_period_doc = fields.Binary(
        string="Notice Period Document",
        attachment=True,
        groups="hr.group_hr_user",
    )
    notice_period_doc_filename = fields.Char(string="Notice Period Filename")

    # ===================================================================
    #  COMPUTED / ONCHANGE
    # ===================================================================

    @api.onchange("same_as_permanent")
    def _onchange_same_as_permanent(self):
        """Copy structured permanent address into current_address text."""
        if self.same_as_permanent:
            parts = filter(
                None,
                [
                    self.private_street,
                    self.private_street2,
                    self.private_city,
                    self.private_state_id.name if self.private_state_id else "",
                    self.private_zip,
                    self.private_country_id.name if self.private_country_id else "",
                ],
            )
            self.current_address = ", ".join(parts) or self.current_address

    # ===================================================================
    #  CONSTRAINTS
    # ===================================================================

    @api.constrains("identification_id")
    def _check_aadhar_format(self):
        """Aadhaar must be exactly 12 digits (spaces allowed for readability)."""
        for rec in self:
            if rec.identification_id:
                cleaned = rec.identification_id.replace(" ", "")
                if not re.match(r"^\d{12}$", cleaned):
                    raise ValidationError(
                        _("Aadhaar number must be exactly 12 digits."),
                    )

    @api.constrains("pan_number")
    def _check_pan_format(self):
        """PAN format: ABCDE1234F (5 letters + 4 digits + 1 letter)."""
        for rec in self:
            if rec.pan_number:
                if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", rec.pan_number.upper()):
                    raise ValidationError(
                        _(
                            "PAN number must follow the format ABCDE1234F "
                            "(5 uppercase letters, 4 digits, 1 uppercase letter).",
                        ),
                    )

    # ===================================================================
    #  CRUD
    # ===================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate Employee ID with CD-XXXX sequence."""
        for vals in vals_list:
            # Check if employee_id is not provided or is 'New'/'False'
            if not vals.get("employee_id") or vals.get("employee_id") == "/":
                vals["employee_id"] = (
                    self.env["ir.sequence"].next_by_code("hr.employee.cd.id")
                    or "CD-0000"
                )
            # Normalize PAN to uppercase
            if vals.get("pan_number"):
                vals["pan_number"] = vals["pan_number"].upper()
        employees = super().create(vals_list)

        # Auto sync documents to vault after employee creation
        for employee in employees:
            employee._sync_documents_to_vault()

        return employees

    def write(self, vals):
        """Auto sync documents when binary fields are updated."""
        _logger.info("[DOCUMENT SYNC] write() called with vals: %s", list(vals.keys()))

        # Normalize PAN to uppercase
        if vals.get("pan_number"):
            vals["pan_number"] = vals["pan_number"].upper()
        result = super().write(vals)

        # Check if any document field was updated
        document_fields = self._get_document_field_mapping().keys()
        if any(field in vals for field in document_fields):
            _logger.info(
                "[DOCUMENT SYNC] Document field detected, triggering sync for %s employee(s)",
                len(self),
            )
            for employee in self:
                employee._sync_documents_to_vault()

        return result

    def _get_document_field_mapping(self):
        """
        Map binary fields to document type names.
        Returns dict: {'binary_field_name': 'Document Type Name'}
        """
        return {
            # Onboarding Documents
            "offer_letter": "Offer Letter",
            "appointment_letter": "Appointment Letter",
            "nda_document": "NDA",
            "bond_document": "Bond Document",
            "contract_document": "Employment Contract",
            # Identity Documents
            "pan_card_doc": "PAN Card",
            "passport_doc": "Passport",
            # Bank Documents
            "bank_document": "Bank Document",
            # Address Proof
            "address_proof_document": "Address Proof",
            # Experience Documents
            "relieving_letter": "Relieving Letter",
            "experience_letter": "Experience Letter",
            "salary_slip_1": "Salary Slip",
            "salary_slip_2": "Salary Slip",
            "salary_slip_3": "Salary Slip",
            # Educational Documents
            "resume_doc": "Resume/CV",
            # Lifecycle Documents
            "appraisal_doc": "Appraisal Document",
            "increment_letter": "Increment Letter",
            "notice_period_doc": "Notice Period Document",
            # Photo
            "passport_photo": "Passport Photo",
        }

    def _get_or_create_document_type(self, doc_type_name):
        """
        Get existing document type by name or create if not exists.
        Returns document.type record.
        """
        DocumentType = self.env["document.type"]
        doc_type = DocumentType.sudo().search([("name", "=", doc_type_name)], limit=1)

        if not doc_type:
            _logger.info(
                "[DOCUMENT SYNC] Creating new document type: %s",
                doc_type_name,
            )
            doc_type = DocumentType.sudo().create(
                {
                    "name": doc_type_name,
                },
            )

        return doc_type

    def _detect_mimetype_from_filename(self, filename):
        """
        Detect MIME type based on file extension.
        Returns tuple: (mimetype, default_extension)
        """
        if not filename:
            return ("application/pdf", ".pdf")

        filename_lower = filename.lower()

        # Image formats
        if filename_lower.endswith((".jpg", ".jpeg")):
            return ("image/jpeg", ".jpg")
        if filename_lower.endswith(".png"):
            return ("image/png", ".png")
        if filename_lower.endswith(".gif"):
            return ("image/gif", ".gif")
        if filename_lower.endswith(".bmp"):
            return ("image/bmp", ".bmp")
        if filename_lower.endswith(".tiff"):
            return ("image/tiff", ".tiff")

        # Document formats
        if filename_lower.endswith(".pdf"):
            return ("application/pdf", ".pdf")
        if filename_lower.endswith((".doc", ".docx")):
            return (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".docx",
            )
        if filename_lower.endswith((".xls", ".xlsx")):
            return (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
            )

        # Default to PDF if unknown
        return ("application/pdf", ".pdf")

    def _detect_mimetype_from_binary(self, binary_data):
        """
        Detect MIME type from binary data using magic numbers.
        Returns tuple: (mimetype, extension) or None if cannot detect.
        """
        if not binary_data:
            return None

        try:
            # Try to decode base64 first (binary fields in Odoo are base64)
            if isinstance(binary_data, str):
                data = base64.b64decode(binary_data)
            elif isinstance(binary_data, bytes):
                # Could be base64-encoded bytes or raw binary
                try:
                    data = base64.b64decode(binary_data)
                except (ValueError, TypeError, binascii.Error):
                    # If decode fails, it's already raw binary
                    data = binary_data
            else:
                data = binary_data

            # Check magic numbers (first few bytes)
            if data[:2] == b"\xff\xd8":  # JPEG
                return ("image/jpeg", ".jpg")
            if data[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
                return ("image/png", ".png")
            if data[:4] == b"%PDF":  # PDF
                return ("application/pdf", ".pdf")
            if data[:2] == b"BM":  # BMP
                return ("image/bmp", ".bmp")
            if data[:4] in [b"GIF87a", b"GIF89a"]:  # GIF
                return ("image/gif", ".gif")

        except (IndexError, TypeError, ValueError, AttributeError) as e:
            _logger.warning("[DOCUMENT SYNC] Could not detect MIME from binary: %s", e)

        return None

    def _sync_documents_to_vault(self):
        """
        Automatically create/update hr.employee.document records
        from binary field uploads in the employee form.
        """
        self.ensure_one()
        _logger.info(
            "[DOCUMENT SYNC] Starting vault sync for employee: %s (ID: %s)",
            self.name,
            self.id,
        )

        DocumentModel = self.env["hr.employee.document"]
        AttachmentModel = self.env["ir.attachment"]
        field_mapping = self._get_document_field_mapping()

        synced_count = 0
        for field_name, doc_type_name in field_mapping.items():
            binary_data = self[field_name]

            if not binary_data:
                continue

            # Get filename
            filename_field = f"{field_name}_filename"
            filename = self[filename_field] if filename_field in self._fields else None

            # Determine if this is a photo field (image) or document field
            is_photo_field = field_name in ["passport_photo"]

            # Detect MIME type - try filename first, then binary data
            mimetype, default_ext = self._detect_mimetype_from_filename(filename)

            # If filename detection failed or returned default PDF for a photo field,
            # try detecting from binary data
            if is_photo_field and mimetype == "application/pdf":
                binary_detection = self._detect_mimetype_from_binary(binary_data)
                if binary_detection:
                    mimetype, default_ext = binary_detection
                    _logger.info(
                        "[DOCUMENT SYNC] Detected MIME from binary data: %s",
                        mimetype,
                    )

            # Set default filename if not provided
            if not filename:
                if is_photo_field:
                    filename = f"{field_name}{default_ext}"  # Use detected extension
                else:
                    filename = f"{field_name}.pdf"  # Default to .pdf for documents

            _logger.info(
                "[DOCUMENT SYNC] Final MIME type: %s for file: %s",
                mimetype,
                filename,
            )

            # Get or create document type
            doc_type = self._get_or_create_document_type(doc_type_name)

            # Generate document name
            doc_name = filename
            if field_name in ["salary_slip_1", "salary_slip_2", "salary_slip_3"]:
                month_num = field_name.split("_")[-1]
                doc_name = f"Salary Slip - Month {month_num}"

            _logger.info("[DOCUMENT SYNC] Processing %s -> %s", field_name, doc_name)

            # Search for existing document vault record
            existing_doc = DocumentModel.search(
                [
                    ("employee_ref_id", "=", self.id),
                    ("document_type_id", "=", doc_type.id),
                    ("name", "=", doc_name),
                ],
                limit=1,
            )

            # Create ir.attachment record with detected MIME type
            attachment = AttachmentModel.sudo().create(
                {
                    "name": filename,
                    "datas": binary_data,
                    "res_model": "hr.employee.document",
                    "res_id": existing_doc.id if existing_doc else 0,
                    "mimetype": mimetype,
                },
            )
            _logger.info(
                "[DOCUMENT SYNC] Created attachment ID: %s with MIME type: %s",
                attachment.id,
                mimetype,
            )

            # Prepare document vault values
            doc_vals = {
                "employee_ref_id": self.id,
                "document_type_id": doc_type.id,
                "name": doc_name,
                "issue_date": fields.Date.today(),
                "doc_attachment_ids": [
                    (4, attachment.id),
                ],  # Link attachment via Many2many
            }

            if existing_doc:
                _logger.info(
                    "[DOCUMENT SYNC] Updating existing vault record ID: %s",
                    existing_doc.id,
                )
                existing_doc.sudo().write(doc_vals)
            else:
                new_doc = DocumentModel.sudo().create(doc_vals)
                _logger.info(
                    "[DOCUMENT SYNC] Created new vault record ID: %s",
                    new_doc.id,
                )
                # Update attachment res_id
                attachment.sudo().write({"res_id": new_doc.id})

            synced_count += 1

        _logger.info(
            "[DOCUMENT SYNC] Completed: %s documents synced to vault",
            synced_count,
        )
