from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEtiquetaNiimbot(TransactionCase):
    def test_zero_and_signed_powers(self):
        order = self.env['optica.lente.orden']
        self.assertEqual(order.format_label_power(0.0), '0.00')
        self.assertEqual(order.format_label_power(2.25), '+2.25')
        self.assertEqual(order.format_label_power(-1.5), '-1.50')

    def test_report_content_and_action(self):
        patient = self.env['res.partner'].create({'name': 'Paciente Etiqueta Prueba'})
        order = self.env['optica.lente.orden'].create({
            'paciente_id': patient.id,
            'fecha_prometida': '2026-11-10',
            'od_esf': 2.25, 'od_cil': -1.5, 'od_eje': 90,
            'oi_esf': 0.0, 'oi_eje': 0, 'add': 1.25,
            'tipo_lente': 'Progresivo', 'material_lente': 'Policarbonato',
            'tratamiento_lente': 'Antirreflejante',
        })
        action = order.action_print_label()
        report = self.env.ref('Orden_de_lentes.action_report_lente_etiqueta')
        self.assertEqual(action['report_name'], report.report_name)
        self.assertEqual(action['report_type'], 'qweb-pdf')
        self.assertEqual(report.paperformat_id.page_width, 50)
        self.assertEqual(report.paperformat_id.page_height, 30)
        html, _ = report._render_qweb_html(report.report_name, order.ids)
        text = html.decode()
        for value in (patient.name, order.name, '+2.25', '-1.50', '0.00',
                      'Progresivo', 'Policarbonato', 'Antirreflejante'):
            self.assertIn(value, text)

    def test_unspecified_lens_details(self):
        patient = self.env['res.partner'].create({'name': 'Sin datos de lente'})
        order = self.env['optica.lente.orden'].create({
            'paciente_id': patient.id, 'fecha_prometida': '2026-11-10',
        })
        report = self.env.ref('Orden_de_lentes.action_report_lente_etiqueta')
        html, _ = report._render_qweb_html(report.report_name, order.ids)
        self.assertEqual(html.decode().count('Sin especificar'), 3)
