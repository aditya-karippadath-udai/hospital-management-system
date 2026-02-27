from app import create_app
from flask import render_template_string

app = create_app('testing')

with app.app_context():
    # Test if 'now' is available in context
    try:
        output = render_template_string("{{ now.strftime('%Y-%m-%d') }}")
        print(f"Jinja context 'now' test pass: {output}")
    except Exception as e:
        print(f"Jinja context 'now' test FAIL: {str(e)}")
