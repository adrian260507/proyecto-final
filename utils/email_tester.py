# utils/email_tester.py
from flask import current_app
from .mailer import send_mail

def test_email_system():
    """Prueba el sistema de correos"""
    try:
        subject = "🚀 Prueba de Correo - Sistema Connexa"
        recipients = [current_app.config.get("MAIL_USERNAME")]  # Enviar a nosotros mismos
        body = "Este es un correo de prueba del sistema Connexa."
        html_body = """
        <html>
        <body>
            <h1>🚀 Prueba de Correo - Sistema Connexa</h1>
            <p>Este es un correo de prueba para verificar que el sistema de correos funciona correctamente.</p>
            <p><strong>Configuración:</strong></p>
            <ul>
                <li>Servidor: {server}</li>
                <li>Puerto: {port}</li>
                <li>Usuario: {username}</li>
            </ul>
        </body>
        </html>
        """.format(
            server=current_app.config.get("MAIL_SERVER"),
            port=current_app.config.get("MAIL_PORT"),
            username=current_app.config.get("MAIL_USERNAME")
        )
        
        success = send_mail(subject, recipients, body, html_body)
        
        if success:
            current_app.logger.info("✅ Prueba de correo EXITOSA")
            return True
        else:
            current_app.logger.error("❌ Prueba de correo FALLIDA")
            return False
            
    except Exception as e:
        current_app.logger.error(f"💥 Error en prueba de correo: {e}")
        return False
