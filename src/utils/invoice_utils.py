# import os
# from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML

# def generate_invoice_pdf(booking):
#     """
#     Takes a SQLAlchemy Booking object and returns PDF bytes.
#     """
#     # 1. Locate templates folder
#     root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#     template_path = os.path.join(root_dir, "templates")
    
#     # 2. Setup Jinja2
#     env = Environment(loader=FileSystemLoader(template_path))
#     template = env.get_template("invoice_template.html")
    
#     # 3. Render HTML
#     html_out = template.render(booking=booking)
    
#     # 4. Return PDF as bytes
#     return HTML(string=html_out).write_pdf()