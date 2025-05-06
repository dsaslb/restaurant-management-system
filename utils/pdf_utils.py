from xhtml2pdf import pisa
from flask import render_template
from io import BytesIO
import os

def generate_contract_pdf(contract, output_path):
    html = render_template('contract_pdf_template.html', contract=contract)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)
    if pisa_status.err:
        return False
    with open(output_path, 'wb') as f:
        f.write(pdf.getvalue())
    return True
