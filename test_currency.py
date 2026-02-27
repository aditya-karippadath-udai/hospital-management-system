from app import create_app
from flask import render_template_string

app = create_app('testing')

def test_filter(value):
    with app.app_context():
        try:
            result = render_template_string("{{ val | currency_inr }}", val=value)
            print(f"Input: {value} -> Output: {result}")
        except Exception as e:
            print(f"Input: {value} -> Error: {str(e)}")

print("Testing currency_inr filter:")
test_filter(100)           # ₹100.00
test_filter(1000)          # ₹1,000.00
test_filter(10000)         # ₹10,000.00
test_filter(100000)        # ₹1,00,000.00
test_filter(1000000)       # ₹10,00,000.00
test_filter(10000000)      # ₹1,00,00,000.00
test_filter(123456.78)     # ₹1,23,456.78
test_filter(None)          # ₹0.00
test_filter("abc")         # ₹abc
