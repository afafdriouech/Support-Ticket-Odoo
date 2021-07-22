from odoo import api, fields, models, tools
from odoo.http import request
from odoo import SUPERUSER_ID
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil import tz
from odoo.http import request



import logging
_logger = logging.getLogger(__name__)

class SupportTicket(models.Model):

    _name = "support.ticket"
    _description = "Support Ticket"
    _order = "create_date desc"
    _rec_name = "subject"
    _inherit = ['mail.thread']
    _translate = True


    @api.model
    def _read_group_state(self, states, domain, order):
        """ Read group customization in order to display all the states in the
            kanban view, even if they are empty
        """

        staff_replied_state = self.env['ir.model.data'].get_object('ticket-module',
                                                                   'website_ticket_state_staff_replied')
        customer_replied_state = self.env['ir.model.data'].get_object('ticket-module',
                                                                      'website_ticket_state_customer_replied')
        #customer_closed = self.env['ir.model.data'].get_object('ticket-module','website_ticket_state_customer_closed')
        #staff_closed = self.env['ir.model.data'].get_object('ticket-module', 'website_ticket_state_staff_closed')

        exclude_states = [staff_replied_state.id, customer_replied_state.id]
        #, customer_closed.id, staff_closed.id]

        # state_ids = states._search([('id','not in',exclude_states)], order=order, access_rights_uid=SUPERUSER_ID)
        state_ids = states._search([], order=order, access_rights_uid=SUPERUSER_ID)

        return states.browse(state_ids)

    def _default_state(self):
        return self.env['ir.model.data'].get_object('ticket-module', 'website_ticket_state_open')

    def _default_priority_id(self):
        default_priority = self.env['ticket.priority'].search([('sequence','=','1')])
        return default_priority[0]

    def _default_category_id(self):
        default_category = self.env['ticket.category'].search([('sequence','=','1')])
        return default_category[0]

    #channel = fields.Char(string="Channel", default="Manual")
    #afaf:check this
    create_user_id = fields.Many2one('res.users', "Create User")
    priority_id = fields.Many2one('ticket.priority', default=_default_priority_id, string="Priority")
    user_id = fields.Many2one('res.users', string="Assigned User", track_visibility='onchange')
    person_name = fields.Char(string='Person Name')
    partner_id = fields.Many2one('res.partner', string="Partner")
    email = fields.Char(string="Email")
    support_email = fields.Char(string="Support Email")
    category_id = fields.Many2one('ticket.category', default=_default_category_id, string="Category", track_visibility='onchange')
    subject = fields.Char(string="Subject")
    description = fields.Text(string="Description")
    state_id = fields.Many2one('ticket.state', group_expand='_read_group_state', default=_default_state,string="State")
    conversation_history_ids = fields.One2many('support.ticket.message', 'ticket_id',
                                               string="Conversation History")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'support.ticket')],
                                     string="Media Attachments")
    portal_access_key = fields.Char(string="Portal Access Key")
    ticket_number = fields.Char(string="Ticket Number", readonly=True)
    ticket_color = fields.Char(related="priority_id.color", string="Ticket Color")
    support_rating = fields.Integer(string="Support Rating")
    support_comment = fields.Text(string="Support Comment")
    close_comment = fields.Html(string="Close Comment")
    close_time = fields.Datetime(string="Close Time")
    close_date = fields.Date(string="Close Date")
    closed_by_id = fields.Many2one('res.users', string="Closed By")
    time_to_close = fields.Integer(string="Time to close (seconds)")

    @api.model
    def create(self, vals):
        # Get next ticket number from the sequence
        vals['ticket_number'] = self.env['ir.sequence'].next_by_code('support.ticket')
        new_id = super(SupportTicket, self).create(vals)
        return new_id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.person_name = self.partner_id.name
        self.email = self.partner_id.email

    ################
    @api.onchange('category_id')
    def _onchange_user_id(self):
        users = self.category_id.cat_user_ids.ids
        return {'domain': {'user_id':[('id','in',users)]}}

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Create new support ticket when receiving new email"""

        defaults = {'support_email': msg.get('to'), 'subject': msg.get('subject')}

        #Extract the name from the from email if you can
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex( "<" ) + 1
            end = msg.get('from').rindex( ">", start )
            from_email = msg.get('from')[start:end]
            from_name = msg.get('from').split("<")[0].strip()
            defaults['person_name'] = from_name
        else:
            from_email = msg.get('from')

        defaults['email'] = from_email
        #defaults['channel'] = "Email"

        #Try to find the partner using the from email
        search_partner = self.env['res.partner'].sudo().search([('email','=', from_email)])
        if len(search_partner) > 0:
            defaults['partner_id'] = search_partner[0].id
            defaults['person_name'] = search_partner[0].name

        defaults['description'] = tools.html_sanitize(msg.get('body'))

        #Assign to default category
        #setting_email_default_category_id = self.env['ir.default'].get('website.support.settings', 'email_default_category_id')

        #if setting_email_default_category_id:
        defaults['category_id'] = self._default_category_id(self)
        return super(SupportTicket, self).message_new(msg, custom_values=defaults)

    #def message_update(self, msg_dict, update_vals=None):
        """ Override to update the support ticket according to the email. """

    #    body_short = tools.html_sanitize(msg_dict['body'])

        # If the to email address is to the customer then it must be a staff member
    #    if msg_dict.get('to') == self.email:
    #        change_state = self.env['ir.model.data'].get_object('ticket-module','website_ticket_state_staff_replied')
    #    else:
    #        change_state = self.env['ir.model.data'].get_object('ticket-module','website_ticket_state_customer_replied')

    #    self.state_id = change_state.id

        # Add to message history to keep HTML clean
    #    self.conversation_history_ids.create({'ticket_id': self.id, 'by': 'customer', 'content': body_short })

    #    return super(SupportTicket, self).message_update(msg_dict, update_vals=update_vals)

class TicketCategory(models.Model):

    _name = "ticket.category"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string='Category Name')
    cat_user_ids = fields.Many2many('res.users', string="Category Users")
    access_group_ids = fields.Many2many('res.groups', string="Access Groups", help="Restrict which users can select the category on the website form, none = everyone")

    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('ticket.category')
        values['sequence'] = sequence
        return super(TicketCategory, self).create(values)

class TicketPriority(models.Model):

    _name = "ticket.priority"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string="Priority Name")
    color = fields.Char(string="Color")

    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('ticket.priority')
        values['sequence']=sequence
        return super(TicketPriority, self).create(values)

class TicketState(models.Model):

    _name = "ticket.state"

    name = fields.Char(required=True, translate=True, string='State Name')
    mail_template_id = fields.Many2one('mail.template', string="Mail Template", domain = "[('model_id','=','support.ticket')]", help="The mail message that the customer gets when the state changes")
    unattended = fields.Boolean(string="Unattended", help="If ticked, tickets in this state will appear by default")

class SupportTicketUsers(models.Model):

    _inherit = "res.users"
    cat_user_ids = fields.Many2many('ticket.category', string="Category Users")


class WebsiteSupportTicketMessage(models.Model):
    _name = "support.ticket.message"

    ticket_id = fields.Many2one('support.ticket', string='Ticket ID')
    by = fields.Selection([('staff', 'Staff'), ('customer', 'Customer')], string="By")
    content = fields.Html(string="Content")

    @api.model
    def create(self, values):

        new_record = super(WebsiteSupportTicketMessage, self).create(values)

        # Notify everyone following the ticket of the custoemr reply
        if values['by'] == "customer":
            customer_reply_email_template = self.env['ir.model.data'].get_object('ticket-module',
                                                                                 'customer_reply_wrapper')
            email_values = customer_reply_email_template.generate_email(new_record.id)
            for follower in new_record.ticket_id.message_follower_ids:
                email_values['email_to'] = follower.partner_id.email
                send_mail = self.env['mail.mail'].sudo().create(email_values)
                send_mail.send()

        return new_record

class WebsiteSupportTicketClose(models.TransientModel):

    _name = "support.ticket.close"

    ticket_id = fields.Many2one('support.ticket', string="Ticket ID")
    message = fields.Html(string="Close Message", required=True)
    template_id = fields.Many2one('mail.template', string="Mail Template", domain="[('model_id','=','support.ticket'), ('built_in','=',False)]")
