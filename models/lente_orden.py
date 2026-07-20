from odoo import api, fields, models
from odoo.exceptions import UserError

class OpticaLenteOrden(models.Model):
    _name = 'optica.lente.orden'
    _description = 'Orden de Lentes'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'name'

    name = fields.Char(default='Nuevo', copy=False, readonly=True, tracking=True)
    state = fields.Selection([
        ('en_espera', 'En espera'),
        ('en_proceso', 'En proceso'),
        ('por_entregar', 'Por entregar'),
        ('entregado', 'Entregado'),
        ('retrabajo', 'Retrabajo'),
        ('cancelado', 'Cancelado'),
    ], default='en_espera', tracking=True, required=True)

    paciente_id = fields.Many2one('res.partner', string='Paciente', required=True, domain=[('is_company','=',False)], tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Orden de venta', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', related='sale_order_id.partner_id', store=True)
    lab_partner_id = fields.Many2one('res.partner', string='Laboratorio', domain=[('supplier_rank','>',0)], tracking=True)
    purchase_id = fields.Many2one('purchase.order', string='OC laboratorio', tracking=True)

    frame_id = fields.Many2one('product.product', string='Armazón')
    lens_product_ids = fields.Many2many('product.product', string='Lentes/Tratamientos')

    # Relación con graduación
    graduacion_id = fields.Many2one('optica.graduacion', string='Graduación de referencia', 
                                   domain="[('paciente_id', '=', paciente_id)]")

    # Snapshot Rx
    od_esf = fields.Float('OD Esf'); od_cil = fields.Float('OD Cil'); od_eje = fields.Integer('OD Eje')
    oi_esf = fields.Float('OI Esf'); oi_cil = fields.Float('OI Cil'); oi_eje = fields.Integer('OI Eje')
    add = fields.Float('Adición')
    dip = fields.Float('DIP'); dnp_od = fields.Float('DNP OD'); dnp_oi = fields.Float('DNP OI')
    alt_co = fields.Float('Alt. CO')
      
    # Medidas del armazón
    diametro_horizontal = fields.Float('Diám. horizontal', digits=(8, 2), tracking=True)
    diametro_vertical = fields.Float('Diám. vertical', digits=(8, 2), tracking=True)
    efectivo = fields.Float('Efectivo', digits=(8, 2), tracking=True)
    puente = fields.Float('Puente', digits=(8, 2), tracking=True)
    diametro_sugerido = fields.Float('Diám. sugerido', digits=(8, 2), tracking=True)
    observaciones = fields.Text()

    fecha_prometida = fields.Date(required=True, tracking=True)
    fecha_entrega_real = fields.Date(tracking=True)

    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id.id)
    monto_total = fields.Monetary(compute='_compute_importes', store=False)
    saldo_pendiente = fields.Monetary(compute='_compute_importes', store=False)

    @api.depends('sale_order_id')
    def _compute_importes(self):
        for r in self:
            so = r.sale_order_id
            if so and so.invoice_ids:
                residual = sum(inv.amount_residual for inv in so.invoice_ids if inv.state not in ('draft','cancel'))
                total = sum(inv.amount_total for inv in so.invoice_ids if inv.state not in ('draft','cancel')) or so.amount_total
                r.monto_total = total
                r.saldo_pendiente = residual
            elif so:
                r.monto_total = so.amount_total
                r.saldo_pendiente = so.amount_total
            else:
                r.monto_total = 0.0
                r.saldo_pendiente = 0.0

    @api.onchange('paciente_id')
    def _onchange_paciente_id(self):
        """Carga automáticamente la graduación cuando se selecciona un paciente"""
        if not self.paciente_id:
            return
        
        graduacion = self.env['optica.graduacion'].search([
            ('paciente_id', '=', self.paciente_id.id)
        ], order='fecha desc', limit=1)
        
        if graduacion:
            self.graduacion_id = graduacion.id
            self.od_esf = self._safe_float(graduacion.ojo_derecho_esfera)
            self.od_cil = self._safe_float(graduacion.ojo_derecho_cilindro)
            self.od_eje = self._safe_int(graduacion.ojo_derecho_eje)
            self.oi_esf = self._safe_float(graduacion.ojo_izquierdo_esfera)
            self.oi_cil = self._safe_float(graduacion.ojo_izquierdo_cilindro)
            self.oi_eje = self._safe_int(graduacion.ojo_izquierdo_eje)
            self.add = self._safe_float(graduacion.adicion)
            self.dip = self._safe_float(graduacion.distancia_interpupilar)
            self.dnp_od = self._safe_float(graduacion.distancia_nasopupilar_od)
            self.dnp_oi = self._safe_float(graduacion.distancia_nasopupilar_oi)
            self.alt_co = self._safe_float(graduacion.altura_centro_optico)
            self.observaciones = graduacion.observaciones or ''

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('optica.lente.orden') or 'Nuevo'
        return super().create(vals)

    def action_en_proceso(self):
        for r in self:
            if not r.lab_partner_id:
                raise UserError('Asigna un laboratorio antes de continuar.')
            r.state = 'en_proceso'

    def action_por_entregar(self):
        self.write({'state': 'por_entregar'})

    def action_entregado(self):
        for r in self:
            if r.saldo_pendiente > 0.0:
                raise UserError('No puedes entregar con saldo pendiente.')
        self.write({'state': 'entregado', 'fecha_entrega_real': fields.Date.context_today(self)})

    def action_retrabajo(self):
        self.write({'state': 'retrabajo'})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})

    def action_print_ticket(self):
        return self.env.ref('Orden_de_lentes.action_report_lente_orden').report_action(self)

    def action_cargar_graduacion(self):
        """Botón manual para cargar la graduación más reciente"""
        for record in self:
            if not record.paciente_id:
                raise UserError('Selecciona un paciente primero')

            graduacion = self.env['optica.graduacion'].search([
                ('paciente_id', '=', record.paciente_id.id)
            ], order='fecha desc', limit=1)

            if not graduacion:
                raise UserError(f'No se encontró graduación para {record.paciente_id.name}')

            record.update({
                'graduacion_id': graduacion.id,
                'od_esf': record._safe_float(graduacion.ojo_derecho_esfera),
                'od_cil': record._safe_float(graduacion.ojo_derecho_cilindro),
                'od_eje': record._safe_int(graduacion.ojo_derecho_eje),
                'oi_esf': record._safe_float(graduacion.ojo_izquierdo_esfera),
                'oi_cil': record._safe_float(graduacion.ojo_izquierdo_cilindro),
                'oi_eje': record._safe_int(graduacion.ojo_izquierdo_eje),
                'add': record._safe_float(graduacion.adicion),
                'dip': record._safe_float(graduacion.distancia_interpupilar),
                'dnp_od': record._safe_float(graduacion.distancia_nasopupilar_od),
                'dnp_oi': record._safe_float(graduacion.distancia_nasopupilar_oi),
                'alt_co': record._safe_float(graduacion.altura_centro_optico),
                'observaciones': graduacion.observaciones or '',
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Graduación cargada',
                    'message': f'Se cargó la graduación del {graduacion.fecha} para {record.paciente_id.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def _safe_float(self, value):
        """Conversión segura a float"""
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _safe_int(self, value):
        """Conversión segura a int"""
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def format_optical_value(self, value, decimals=2, show_positive=True):
        """Formatea valores ópticos con signo positivo explícito."""
        if value in (False, None, ""):
            return "-"

        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        if number > 0 and show_positive:
            return f"+{number:.{decimals}f}"

        return f"{number:.{decimals}f}"

    def format_axis_value(self, value):
        """Formatea eje sin signo y sin decimales."""
        if value in (False, None, ""):
            return "-"

        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return str(value)
