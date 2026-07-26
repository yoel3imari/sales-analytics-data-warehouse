"""Unit tests for synthetic product and customer generation."""

import numpy as np
from src.data.customers import generate_customers
from src.data.products import generate_products


def test_generate_products():
    """Verify product generation generates catalog with correct fields."""
    rng = np.random.default_rng(42)
    products = generate_products(rng, num=10)
    assert len(products) == 10
    first = products[0]
    assert "product_id" in first
    assert "product_name" in first
    assert "list_price" in first
    assert first["list_price"] > 0


def test_generate_customers():
    """Verify customer generation creates valid customer records."""
    rng = np.random.default_rng(42)
    custs = generate_customers(rng, num=5)
    assert len(custs) == 5
    cust = custs[0]
    assert cust["customer_id"] == "CUST-00001"
    assert "@" in cust["email"]
    assert cust["income_bracket"] in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
