import logging
from email.utils import formataddr, parseaddr

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = "applicant.get.refuse.reason"

    def _get_sender_from_server(self, server):
        if server.from_filter:
            for raw_part in server.from_filter.split(","):
                part = raw_part.strip()
                if not part or "@" not in part:
                    continue
                _, parsed_email = parseaddr(part)
                sender_email = parsed_email or part
                return server.id, formataddr(
                    (self.env.company.name or "", sender_email)
                )
        if server.smtp_user and "@" in server.smtp_user:
            return server.id, formataddr(
                (self.env.company.name or "", server.smtp_user)
            )
        return False, False

    def _get_refusal_mail_server_sender(self):
        """Pick sender from active outgoing server settings.

        Prefer an explicit address from from_filter, then smtp_user.
        """
        self.ensure_one()

        template_server = (
            self.template_id.mail_server_id.sudo()
            if self.template_id and self.template_id.mail_server_id
            else False
        )
        if template_server and template_server.active:
            server_id, sender = self._get_sender_from_server(template_server)
            if sender:
                return server_id, sender

        servers = (
            self.env["ir.mail_server"]
            .sudo()
            .search([("active", "=", True)], order="sequence, id")
        )
        for server in servers:
            server_id, sender = self._get_sender_from_server(server)
            if sender:
                return server_id, sender
        return False, False

    def _get_refusal_sender_email(self):
        """Return a usable sender for refusal emails.

        Priority: outgoing server sender, then current user email,
        then company/default-from, then catchall, then mail-server default,
        then a last-resort local address.
        """
        self.ensure_one()
        _, server_sender = self._get_refusal_mail_server_sender()
        if server_sender:
            return server_sender

        if self.env.user.email:
            return self.env.user.email_formatted

        company_email = (
            self.env.company.default_from_email
            or self.env.company.email
            or self.env.company.partner_id.email
        )
        if company_email:
            return formataddr((self.env.company.name or "", company_email))

        catchall_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.catchall.alias")
        )
        catchall_domain = (
            self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")
        )
        if catchall_alias and catchall_domain:
            return f"{catchall_alias}@{catchall_domain}"

        default_from = self.env["ir.mail_server"]._get_default_from_address()
        if default_from:
            return default_from

        # Keep flow non-blocking in unconfigured dev databases.
        return "odoo@localhost"

    def action_refuse_reason_apply(self):
        self.ensure_one()

        if not self.send_mail:
            return super().action_refuse_reason_apply()

        if any(
            not (applicant.email_from or applicant.partner_id.email)
            for applicant in self.applicant_ids
        ):
            raise UserError(
                _(
                    "At least one applicant doesn't have a email; you can't use send email option.",
                ),
            )

        server_id, server_sender = self._get_refusal_mail_server_sender()
        sender_email = self._get_refusal_sender_email()

        self.write({"send_mail": False})
        action = super().action_refuse_reason_apply()
        self.with_context(
            refusal_sender_email=server_sender or sender_email,
            refusal_mail_server_id=server_id,
        )._prepare_send_refusal_mails()
        return action

    def _prepare_send_refusal_mails(self):
        mail_values = []
        for applicant in self.applicant_ids:
            mail_values.append(self._prepare_mail_values(applicant))

        if mail_values:
            mails = self.env["mail.mail"].sudo().create(mail_values)
            mails.send(auto_commit=False, raise_exception=False)
            failed_mails = mails.filtered(lambda mail: mail.state == "exception")
            if failed_mails:
                reasons = [
                    reason for reason in failed_mails.mapped("failure_reason") if reason
                ]
                _logger.warning(
                    "Refusal email send failed for %s/%s mail(s), applicant_ids=%s, mail_ids=%s, reasons=%s",
                    len(failed_mails),
                    len(mails),
                    self.applicant_ids.ids,
                    failed_mails.ids,
                    " | ".join(reasons) if reasons else "n/a",
                )
            else:
                _logger.info(
                    "Refusal emails sent immediately for applicant_ids=%s, mail_ids=%s",
                    self.applicant_ids.ids,
                    mails.ids,
                )

    def _prepare_mail_values(self, applicant):
        mail_values = super()._prepare_mail_values(applicant)
        mail_values["scheduled_date"] = False

        server_id = self.env.context.get("refusal_mail_server_id")
        if server_id:
            mail_values["mail_server_id"] = server_id

        sender_email = self.env.context.get("refusal_sender_email")
        if sender_email:
            mail_values["email_from"] = sender_email
        elif not mail_values.get("email_from"):
            fallback_sender = self._get_refusal_sender_email()
            if fallback_sender:
                mail_values["email_from"] = fallback_sender
        return mail_values
